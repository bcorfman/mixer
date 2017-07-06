from PyQt4 import QtGui
from tvtk.pyface.api import DecoratedScene


class MayaviQWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        # If you want to debug, beware that you need to remove the Qt
        # input hook.
        # QtCore.pyqtRemoveInputHook()
        # import pdb ; pdb.set_trace()
        # QtCore.pyqtRestoreInputHook()

        # The edit_traits call will generate the widget to embed.
        self.ui = DecoratedScene(parent).control
        parent.gridLayout.addWidget(self.ui)
        #geo = parent.gridLayout
        #width, height = geo.width(), geo.height()
        #x, y = geo.x(), geo.y()
        #self.setGeometry(x, y, width, height)
        self.ui.setParent(self)
