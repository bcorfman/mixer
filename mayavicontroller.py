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
        parent.btnAxes.clicked.connect(self.on_btn_axes_clicked)

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

        plotter = Plotter(parent, scene)
        self.plotter = plotter
        points = model.get_sample_points() if parent.rdoSample.isChecked() else model.get_burst_points()
        az = self.buttonGroup.checkedId() if model.az_averaging else int(model.attack_az)
        figure = self.plotter.plot_data(model, az, points)

        def picker_callback(pick):
            """ This get called on pick events. """
            if pick.actor in plotter.sample_glyphs.actor.actors:
                # Find which data point corresponds to the point picked:
                # we have to account for the fact that each data point is
                # represented by a glyph with several points
                point_id = pick.point_id // plotter.sample_points.shape[0]

                # If the no points have been selected, we have '-1'
                if point_id != -1:
                    # Retrieve the coordinates corresponding to that data
                    # point
                    x = points[point_id + 1][az][0]
                    y = points[point_id + 1][az][1]
                    z = points[point_id + 1][az][2]

                    # Move the outline to the data point.
                    # Add an outline to show the selected point and center it on the first
                    # data point.
                    plotter.set_outline(x, y, z)

                    if parent.rdoSample.isChecked():
                        parent.txtInfo.setPlainText('Sample point {0}:'.format(point_id + 1))
                    else:
                        parent.txtInfo.setPlainText('Burst point {0}:'.format(point_id + 1))

        picker = figure.on_mouse_pick(picker_callback)
        picker.tolerance = 0.01  # Decrease tolerance, so that we can more easily select a precise point

    def on_btn_home_clicked(self):
        self.plotter.reset_view()

    def on_btn_save_clicked(self):
        filename = QFileDialog.getSaveFileName(self.parent, 'Save Figure', self.working_dir,
                                               'Images(*.png *.xpm *.jpg)')
        if filename:
            self.plotter.save_view_to_file(filename)

    def on_btn_axes_clicked(self):
        self.plotter.show_axes(self.parent.btnAxes.isChecked())

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



