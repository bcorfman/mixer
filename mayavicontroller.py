from PyQt4 import QtGui
from PyQt4.QtGui import QFileDialog
from mayavi_qt import MayaviQWidget
from plot3d import Plotter


class MayaviController:
    def __init__(self, model, view, working_dir):
        self.model = model
        self.view = view
        self.working_dir = working_dir
        self.plotter = plotter = Plotter(model)

        # set up window controls and events
        view.closeEvent = self.closeEvent
        view.rdoSample.setChecked(True)
        view.rdoSample.clicked.connect(self.on_rdo_sample)
        view.rdoBurst.clicked.connect(self.on_rdo_burst)
        view.btnSave.clicked.connect(self.on_btn_save_clicked)
        view.btnHome.clicked.connect(self.on_btn_home_clicked)
        view.btnAxes.clicked.connect(self.on_btn_axes_clicked)
        view.btnClearSel.clicked.connect(self.on_btn_clear_clicked)

        if model.az_averaging and model.dtl_file is not None:
            layout = view.frmAzimuth.layout()
            point_type = 'sample' if view.rdoSample.isChecked() else 'burst'
            label_text = 'View {0} points at attack azimuth:'.format(point_type)
            view.lblAzimuth = QtGui.QLabel(label_text, view.frmAzimuth)
            layout.addWidget(view.lblAzimuth)
            view.buttonGroup = QtGui.QButtonGroup(view.frmAzimuth)
            view.buttonGroup.buttonClicked.connect(self.on_rdo_azimuth_clicked)
            for az in range(0, 360, int(model.attack_az)):
                rdo_button = QtGui.QRadioButton('{0} degrees'.format(az), view.frmAzimuth)
                layout.addWidget(rdo_button)
                view.buttonGroup.addButton(rdo_button, az)
                if az == 0:
                    rdo_button.setChecked(True)
        else:
            view.frmAzimuth.setVisible(False)
            view.frmDetail.setVisible(False)

        # when this code is called, the sample points or burstpoints in the plotter are initialized only.
        # They cannot be drawn until the Mayavi widget is created here and the scene is activated (and then
        # plotter.update_plot is called).
        if model.dtl_file is not None:
            points = model.get_sample_points() if view.rdoSample.isChecked() else model.get_burst_points()
            az = view.buttonGroup.checkedId() if model.az_averaging else int(model.attack_az)
            self.plotter.update_point_detail(az, points)
        self.mayavi_widget = MayaviQWidget(plotter, view.frmMayavi)
        layout = QtGui.QGridLayout(view.frmMayavi)
        layout.addWidget(self.mayavi_widget, 1, 1)

        def picker_callback(pick):
            """ This get called on pick events. """
            if not plotter.burstpoint_glyphs:
                return

            if pick.actor in plotter.burstpoint_glyphs.actor.actors:
                # Find which data point corresponds to the point picked:
                # we have to account for the fact that each data point is
                # represented by a glyph with several points
                point_id = pick.point_id // plotter.burstpoint_array.shape[0]

                # If the no points have been selected, we have '-1'
                if point_id != -1:
                    # Retrieve the coordinates corresponding to that data
                    # point -- point ids start at 1, so add 1 to 0-based indexing.
                    pid = plotter.pid = point_id + 1

                    # Move the outline to the data point.
                    # Add an outline to show the selected point and center it on the first
                    # data point.
                    x, y, z = plotter.set_outline()
                    self.print_point_details(pid, x, y, z)

        if model.dtl_file is not None:
            figure = plotter.scene.mlab.gcf()
            picker = figure.on_mouse_pick(picker_callback)
            picker.tolerance = 0.01  # Decrease tolerance, so that we can more easily select a precise point

    def print_point_details(self, pid, x, y, z):
        model = self.model
        if self.view.rdoSample.isChecked():
            output = 'Sample point {0} ({1:.2f}, {2:.2f}, {3:.2f})\n'.format(pid, x, y, z)
        else:
            output = 'Burst point {0} ({1:.2f}, {2:.2f}, {3:.2f})\n'.format(pid, x, y, z)

        az = self.plotter.selected_az
        comp_ids = sorted(model.dh_ids.union(model.blast_ids).union(model.frag_ids))
        for cid in comp_ids:
            if cid in model.dh_ids:
                output += '   DH PK for {0}: {1:.2f}\n'.format(model.comps[cid].name, model.comp_pk[pid][az][cid])
                surf_name = model.surf_names[model.surface_hit[pid][az]]
                output += '      Surf hit: {0}\n'.format(surf_name)
            elif cid in model.blast_ids:
                output += '   Blast PK for {0}: {1:.2f}\n'.format(model.comps[cid].name,
                                                                  model.comp_pk[pid][az][cid])
            elif cid in model.frag_ids:
                output += '   Frag PK for {0}: {1:.2f}\n'.format(model.comps[cid].name,
                                                                 model.comp_pk[pid][az][cid])
                output += '      Zone '
                zones = model.frag_zones[pid][az][cid]
                if zones:
                    output += '{0}'.format(zones[0][0])
                    for z in range(1, len(zones) - 1):
                        output += ', {0}'.format(zones[z][0])
                else:
                    output += 'None'
                output += '\n'

        self.view.txtInfo.setPlainText(output)

    def on_btn_home_clicked(self):
        self.plotter.reset_view()

    def on_btn_save_clicked(self):
        filename = QFileDialog.getSaveFileName(self.view, 'Save Figure', self.working_dir,
                                               'Images(*.png *.xpm *.jpg)')
        if filename:
            self.plotter.save_view_to_file(filename)

    def on_btn_axes_clicked(self):
        self.plotter.show_axes(self.view.btnAxes.isChecked())

    def on_btn_clear_clicked(self):
        self.plotter.turn_off_outline()
        self.view.txtInfo.setPlainText("")
        
    def on_rdo_azimuth_clicked(self, button):
        self.view.txtInfo.setPlainText("")
        if self.model.sample_loc:  # set if detail file was read
            self.update_radius_params()
            x, y, z = self.plotter.set_outline()
            self.print_point_details(self.plotter.pid, x, y, z)

    def on_rdo_sample(self):
        self.view.txtInfo.setPlainText("")
        self._set_lbl_azimuth_text()
        if self.model.sample_loc:  # set if detail file was read
            self.update_radius_params()
            x, y, z = self.plotter.set_outline()
            self.print_point_details(self.plotter.pid, x, y, z)

    def on_rdo_burst(self):
        self.view.txtInfo.setPlainText("")
        self._set_lbl_azimuth_text()
        if self.model.sample_loc:  # set if detail file was read
            self.update_radius_params()
            x, y, z = self.plotter.set_outline()
            self.print_point_details(self.plotter.pid, x, y, z)

    def _set_lbl_azimuth_text(self):
        if self.view.frmAzimuth.isVisible():
            point_type = 'sample' if self.view.rdoSample.isChecked() else 'burst'
            label_text = 'View {0} points at attack azimuth:'.format(point_type)
            self.view.lblAzimuth.setText(label_text)

    def closeEvent(self, event):
        self.mayavi_widget.deleteLater()

    def update_radius_params(self):
        model = self.model
        view = self.view
        points = model.get_sample_points() if view.rdoSample.isChecked() else model.get_burst_points()
        az = view.buttonGroup.checkedId() if model.az_averaging else int(model.attack_az)
        self.plotter.update_point_detail(az, points)
        if model.sample_loc:  # set if detail file was read
            self.plotter.plot_detail()


