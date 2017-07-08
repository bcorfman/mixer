from PyQt4 import QtGui
from tvtk.pyface.api import DecoratedScene
from plot3d import Plotter


class MayaviController(QtGui.QWidget):
    def __init__(self, model, parent):
        QtGui.QWidget.__init__(self, parent)

        # If you want to debug, beware that you need to remove the Qt
        # input hook.
        # QtCore.pyqtRemoveInputHook()
        # import pdb ; pdb.set_trace()
        # QtCore.pyqtRestoreInputHook()

        self.parent = parent
        scene = DecoratedScene(parent)
        window = scene.control
        layout = QtGui.QVBoxLayout(parent.frmMayavi)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(window)

        # set up window controls and events
        parent.rdoSample.setChecked(True)
        parent.rdoSample.clicked.connect(self.on_rdo_sample)
        parent.rdoBurst.clicked.connect(self.on_rdo_burst)

        model.attack_az = 45.0
        model.az_averaging = True
        if model.az_averaging:
            layout = parent.frmAzimuth.layout()
            point_type = 'sample' if parent.rdoSample.isChecked() else 'burst'
            label_text = 'View {0} points at attack azimuth:'.format(point_type)
            parent.lblAzimuth = QtGui.QLabel(label_text, parent.frmAzimuth)
            layout.addWidget(parent.lblAzimuth)
            self.buttonGroup = QtGui.QButtonGroup(parent.frmAzimuth)
            self.buttonGroup.buttonClicked.connect(self.on_rdo_azimuth_clicked)
            for az in range(0, 360, int(model.attack_az)):
                rdo_button = QtGui.QRadioButton('{0} degrees'.format(az), parent.frmAzimuth)
                layout.addWidget(rdo_button)
                self.buttonGroup.addButton(rdo_button, az)
        else:
            parent.frmAzimuth.setVisible(False)
        model.attack_az = 0.0
        model.az_averaging = False

        plotter = Plotter(parent, scene)
        figure = plotter.plot_data(model)
        picker = figure.on_mouse_pick(self.on_picker_callback)
        picker.tolerance = 0.01 # Decrease the tolerance, so that we can more easily select a precise point

    def on_rdo_azimuth_clicked(self, button):
        print('on_rdo_azimuth {0}'.format(self.buttonGroup.checkedId()))

    def on_rdo_sample(self):
        self._set_lbl_azimuth_text()

    def on_rdo_burst(self):
        self._set_lbl_azimuth_text()

    def _set_lbl_azimuth_text(self):
        if self.parent.frmAzimuth.isVisible():
            point_type = 'sample' if self.parent.rdoSample.isChecked() else 'burst'
            label_text = 'View {0} points at attack azimuth:'.format(point_type)
            self.parent.lblAzimuth.setText(label_text)

    def on_picker_callback(self):
        pass
