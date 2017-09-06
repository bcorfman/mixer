from PyQt4 import QtGui
from tvtk.pyface.api import DecoratedScene


class MayaviQWidget(QtGui.QWidget):
    def __init__(self, visualization, parent=None):
        QtGui.QWidget.__init__(self, parent)

        # The edit_traits call will generate the widget to embed.
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.visualization = visualization
        self.ui = visualization.edit_traits(parent=self,
                                            kind='subpanel').control
        layout.addWidget(self.ui)
        self.ui.setParent(self)

