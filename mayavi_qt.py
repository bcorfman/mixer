from PyQt4 import QtGui


class MayaviQWidget(QtGui.QWidget):
    def __init__(self, visualization, parent=None):
        """
        :param visualization: Instance of Plotter class (subclass of Visualization class).
        :param parent: the QWidget is intended to be hosted inside a parent widget (like a QFrame).
        """
        QtGui.QWidget.__init__(self, parent)

        # The edit_traits call will generate the widget to embed.
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.visualization = visualization
        # instantiate the Plotter GUI
        self.ui = visualization.edit_traits(parent=self,
                                            kind='subpanel').control
        # add the widget to the underlying GUI layout for correct display.
        layout.addWidget(self.ui)
        self.ui.setParent(self)

