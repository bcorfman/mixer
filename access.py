from mayavi import mlab
from tvtk.api import tvtk
from callout import Callout
import util
from const import LIGHT_YELLOW3


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

    def display(self, pid, extent, sphere_radius, munition_az, munition_aof):
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
        # TODO: iterate and do an AppendPolyData to display all zones
        t = tvtk.Transform()
        t.rotate_x(90.0)
        p = tvtk.Property(opacity=0.25, color=LIGHT_YELLOW3)
        # blast sphere
        source_obj = mlab.pipeline.builtin_surface()
        source_obj.source = 'sphere'
        source_obj.data_source.center = (self.x_mid, self.z_mid, self.y_mid)
        source_obj.data_source.radius = sphere_radius
        zones = self.model.frag_zones[pid][munition_az][cid]
        if zones:
            output += '{0}'.format(zones[0][0])
            for z in range(1, len(zones) - 1):
                output += ', {0}'.format(zones[z][0])
        else:
            output += 'None'

        source_obj.data_source.start_theta = 0
        source_obj.data_source.end_theta = 180
        source_obj.data_source.phi_resolution = 50
        source_obj.data_source.theta_resolution = 50
        # adding TVTK poly to Mayavi pipeline will do all the rest of the setup necessary to view the volume
        surf = mlab.pipeline.surface(source_obj, name='frag sphere')
        surf.actor.actor.property = p  # add color
        surf.actor.actor.user_transform = t  # rotate the volume into place

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
