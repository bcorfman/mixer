# -*- coding: utf-8 -*-
from numpy import array, full, flipud, fliplr
import util
from tvtk.api import tvtk
from tvtk.common import configure_input
from mayavi import mlab
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


class Plotter:
    def __init__(self, title, parent):
        self.parent = parent
        self.title = title
        self.scale_defl, self.scale_range = 0.0, 0.0
        self.plot = None
        self.target = None
        self.model = None
        self.rotation = 0

    def plot_av(self):
        # TODO: plot AVs based on interpolation like JMAE (not just the nearest ones)
        model = self.model
        iaz = model.az_idx
        iel = model.el_idx
        x, y, z, sz, color = [], [], [], [], []
        for i in range(model.num_tables):  # iterates over real component AVs (no dummy components)
            x.append(model.comp_list[i].x)
            y.append(model.comp_list[i].y)
            z.append(model.comp_list[i].z)
            # get the average masses and velocities for the selected azimuth and elevation
            avg_av, avg_pe = 0.0, 0.0
            for ims, _ in enumerate(model.mss):
                # noinspection PyAssignmentToLoopOrWithParameter
                for ivl, _ in enumerate(model.vls):
                    avg_av += model.avs[i][iaz][iel][ims][ivl]
                    if model.az_averaging:
                        avg_pe += model.pes[i][iaz][iel][ims][ivl]
            avg_av /= (model.num_ms * model.num_vl)
            if model.az_averaging:
                avg_pe /= (model.num_ms * model.num_vl)
            # sphere size represents average vulnerable areas (relative to each other)
            # sphere color represents average probability of exposure using blue-red colormap (blue=0.0, red=1.0)
            sz.append(avg_av)
            color.append(avg_pe)
        if not model.az_averaging:
            color = [1.0 for _ in range(model.num_tables)]  # red for any by-azimuth AVs, since PEs don't apply.
        pts = mlab.quiver3d([x], [y], [z], [sz], [sz], [sz], name='component AV', colormap='blue-red',
                            scalars=color, mode='sphere')
        pts.module_manager.scalar_lut_manager.reverse_lut = True
        pts.glyph.color_mode = 'color_by_scalar'

    def plot_srf_file(self):
        model = self.model
        fig = mlab.gcf()
        polys = array([[4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3] for i in range(len(model.surfaces) / 4)])
        poly_obj = tvtk.PolyData(points=model.surfaces, polys=polys)
        self.target = mlab.pipeline.surface(poly_obj, name='target', figure=fig)
        self.target.actor.property.representation = 'wireframe'
        self.target.actor.property.color = (0, 0, 0)

    def plot_matrix_file(self):
        model = self.model
        figure = mlab.gcf()

        # Define rectilinear grid according to the matrix gridlines.
        # Set the single Z coordinate in the elevation array equal to the munition burst height.
        elevations = full(1, model.burst_height)
        x_dim, y_dim, z_dim = len(model.gridlines_range), len(model.gridlines_defl), len(elevations)
        rgrid = tvtk.RectilinearGrid(x_coordinates=model.gridlines_range, y_coordinates=model.gridlines_defl,
                                     z_coordinates=elevations, dimensions=(x_dim, y_dim, z_dim))
        # Grid colors are displayed using an additional array (PKs).
        # T transposes the 2D PK array to match the gridline cells and then
        # ravel() flattens the 2D array to a 1D array for VTK use as scalars.
        rgrid.cell_data.scalars = model.pks.T.ravel()
        rgrid.cell_data.scalars.name = 'pks'
        rgrid.cell_data.update()  # refreshes the grid now that a new array has been added.

        t = tvtk.Transform()
        t.rotate_z(180.0)  # matrix is reversed in VTK coordinate system
        p = tvtk.Property(color=(0, 0, 0))  # color only matters if we are using wireframe, but I left it in for ref.

        # this method puts the surface in the Mayavi pipeline so the user can change it.
        surf = mlab.pipeline.surface(rgrid, name='matrix')
        surf.actor.actor.user_transform = t
        surf.actor.actor.property = p
        surf.actor.update_data()

        # give PK colorbar a range between 0 and 1. The default is to use the min/max values in the array,
        # which would give us a custom range every time and make it harder for the user to consistently identify what
        # the colors mean.
        surf.module_manager.scalar_lut_manager.use_default_range = False
        surf.module_manager.scalar_lut_manager.data_range = array([0., 1.])
        mlab.colorbar(surf, title='Cell Pk', orientation='vertical')
        mlab.text3d(model.gridlines_range[0], model.gridlines_defl[-1], 140,
                    str('Matrix range: (%5.1f, %5.1f)' % (model.gridlines_range[0], model.gridlines_range[-1])),
                    scale=(20, 20, 20), name='Matrix range coordinates')
        mlab.text3d(model.gridlines_range[0], model.gridlines_defl[-1], 100,
                    str('Matrix defl: (%5.1f, %5.1f)' % (model.gridlines_defl[0], model.gridlines_defl[-1])),
                    scale=(20, 20, 20), name='Matrix deflection coordinates')

    def plot_blast_volume(self):
        model = self.model
        t = tvtk.Transform()
        t.rotate_x(90.0)
        for i in model.blast_comps:
            comp = model.comp_list[i]
            r1, r2, r3, z1, z2 = model.blast_vol[i]
            if r1 == 0 or r2 == 0 or z1 == 0:
                # blast sphere
                p = tvtk.Property(opacity=0.25, color=GYPSY_PINK)
                sphere = tvtk.SphereSource(center=(comp.x, z2 + comp.z, comp.y), radius=r3, phi_resolution=50,
                                           theta_resolution=50)
                surf = mlab.pipeline.surface(sphere.output, name='blast sphere %s' % comp.name)
                surf.actor.actor.property = p
                surf.actor.actor.user_transform = t
            else:
                # double cylinder
                lower_cyl = tvtk.CylinderSource(center=(comp.x, (z1 + comp.z) / 2.0 + 0.01, comp.y), radius=r1,
                                                height=z1, resolution=50, capping=True)
                p = tvtk.Property(opacity=0.25, color=GYPSY_PINK)
                combined_source = tvtk.AppendPolyData(input=lower_cyl.output)

                upper_cyl = tvtk.CylinderSource(center=(comp.x, ((z2 - z1) / 2.0) + z1 + comp.z, comp.y), radius=r2,
                                                height=z2 - z1, resolution=50, capping=False)
                combined_source.add_input(upper_cyl.output)

                cap = tvtk.SphereSource(center=(comp.x, z2 + comp.z, comp.y), radius=r3, start_theta=0, end_theta=180,
                                        phi_resolution=50, theta_resolution=50)
                combined_source.add_input(cap.output)

                surf = mlab.pipeline.surface(combined_source.output, name='blast volume %s' % comp.name)
                surf.actor.actor.property = p
                surf.actor.actor.user_transform = t
                mlab.outline(surf)
                mlab.axes(surf)

    def plot_munition(self):
        """ Plot an arrow showing direction of incoming munition and display text showing angle of fall,
        attack azimuth and terminal velocity. """
        model = self.model
        fig = mlab.gcf()
        scale = max(model.gridlines_range[-1] - model.gridlines_range[0],
                    model.gridlines_defl[-1] - model.gridlines_defl[0]) / 1000
        # position arrow position outside of target, using both maximum radius and matrix offset.
        arrow_distance = model.volume_radius + 20 - (model.aof / 90.0 * 20)  # fudge to put arrow just outside radius
        if not model.az_averaging:
            # rotate unit vector into position of munition attack_az and aof
            xv, yv, zv = util.rotate_pt_around_yz_axes(1.0, 0.0, 0.0, model.aof, model.attack_az)

            # rotate arrow into correct position
            xloc, yloc, zloc = util.rotate_pt_around_yz_axes(-arrow_distance, 0.0, 0.0, model.aof, model.attack_az)
            mlab.quiver3d([xloc], [yloc], [zloc + 1.0], [xv], [yv], [zv], color=(1, 1, 1), reset_zoom=False,
                          line_width=15, scale_factor=15, name='munition', mode='arrow', figure=fig)
            # label arrow with text describing terminal conditions
            format_str = '{0} deg AOF\n{1}° deg attack azimuth\n{2} ft/s terminal velocity'
            mlab.text3d(xloc, yloc, zloc + 12, format_str.format(model.aof, model.attack_az, model.term_vel),
                        color=(1, 1, 1), scale=(scale, scale, scale), name='munition-text', figure=fig)
        else:
            for az in range(0, 360, int(model.attack_az)):
                # rotate unit vector into position of munition attack_az and aof
                xv, yv, zv = util.rotate_pt_around_yz_axes(1.0, 0.0, 0.0, model.aof, az)

                # rotate arrow into correct position
                xloc, yloc, zloc = util.rotate_pt_around_yz_axes(-arrow_distance, 0.0, 0.0, model.aof, az)
                mlab.quiver3d([xloc], [yloc], [zloc + 1.0], [xv], [yv], [zv], color=(1, 1, 1), reset_zoom=False,
                              line_width=15, scale_factor=15, name='munition %d deg' % az, mode='arrow', figure=fig)
                if az == 0:
                    format_str = '{0} deg AOF\nAveraged attack az - {1} deg increment\n{2} ft/s terminal velocity'
                    mlab.text3d(xloc, yloc, zloc + 12, format_str.format(model.aof, model.attack_az, model.term_vel),
                                color=(1, 1, 1), scale=(scale, scale, scale), name='munition-text', figure=fig)

    def plot_data(self, model):
        self.model = model
        scene = mlab.get_engine().new_scene()  # create a new scene window every time
        scene.title = self.title
        scene.disable_render = True  # generate scene more quickly by temporarily turning off rendering
        if self.model.pks is not None:
            self.plot_matrix_file()  # matrix can be plotted if it was read in
        self.plot_srf_file()
        if self.model.blast_vol:
            self.plot_blast_volume()  # plot blast volume if blast damage was included in output
        self.plot_av()
        self.plot_munition()
        # figure = mlab.gcf()
        # picker = figure.on_mouse_pick(self.pick_callback)
        # picker.tolerance = 0.01 # Decrease the tolerance, so that we can more easily select a precise point
        scene.disable_render = False  # reinstate display
        mlab.view(azimuth=0, elevation=30, distance=150, focalpoint=(0, 0, 50), figure=mlab.gcf())  # focalpoint=(0, 0, 29), figure=mlab.gcf())
