from tvtk.api import tvtk


class AccessObj:
    """ Access object for the Plotter class. Takes input from the point pick callback and displays it."""
    def __init__(self, plotter, extent):
        self.plotter = plotter
        self.extent = extent
        x_min, x_max, y_min, y_max, z_min, z_max = extent
        self.x_mid = (x_max - x_min) / 2.0 + x_min
        self.y_mid = (y_max - y_min) / 2.0 + y_min
        self.z_mid = (z_max - z_min) / 2.0 + z_min

    def display(self, show):
        plotter = self.plotter
        if show:
            if plotter.outline is None:
                plotter.outline = self.plotter.scene.mlab.outline(line_width=3)
            plotter.outline.manual_bounds = True
            plotter.outline.visible = True
        else:
            plotter.outline.visible = False


class PointBounds(AccessObj):
    """ Access object for the Plotter class. Takes input from the point pick callback and displays it."""
    def __init__(self, plotter, extent):
        super().__init__(plotter, extent)

    def display(self, show=True):
        self.plotter.outline.bounds = (self.x_mid - 0.5, self.x_mid + 0.5,
                                       self.y_mid - 0.5, self.y_mid + 0.5,
                                       self.z_mid - 0.5, self.z_mid + 0.5)
        super().display(show)

    # noinspection PyMethodMayBeStatic
    def is_cell_outline(self):
        return False


class CellBounds(AccessObj):
    """ Access object for the Plotter class. Takes input from the cell pick callback and displays it."""
    def __init__(self, plotter, extent, pk):
        super().__init__(plotter, extent)
        self.pk = pk

    def display(self, show=True):
        super().display(show)
        plotter = self.plotter
        x_min, x_max, y_min, y_max, z_min, z_max = self.extent
        plotter.outline.bounds = (y_min, y_max, x_min, x_max, z_min, z_max)
        txt = "%4.2f" % self.pk
        if show and plotter.pk_text is None:
            plotter.pk_text = tvtk.BillboardTextActor3D()
            plotter.pk_text.text_property.justification = 'center'
            plotter.pk_text.text_property.font_size = 18
            plotter.pk_text.text_property.color = (1.0, 1.0, 0.4)
            plotter.pk_text.position = (self.y_mid, self.x_mid, self.z_mid + 5)
            plotter.pk_text.input = txt
            plotter.pk_text.visibility = show
            plotter.scene.add_actor(plotter.pk_text)
        else:
            plotter.pk_text.position = (self.y_mid, self.x_mid, self.z_mid + 5)
            plotter.pk_text.input = txt
            plotter.pk_text.visibility = show

    # noinspection PyMethodMayBeStatic
    def is_cell_outline(self):
        return True
