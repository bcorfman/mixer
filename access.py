from tvtk.api import tvtk
from callout import Callout
from math import sqrt
import collections


class AccessObj:
    """ Access object for the Plotter class. Takes input and displays an outline."""
    def __init__(self, plotter):
        self.plotter = plotter


class PointBounds(AccessObj):
    """ Access object for the Plotter class. Takes input from the point pick callback and displays it."""
    def __init__(self, plotter):
        super().__init__(plotter)
        self.x_mid = None
        self.y_mid = None
        self.z_mid = None
        self.surf = None
        self.zones = []

    def hide(self):
        """ Hides the object from the 3D display, but doesn't delete it. """
        self.plotter.outline.visible = False
        for z in self.zones:
            z.visible = False
        self.zones = []

    def display(self, pid, extent, mun_az, mun_aof, comp_ids, frag_zones):
        """ Outlines the burstpoint on the 3D display and displays associated frag zones that intersect with the
        frag AV components. """
        # Hides the currently selected object first.
        if self.plotter.access_obj is not None:
            self.plotter.access_obj.hide()
        model = self.plotter.model
        x_min, x_max, y_min, y_max, z_min, z_max = extent
        # Center the outline around the X,Y,Z midpoint
        self.x_mid = (x_max - x_min) / 2.0 + x_min
        self.y_mid = (y_max - y_min) / 2.0 + y_min
        self.z_mid = (z_max - z_min) / 2.0 + z_min
        if self.plotter.outline is None:
            self.plotter.outline = self.plotter.scene.mlab.outline(line_width=3)
        self.plotter.outline.manual_bounds = True
        self.plotter.outline.bounds = (self.x_mid - 0.5, self.x_mid + 0.5,
                                       self.y_mid - 0.5, self.y_mid + 0.5,
                                       self.z_mid - 0.5, self.z_mid + 0.5)
        self.plotter.outline.visible = True

        # set up a Transform to rotate and translate each frag zone steradian to the correct position at the end.
        t = tvtk.Transform()
        # transforms occur in reverse order (The Visualization Toolkit 4th ed, p. 73)
        t.translate(self.x_mid, self.y_mid, self.z_mid)
        t.rotate_z(mun_az)
        t.rotate_y(-90.0 + mun_aof)  # AOF - 90 is necessary to give correct orientation in the Mayavi coord sys
        t.rotate_x(180.0)  # 0 deg is at North Pole by default, so must flip 180 deg to match JMAE orientation

        # create reverse lookup -- all component ids that use each zone angle
        zone_lookup = collections.defaultdict(list)
        for cid in comp_ids:
            zones = frag_zones[pid][mun_az][cid]
            for _, lower_angle, upper_angle in zones:
                zone_lookup[(lower_angle, upper_angle)].append(cid)

        # display each frag zone using largest radius of involved components
        max_radius = 0.0
        for zone in zone_lookup:
            lower_angle, upper_angle = zone
            for cid in zone_lookup[zone]:
                sphere_radius = self.dist_to_active_comp(cid)
                max_radius = max(sphere_radius, max_radius)
                # set the center to (0, 0, 0) so rotation occurs about the origin first, then translate at the end.
                frag_zone = tvtk.SphereSource(center=(0, 0, 0), radius=sphere_radius,
                                              start_phi=lower_angle, end_phi=upper_angle, phi_resolution=50,
                                              theta_resolution=50)
                zone_obj = tvtk.AppendPolyData(input_connection=frag_zone.output_port)
                zone_obj.update()
                zone_tf = tvtk.TransformPolyDataFilter(input_connection=zone_obj.output_port, transform=t)
                zone_tf.update()
                # add the surface to the Mayavi scene
                surf = self.plotter.scene.mlab.pipeline.surface(zone_tf.output, reset_zoom=False)
                # manually adjust zone color according to PK value. When the 3D scene was generated, a color lookup
                # table was saved when the matrix plot was done, and here I use it to match the same color scheme.
                tid = self.plotter.lut_table.get_index(model.comp_pk[pid][mun_az][cid])
                surf.actor.actor.property = tvtk.Property(opacity=0.5,
                                                          color=self.plotter.lut_table.get_table_value(tid)[0:3])
                # store all the zones in a list so we can do operations (like hide) on them later.
                self.zones.append(surf)
                surf.actor.update_data()

    def dist_to_active_comp(self, idx):
        """ Distance between burstpoint and AV component.
        :param idx: AV component index
        :return: distance distance between the burstpoint X,Y,Z coordinates and the AV component X,Y,Z coordinates.
        """
        model = self.plotter.model
        cmp_x, cmp_y, cmp_z = model.comps[idx].x, model.comps[idx].y, model.comps[idx].z
        return sqrt((self.x_mid - cmp_x) ** 2 + (self.y_mid - cmp_y) ** 2 + (self.z_mid - cmp_z) ** 2)

    # noinspection PyMethodMayBeStatic
    def is_cell_outline(self):
        return False

    def is_visible(self):
        return self.plotter.outline.visible


class CellBounds(AccessObj):
    """ Access object for the Plotter class. Takes input from the cell pick callback and displays it."""
    def __init__(self, plotter):
        super().__init__(plotter)
        self.callout = Callout(justification='center', font_size=18, color=(1, 1, 1))
        self.plotter.scene.add_actor(self.callout.actor)
        self.plotter.outline = self.plotter.scene.mlab.outline(line_width=3)
        self.hide()

    def hide(self):
        """ Hides the outline and callout from the 3D display, but doesn't delete it. """
        self.plotter.outline.visible = False
        self.callout.visible = False

    def display(self, extent, pk):
        """ Outlines the selected cell on the 3D display and displays the cell PK value in a callout. """
        if self.plotter.access_obj is not None:
            self.plotter.access_obj.hide()
        x_min, x_max, y_min, y_max, z_min, z_max = extent
        self.plotter.outline.manual_bounds = True
        self.plotter.outline.bounds = (y_min, y_max, x_min, x_max, z_min, z_max)
        self.plotter.outline.visible = True
        x_mid = (x_max - x_min) / 2.0 + x_min
        y_mid = (y_max - y_min) / 2.0 + y_min
        z_mid = (z_max - z_min) / 2.0 + z_min
        self.callout.position = (y_mid, x_mid, z_mid + 5)
        txt = "%4.2f" % pk
        self.callout.text = txt
        self.callout.visible = True

    # noinspection PyMethodMayBeStatic
    def is_cell_outline(self):
        return True

    def is_visible(self):
        return self.plotter.outline.visible
