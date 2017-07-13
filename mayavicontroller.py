from PyQt4 import QtGui
from PyQt4.QtGui import QFileDialog
from tvtk.pyface.api import DecoratedScene
from plot3d import Plotter


class MayaviController(QtGui.QWidget):
    def __init__(self, model, parent, working_dir):
        QtGui.QWidget.__init__(self, parent)

        # If you want to debug, beware that you need to remove the Qt
        # input hook.
        # QtCore.pyqtRemoveInputHook()
        # import pdb ; pdb.set_trace()
        # QtCore.pyqtRestoreInputHook()

        self.parent = parent
        self.working_dir = working_dir
        scene = DecoratedScene(parent)
        scene._tool_bar.setVisible(False)
        window = scene.control
        layout = QtGui.QVBoxLayout(parent.frmMayavi)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(window)

        # set up window controls and events
        parent.rdoSample.setChecked(True)
        parent.rdoSample.clicked.connect(self.on_rdo_sample)
        parent.rdoBurst.clicked.connect(self.on_rdo_burst)
        parent.btnSave.clicked.connect(self.on_btn_save_clicked)
        parent.btnHome.clicked.connect(self.on_btn_home_clicked)

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
                if az == 0:
                    rdo_button.setChecked(True)
        else:
            parent.frmAzimuth.setVisible(False)
        model.attack_az = 0.0
        model.az_averaging = False

        plotter = Plotter(parent, scene)
        self.plotter = plotter
        figure = self.plotter.plot_data(model)

        def picker_callback(pick):
            """ Picker callback: this get called when on pick events.
            """
            if pick.actor in plotter.sample_glyphs.actor.actors:
                # Find which data point corresponds to the point picked:
                # we have to account for the fact that each data point is
                # represented by a glyph with several points
                point_id = pick.point_id // plotter.sample_points.shape[0]

                # If the no points have been selected, we have '-1'
                if point_id != -1:
                    # Retrieve the coordinates corresponding to that data
                    # point
                    x = plotter.sample_x[point_id]
                    y = plotter.sample_y[point_id]
                    z = plotter.sample_z[point_id]

                    # Move the outline to the data point.
                    # Add an outline to show the selected point and center it on the first
                    # data point.
                    plotter.set_outline(x, y, z)

                    parent.txtInfo.setText()

        picker = figure.on_mouse_pick(picker_callback)
        picker.tolerance = 0.01  # Decrease tolerance, so that we can more easily select a precise point

    def on_btn_home_clicked(self):
        self.plotter.reset_view()

    def on_btn_save_clicked(self):
        filename = QFileDialog.getSaveFileName(self.parent, 'Save Figure', self.working_dir,
                                               'Images(*.png *.xpm *.jpg)')
        if filename:
            self.plotter.save_view_to_file(filename)

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



