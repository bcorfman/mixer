# -*- coding: utf-8 -*-
import numpy
from tvtk.api import tvtk
from tvtk.common import configure_input
from mayavi import mlab
from PySide import QtGui
import util
from datamodel import DataModel


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
        self.model = DataModel()
        self.scale_defl, self.scale_range = 0.0, 0.0
        self.plot = None

    def plot_av(self):
        # TODO: plot AVs based on actual az and el (not just first indexed) and by only the comps that are in the
        # TODO: selected kill (self.model.kill_comps)
        model = self.model
        iaz = model.az_idx
        iel = model.el_idx
        x, y, z, sz, color = [], [], [], [], []
        for i in range(model.num_tables):
            x.append(model.comp_list[i].x)
            y.append(model.comp_list[i].y)
            z.append(model.comp_list[i].z)
            avg_av, avg_pe = 0.0, 0.0
            for ims, _ in enumerate(model.mss):
                for ivl, __ in enumerate(model.vls):
                    avg_av += model.avs[i][iaz][iel][ims][ivl]
                    avg_pe += model.pes[i][iaz][iel][ims][ivl]
            avg_av /= (model.num_az * model.num_el)
            avg_pe /= (model.num_az * model.num_el)
            sz.append(avg_av)
            color.append(avg_pe)
        if not model.az_averaging:
            pts = mlab.quiver3d([x], [y], [z], [sz], [sz], [sz], name='component AV', colormap='blue-red',
                                scalars=color, mode='sphere')
            pts.module_manager.scalar_lut_manager.reverse_lut = True
            pts.glyph.color_mode = 'color_by_scalar'
            # pts.glyph.glyph_source.glyph_source.center = [0, 0, 0]

    def plot_srf_file(self, rgb_color=(0, 0, 0)):
        model = self.model
        fig = mlab.gcf()
        if model.az_averaging:
            rad = max(abs(model.srf_min_x), abs(model.srf_max_x), abs(model.srf_min_y), abs(model.srf_max_y))
            t = tvtk.Transform()
            t.rotate_x(90.0)
            lower_cyl = tvtk.CylinderSource(center=(0, 0, 0), radius=rad,
                                            height=model.srf_max_z, resolution=50, capping=True)
            cyl_mapper = tvtk.PolyDataMapper(input=lower_cyl.output)
            p = tvtk.Property(opacity=0.65, color=(0.6745, 0.196, 0.3882))
            cyl_actor = tvtk.Actor(mapper=cyl_mapper, property=p, position=[0, model.srf_max_z / 2.0 + 0.1, 0],
                                   rotate_x=90.0)
            # cyl_actor.user_transform = t
            fig.scene.add_actor(cyl_actor)
            # cx, cy, cz = self.rotate_pt_around_yz_axes(cx, cy, cz, 0.0, self.attack_az)
            # cyl_actor.position = [cx, (self.z1[i] + cz) / 2.0 + 0.01, cy]
        else:
            polys = numpy.array([[4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3] for i in range(len(model.surfaces) / 4)])
            target = tvtk.PolyData(points=numpy.array(model.surfaces), polys=polys)
            surf = mlab.pipeline.surface(target, name='target', figure=fig)
            surf.actor.property.representation = 'wireframe'
            surf.actor.property.color = (0, 0, 0)

    def plot_matrix_file(self):
        model = self.model
        figure = mlab.gcf()
        elevations = numpy.zeros(1)
        x_dim, y_dim, z_dim = len(model.gridlines_defl), len(model.gridlines_range), len(elevations)
        rgrid = tvtk.RectilinearGrid(x_coordinates=model.gridlines_defl, y_coordinates=model.gridlines_range,
                                     z_coordinates=elevations, dimensions=(x_dim, y_dim, z_dim))

        # Extract a plane from the grid to see what we've got.
        plane = tvtk.RectilinearGridGeometryFilter(extent=(0, x_dim - 1, 0, y_dim - 1, 0, z_dim - 1))
        configure_input(plane, rgrid)

        rgrid_mapper = tvtk.PolyDataMapper(input_connection=plane.output_port)

        p = tvtk.Property(color=(0, 0, 0))
        wire_actor = tvtk.Actor(mapper=rgrid_mapper, property=p)
        figure.scene.add_actor(wire_actor)

        # grid colors are displayed using an additional array (PKs).
        rgrid.cell_data.scalars = model.pks.ravel()
        rgrid.cell_data.scalars.name = 'pks'
        rgrid.cell_data.update()

        surf = mlab.pipeline.surface(rgrid)
        surf.module_manager.scalar_lut_manager.use_default_range = False
        surf.module_manager.scalar_lut_manager.data_range = numpy.array([0., 1.])
        mlab.colorbar(surf, title='Cell Pk', orientation='vertical')

        # if not model.az_averaging:
        #     xv, yv, zv = util.rotate_pt_around_yz_axes(1.0, 0.0, 0.0, model.aof, model.attack_az)
        #     xloc, yloc, zloc = util.rotate_pt_around_yz_axes(-model.srf_max_x, 0.0, 0.0, model.aof, model.attack_az)
        #     mlab.quiver3d([xloc - model.offset_range], [yloc - model.offset_defl], [zloc + 5.0], [xv], [yv], [zv],
        #                   color=(1, 1, 1), reset_zoom=False, line_width=15, scale_factor=15, name='projectile',
        #                   mode='arrow', figure=fig)
        #     mlab.text3d(-model.srf_max_x - model.offset_range, - model.offset_defl, 5.0,
        #                 '{0}° AOF\n{1}° attack azimuth\n{2} ft/s terminal velocity'.format(model.aof, model.attack_az,
        #                                                                                    model.term_vel),
        #                 color=(1, 1, 1), name='proj-text', figure=fig)

    def plot_blast_volumes(self):
        model = self.model
        v = mlab.gcf()
        # t = tvtk.Transform()
        # t.rotate_x(90.0)
        for bid, r1, r2, r3, z1, z2 in model.blast_vol:
            for ci, lst in enumerate(model.comp_list):
                _, cx, cy, cz, _ = lst
                if ci == bid:
                    if r1 == 0 or r2 == 0 or z1 == 0:
                        # blast sphere
                        p = tvtk.Property(opacity=0.25, color=(1, 1, 0))
                        sphere = tvtk.SphereSource(center=(0, 0, 0), radius=r3)
                        sphere_mapper = tvtk.PolyDataMapper(input=sphere.output)
                        sphere_actor = tvtk.Actor(mapper=sphere_mapper, property=p)
                        # sphere_actor.user_transform = t
                        v.scene.add_actor(sphere_actor)
                        sphere_actor.position = [cx, z2 + cz, cy]  # TODO: check correct sphere rotation
                    else:
                        # double cylinder
                        lower_cyl = tvtk.CylinderSource(center=(0, 0, 0), radius=r1,
                                                        height=z1, resolution=50, capping=True)
                        cyl_mapper = tvtk.PolyDataMapper(input=lower_cyl.output)
                        p = tvtk.Property(opacity=0.25, color=(1, 1, 0))
                        cyl_actor = tvtk.Actor(mapper=cyl_mapper, property=p)
                        # cyl_actor.user_transform = t
                        v.scene.add_actor(cyl_actor)
                        cx, cy, cz = util.rotate_pt_around_yz_axes(cx, cy, cz, 0.0, model.attack_az)
                        cyl_actor.position = [cx, (z1 + cz) / 2.0 + 0.01, cy]

                        upper_cyl = tvtk.CylinderSource(center=(0, 0, 0), radius=r2, height=z2 - z1, resolution=50,
                                                        capping=False)
                        cyl_mapper = tvtk.PolyDataMapper(input=upper_cyl.output)
                        cyl_actor = tvtk.Actor(mapper=cyl_mapper, property=p)
                        # cyl_actor.user_transform = t
                        v.scene.add_actor(cyl_actor)
                        cyl_actor.position = [cx, ((z2 - z1) / 2.0) + z1 + cz, cy]

                        cap = tvtk.SphereSource(center=(0, 0, 0), radius=r3, start_theta=0, end_theta=180,
                                                phi_resolution=50)
                        cap_mapper = tvtk.PolyDataMapper(input=cap.output)
                        cap_actor = tvtk.Actor(mapper=cap_mapper, property=p)
                        # cap_actor.user_transform = t
                        v.scene.add_actor(cap_actor)
                        cap_actor.position = [cx, z2 + cz, cy]
                        # show only the first blast volume, then exit
                        # TODO: add checkboxes to the GUI to select which blast volume to look at
                        return

    def initialize(self, out_file):
        try:
            self.model.read(out_file)

            self.model.transform_matrix()
            self.model.transform_component_centroids(0.0, self.model.attack_az)
            self.model.transform_surfaces(self.model.attack_az)
            self.model.transform_blast_volumes()
            self.model.extract_az_and_el_indices()
            #self.model.kill_comps = self.model.extract_components('k8')
            self.update_plot()
        except IOError, e:
            QtGui.QMessageBox.warning(QtGui.QWidget(), "File error",
                                      "Cannot find %s in the directory you chose." % e.filename,
                                      QtGui.QMessageBox.StandardButton.Ok)

    def update_plot(self):
        scene = mlab.get_engine().new_scene()
        scene.disable_render = True
        if self.model.pks is not None:
            self.plot_matrix_file()
        self.plot_srf_file()
        # if self.blast_id:
        #     self.plot_blast_volumes()
        # self.plot_av()
        # figure = mlab.gcf()
        # picker = figure.on_mouse_pick(self.pick_callback)
        # picker.tolerance = 0.01 # Decrease the tolerance, so that we can more easily select a precise point
        mlab.view(azimuth=-90, elevation=30, distance=250, focalpoint=(0, 0, 29), figure=mlab.gcf())
