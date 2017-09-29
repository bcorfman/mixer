import os
os.environ['ETS_TOOLKIT'] = 'qt4'
os.environ['QT_API'] = 'pyqt'
import math
from numpy import array, full, eye, ones_like
import util
import vtk
from tvtk.api import tvtk
from mayavi import mlab
from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from mayavi.core.api import Engine
from const import GYPSY_PINK



"""
Created on Wed Nov 27 10:37:08 2013
"""
__author__ = 'brandon.corfman'
__doc__ = '''
    Plot a target scene using JMAE input and output files.

    The AVs in AVFILE are plotted as a 3D bubble chart at the az & el defined in the output file.
    Vulnerable areas are sized by magnitude, and probabilities of exposure are graded by color
    (full red = 1.0, full green = 0.0).

    Target surfaces are plotted as wireframe quads.
    Blast volumes are plotted as spheres or double cylinders with sphere caps.
'''


######################################################################


class Visualization(HasTraits):
    scene = Instance(MlabSceneModel)

    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                     resizable=True, show_label=False),
                resizable=True)

    def __init__(self, **traits):
        super(HasTraits, self).__init__(**traits)
        self.engine = Engine()
        self.engine.start()

    def _scene_default(self):
        return MlabSceneModel(engine=self.engine)

    @on_trait_change('scene.activated')
    def update_plot(self):
        pass


class Plotter(Visualization):
    def __init__(self, model):
        super(Plotter, self).__init__()
        self.scale_defl, self.scale_range = 0.0, 0.0
        self.plot = None
        self.target = None
        self.model = model
        self.rotation = 0
        self.sel_x = []
        self.sel_y = []
        self.sel_z = []
        self.burstpoint_array = None
        self.burstpoint_glyphs = None
        self.outline = None
        self.axes = None
        self.selected_az = None
        self.radius_points = None
        self.pid = None

    def plot_av(self):
        # TODO: plot AVs based on interpolation like JMAE (not just the nearest ones)
        model = self.model
        x, y, z, sz, color = [], [], [], [], []
        for i in model.frag_ids:
            x.append(model.comps[i].x)
            y.append(model.comps[i].y)
            z.append(model.comps[i].z)
            sz.append(0.3)
            color.append(1.0)
        pts = self.scene.mlab.quiver3d([x], [y], [z], [sz], [sz], [sz], name='component AV', colormap='blue-red',
                                       scalars=color, mode='sphere', scale_factor=1)
        pts.module_manager.scalar_lut_manager.reverse_lut = True
        pts.glyph.color_mode = 'color_by_scalar'
        pts.glyph.glyph_source.glyph_source.center = (0, 0, 0)

    def plot_srf_file(self):
        model = self.model
        polys = array([[4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3] for i in range(len(model.surfaces) // 4)])
        poly_obj = tvtk.PolyData(points=model.surfaces, polys=polys)
        self.target = mlab.pipeline.surface(poly_obj, name='target')
        self.target.actor.property.representation = 'wireframe'
        self.target.actor.property.color = (0, 0, 0)

    def plot_matrix_file(self):
        model = self.model

        # Define rectilinear grid according to the matrix gridlines.
        # Set the single Z coordinate in the elevation array equal to the munition burst height.
        elevations = full(1, 0.0)
        x_dim, y_dim, z_dim = len(model.gridlines_range), len(model.gridlines_defl), len(elevations)
        rgrid = tvtk.RectilinearGrid(x_coordinates=model.gridlines_range, y_coordinates=model.gridlines_defl,
                                     z_coordinates=elevations, dimensions=(x_dim, y_dim, z_dim))
        # Grid colors are displayed using an additional array (PKs).
        # T transposes the 2D PK array to match the gridline cells and then
        # ravel() flattens the 2D array to a 1D array for VTK use as scalars.
        rgrid.cell_data.scalars = model.pks.T.ravel()
        rgrid.cell_data.scalars.name = 'pks'
        rgrid.cell_data.update()  # refreshes the grid now that a new array has been added.

        p = tvtk.Property(color=(0, 0, 0))  # color only matters if we are using wireframe, but I left it in for ref.

        # this method puts the surface in the Mayavi pipeline so the user can change it.
        surf = self.scene.mlab.pipeline.surface(rgrid, name='matrix')
        surf.actor.actor.property = p
        surf.actor.update_data()

        # give PK colorbar a range between 0 and 1. The default is to use the min/max values in the array,
        # which would give us a custom range every time and make it harder for the user to consistently identify what
        # the colors mean.
        surf.module_manager.scalar_lut_manager.use_default_range = False
        surf.module_manager.scalar_lut_manager.data_range = array([0., 1.])
        self.scene.mlab.colorbar(surf, title='Cell Pk', orientation='vertical')

        # Put max and min gridline coordinates in the upper-right corner of the matrix.
        # Also, scale the text to a readable size.
        sz = max(1, int(abs(model.gridlines_range[-1] - model.gridlines_range[0]) / 100))
        spacing = max(5, sz)
        self.scene.mlab.text3d(model.gridlines_range[-1], model.gridlines_defl[0], 5 * spacing + 2 * sz,
                               str('Matrix range: (%5.1f, %5.1f)' % (model.mtx_extent_range[0], model.mtx_extent_range[1])),
                               scale=(sz, sz, sz), name='Matrix range coordinates')
        self.scene.mlab.text3d(model.gridlines_range[-1], model.gridlines_defl[0], 5 * spacing,
                               str('Matrix defl: (%5.1f, %5.1f)' % (model.mtx_extent_defl[0], model.mtx_extent_defl[1])),
                               scale=(sz, sz, sz), name='Matrix deflection coordinates')

    def plot_blast_volumes(self):
        model = self.model
        t = tvtk.Transform()
        t.rotate_x(90.0)
        p = tvtk.Property(opacity=0.25, color=GYPSY_PINK)
        for bidx in model.blast_ids:
            comp = model.comps[bidx]
            r1, r2, r3, z1, z2 = model.blast_vol[bidx]
            if r1 == 0 or r2 == 0 or z1 == 0:
                # blast sphere
                source_obj = mlab.pipeline.builtin_surface()
                source_obj.source = 'sphere'
                source_obj.data_source.center = (comp.x, z2, comp.y)
                source_obj.data_source.radius = r3
                source_obj.data_source.phi_resolution = 50
                source_obj.data_source.theta_resolution = 50
                # adding TVTK poly to Mayavi pipeline will do all the rest of the setup necessary to view the volume
                surf = mlab.pipeline.surface(source_obj, name='blast sphere %s' % comp.name)
                surf.actor.actor.property = p  # add color
                surf.actor.actor.user_transform = t  # rotate the volume into place
            else:
                # double cylinder merged with sphere cap
                cap = tvtk.SphereSource(center=(comp.x, z2 + 0.01, comp.y), radius=r3, start_theta=0,
                                        end_theta=180, phi_resolution=50, theta_resolution=50)
                upper_cyl = tvtk.CylinderSource(center=(comp.x, (r3 + z2 - z1) / 2.0 + z1 + 0.01, comp.y), radius=r2,
                                                height=r3 + z2 - z1, resolution=50, capping=False)
                tri1 = tvtk.TriangleFilter(input_connection=cap.output_port)
                tri2 = tvtk.TriangleFilter(input_connection=upper_cyl.output_port)
                # calculate intersection of upper cylinder and sphere cap without displaying
                # vtkDelaunay2D warnings about "edge not recovered, polygon fill suspect" on the console.
                vtk.vtkObject.GlobalWarningDisplayOff()
                boolean_op = tvtk.BooleanOperationPolyDataFilter()
                boolean_op.operation = 'intersection'
                boolean_op.add_input_connection(0, tri2.output_port)
                boolean_op.add_input_connection(1, tri1.output_port)
                boolean_op.update()
                vtk.vtkObject.GlobalWarningDisplayOn()
                source_obj = tvtk.AppendPolyData(input_connection=boolean_op.output_port)
                lower_cyl = tvtk.CylinderSource(center=(comp.x, z1 / 2.0 + 0.01, comp.y), radius=r1,
                                                height=z1, resolution=50, capping=True)
                source_obj.add_input_connection(lower_cyl.output_port)
                source_obj.update()
                # adding TVTK poly to Mayavi pipeline will do all the rest of the setup necessary to view the volume
                surf = mlab.pipeline.surface(source_obj.output, name='blast volume %s' % comp.name)
                surf.actor.actor.property = p  # add color
                surf.actor.actor.user_transform = t  # rotate the volume into place

    def plot_munition(self):
        """ Plot an arrow showing direction of incoming munition and display text showing angle of fall,
        attack azimuth and terminal velocity. """
        model = self.model

        # calculate scaling size for matrix range and deflection text.
        # allow for a missing matrix file by checking to see whether gridlines exist first.
        if model.gridlines_range:
            sz = max(1, int(abs(model.gridlines_range[-1] - model.gridlines_range[0]) / 1000),
                     int(abs(model.gridlines_defl[-1] - model.gridlines_defl[0]) / 1000))
        else:
            sz = 1

        # position arrow position outside of target, using both maximum radius and matrix offset.
        line_scale = 15
        zloc = model.burst_height + line_scale * math.sin(math.radians(model.aof))

        if not model.az_averaging:
            xv, yv, zv = util.rotate_pt_around_yz_axes(1.0, 0.0, 0.0, model.aof, model.attack_az)

            # rotate unit vector into position of munition attack_az and aof
            xloc, yloc, _ = util.rotate_pt_around_yz_axes(-1.0, 0.0, 0.0, model.aof, model.attack_az)
            xloc *= model.volume_radius
            yloc *= model.volume_radius

            # rotate arrow into correct position
            mlab.quiver3d([xloc], [yloc], [zloc], [xv], [yv], [zv], color=(1, 1, 1), reset_zoom=False, line_width=15,
                          scale_factor=15, name='munition', mode='arrow')
            # label arrow with text describing terminal conditions
            format_str = '{0} deg AOF\n{1}° deg attack azimuth\n{2} ft/s terminal velocity\n{3} ft. burst height'
            label = format_str.format(model.aof, model.attack_az, model.term_vel, model.burst_height)
            self.scene.mlab.text3d(xloc, yloc, zloc + 8, label, color=(1, 1, 1), scale=(sz, sz, sz), name='munition-text')
        else:
            for az in range(0, 360, int(model.attack_az)):
                xv, yv, zv = util.rotate_pt_around_yz_axes(1.0, 0.0, 0.0, model.aof, az)

                # rotate arrow into correct position
                xloc, yloc, _ = util.rotate_pt_around_yz_axes(-1.0, 0.0, 0.0, model.aof, az)
                xloc *= model.volume_radius
                yloc *= model.volume_radius
                self.scene.mlab.quiver3d([xloc], [yloc], [zloc], [xv], [yv], [zv], color=(1, 1, 1), reset_zoom=False,
                                         line_width=15, scale_factor=15, name='munition %d deg' % az, mode='arrow')
                if az == 0:
                    format_str = '{0} deg AOF\nAvg attack az - {1} deg inc.\n{2} ft/s terminal velocity\n'
                    format_str += '{3} fr. burst height'
                    label = format_str.format(model.aof, model.attack_az, model.term_vel, model.burst_height)
                    self.scene.mlab.text3d(xloc, yloc, zloc + 8, label, color=(1, 1, 1), scale=(sz, sz, sz), name='munition-text')

    def plot_detail(self):
        """
        :param az: azimuth value used as an index for the points dictionary.
        :param points: dictionary that holds either sample point or burst point locations
        :return: None
        """
        self.sel_x, self.sel_y, self.sel_z = [], [], []
        points = self.radius_points
        az = self.selected_az
        for _, key in enumerate(points):
            self.sel_x.append(points[key][az][0])
            self.sel_y.append(points[key][az][1])
            self.sel_z.append(points[key][az][2])
        # setting the scalars here is necessary to avoid VTK error: "Algorithm vtkAssignAttribute returned failure
        # for request: vtkInformation". See https://github.com/enthought/mayavi/issues/3
        if self.burstpoint_glyphs is None:
            self.burstpoint_glyphs = self.scene.mlab.points3d(self.sel_x, self.sel_y, self.sel_z, ones_like(self.sel_x),
                                                              color=(1, 1, 1), scale_factor=0.75)
        else:
            self.burstpoint_glyphs.mlab_source.set(x=self.sel_x, y=self.sel_y, z=self.sel_z,
                                                   scalars=ones_like(self.sel_x))
        # Here, we grab the points describing the individual glyph, to figure
        # out how many points are in an individual glyph.
        self.burstpoint_array = self.burstpoint_glyphs.glyph.glyph_source.glyph_source.output.points.to_array()

    @on_trait_change('scene.activated')
    def update_plot(self):
        model = self.model
        self.scene.scene_editor._tool_bar.setVisible(False)
        self.scene.disable_render = True  # generate scene more quickly by temporarily turning off rendering
        if model.pks is not None:
            self.plot_matrix_file()  # matrix can be plotted if it was read in
        self.plot_srf_file()
        if model.blast_ids:
            self.plot_blast_volumes()
        self.plot_av()
        self.plot_munition()
        if model.sample_loc:
            self.plot_detail()
        self.axes = self.scene.mlab.orientation_axes(figure=self.scene.mlab.gcf())
        self.axes.visible = False
        self.scene.disable_render = False  # reinstate display
        super(Plotter, self).update_plot()
        self.reset_view()

    def update_point_detail(self, az, points):
        self.selected_az = az
        self.radius_points = points

    def turn_off_outline(self):
        self.outline.visible = False

    def set_outline(self):
        if self.outline is None:
            self.outline = self.scene.mlab.outline(line_width=3)
            # self.outline.outline_mode = 'cornered'
            self.outline.manual_bounds = True

        x = self.radius_points[self.pid][self.selected_az][0]
        y = self.radius_points[self.pid][self.selected_az][1]
        z = self.radius_points[self.pid][self.selected_az][2]
        self.outline.bounds = (x - 0.5, x + 0.5,
                               y - 0.5, y + 0.5,
                               z - 0.5, z + 0.5)
        self.outline.visible = True
        return x, y, z

    def reset_view(self):
        self.scene.mlab.view(azimuth=315, elevation=83, distance=self.model.volume_radius * 6, focalpoint=(0, 0, 20))

    def save_view_to_file(self, filename):
        self.scene.mlab.savefig(filename)

    def show_axes(self, state):
        self.axes.visible = state
