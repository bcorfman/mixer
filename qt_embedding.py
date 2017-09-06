import os
os.environ['ETS_TOOLKIT'] = 'qt4'
os.environ['QT_API'] = 'pyqt'
import numpy as np
from pyface.qt import QtGui, QtCore
from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from mayavi.core.api import Engine
from uiloader import load_ui_widget


class Visualization(HasTraits):
    scene = Instance(MlabSceneModel)

    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                     height=600, width=800, show_label=False),
                resizable=True)

    def __init__(self, points, engine, **traits):
        super(HasTraits, self).__init__(**traits)
        self.engine = engine
        self.engine.start()
        self.points = points
        self.np = len(points)
        self.figure = self.scene.mlab.gcf()

    def _scene_default(self):
        scene = MlabSceneModel(engine=self.engine)
        return scene

    @on_trait_change('scene.activated')
    def update_plot(self):
        picker = self.figure.on_mouse_pick(self.on_pick)
        picker.tolerance = 0.5
        self.scene.mlab.points3d(*self.points, scale_factor=0.03)

    def on_pick(self, event):
        pass
        #ind = event.point_id//self.np
        #print(ind)
        #print(self.points[0][ind], self.points[1][ind], self.points[2][ind])


class Sphere(Visualization):

    def __init__(self, radius, points, engine):
        super(Sphere, self).__init__(points, engine)
        self.radius = radius

    @on_trait_change('scene.activated')
    def update_plot(self):
        pi = np.pi
        phi, theta = np.mgrid[0:pi:101j, 0:2 * pi:101j]

        x = self.radius * np.sin(phi) * np.cos(theta)
        y = self.radius * np.sin(phi) * np.sin(theta)
        z = self.radius * np.cos(phi)

        self.scene.mlab.mesh(x, y, z, color=(0, 1, 0))

        super(Sphere, self).update_plot()


class MayaviQWidget(QtGui.QWidget):
    def __init__(self, visualization, parent=None):
        QtGui.QWidget.__init__(self, parent)
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.visualization = visualization
        self.ui = self.visualization.edit_traits(parent=self,
                                                 kind='subpanel').control
        layout.addWidget(self.ui)
        self.ui.setParent(self)


if __name__ == "__main__":
    app = QtGui.QApplication.instance()
    container = load_ui_widget('mayavi_win.ui')
    #container = QtGui.QWidget()
    container.setWindowTitle("Embedding Mayavi in a PyQt4 Application")
    layout = QtGui.QGridLayout(container.frmMayavi)
    s = Sphere(1, [[0, 1], [0, 0], [1, 0]], Engine())
    mayavi_widget = MayaviQWidget(s, container.frmMayavi)  # the interesting part
    layout.addWidget(mayavi_widget, 1, 1)
    #label = QtGui.QLabel(container)
    #label.setText("hi")
    #layout.addWidget(label, 1, 2)
    container.show()
    app.exec_()
    layout.deleteLater()
    mayavi_widget.deleteLater()
    container.deleteLater()
