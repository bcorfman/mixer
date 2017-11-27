from mayavi import mlab
from tvtk.api import tvtk
from callout import Callout
from const import WHITE
from math import sqrt


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

    def hide(self):
        self.plotter.outline.visible = False

    def display(self, pid, extent, mun_az, mun_aof, comp_ids, frag_zones):
        if self.plotter.access_obj is not None:
            self.plotter.access_obj.hide()
        x_min, x_max, y_min, y_max, z_min, z_max = extent
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

        # add each steradian (sphere slice representing a zone) to a single AppendPolyData object, and then
        # add the PolyData object to the Mayavi pipeline.
        t = tvtk.Transform()
        # transforms occur in reverse order (The Visualization Toolkit 4th ed, p. 73)
        t.translate(self.x_mid, self.y_mid, self.z_mid)
        t.rotate_z(mun_az)
        t.rotate_y(mun_aof)
        t.rotate_x(90.0)
        p = tvtk.Property(opacity=0.5, color=WHITE)
        source_obj = tvtk.AppendPolyData()
        # gather only unique zone angles amongst all the components
        zone_set = set()
        for cid in comp_ids:
            zones = frag_zones[pid][mun_az][cid]
            for z in zones:
                lower_angle, upper_angle = z[1], z[2]
                zone_set.add((lower_angle, upper_angle))
            for lower_angle, upper_angle in zone_set:
                sphere_radius = self.dist_to_active_comps(cid)
                # set the center to (0, 0, 0) so rotation occurs about the origin first, then translate at the end.
                frag_zone = tvtk.SphereSource(center=(0, 0, 0), radius=sphere_radius,
                                              start_theta=lower_angle, end_theta=upper_angle, phi_resolution=50,
                                              theta_resolution=50)
                source_obj.add_input_connection(frag_zone.output_port)
        source_obj.update()

        # adding TVTK poly to Mayavi pipeline will do all the rest of the setup necessary to view the volume
        surf = mlab.pipeline.surface(source_obj.output, name='frag zones', reset_zoom=False)
        surf.actor.actor.property = p  # add color
        surf.actor.actor.user_transform = t  # rotate and move the volume into place over the sample point

    def dist_to_active_comps(self, idx):
        model = self.plotter.model
        cmp_x, cmp_y, cmp_z = model.comps[idx].x, model.comps[idx].y, model.comps[idx].z
        return sqrt((self.x_mid - cmp_x) ** 2 + (self.y_mid - cmp_y) ** 2 + (self.z_mid - cmp_z) ** 2)

    # noinspection PyMethodMayBeStatic
    def is_cell_outline(self):
        return False


class CellBounds(AccessObj):
    """ Access object for the Plotter class. Takes input from the cell pick callback and displays it."""
    def __init__(self, plotter):
        super().__init__(plotter)
        self.callout = Callout(justification='center', font_size=18, color=(1, 1, 1))
        self.plotter.scene.add_actor(self.callout.actor)
        self.plotter.outline = self.plotter.scene.mlab.outline(line_width=3)
        self.hide()

    def hide(self):
        self.plotter.outline.visible = False
        self.callout.visible = False

    def display(self, extent, pk):
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
