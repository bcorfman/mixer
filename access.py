class AccessObj:
    """ Access object for the Plotter class. Takes input from the point pick callback and displays it."""
    def __init__(self, plotter, extent):
        self.plotter = plotter
        self.extent = extent
        x_min, x_max, y_min, y_max, z_min, z_max = self.extent
        self.x_mid = (x_max - x_min) / 2.0
        self.y_mid = (y_max - y_min) / 2.0
        self.z_mid = (z_max - z_min) / 2.0

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
        if show and plotter.pk_text is None:
            plotter.pk_text = plotter.scene.mlab.text3d(self.x_mid, self.y_mid, self.z_mid, str(self.pk),
                                                        color=(1, 1, 1), scale=(1, 1, 1), name='pk-text')
        plotter.pk_text.visible = show

    # noinspection PyMethodMayBeStatic
    def is_cell_outline(self):
        return True
