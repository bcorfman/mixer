from PyQt4 import QtGui
from PyQt4.QtGui import QFileDialog
from tvtk.api import tvtk
import vtk
from mayavi_qt import MayaviQWidget
from plot3d import Plotter
from access import CellBounds


class CustomInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, model, plotter):
        self.model = model
        self.plotter = plotter
        self.AddObserver('LeftButtonReleaseEvent', self.on_left_button_release)

    def on_left_button_release(self, obj, eventType):
        # get camera's view transform matrix, which gives any rotations and transforms used to display the
        # camera's (and user's) current viewpoint of the scene.
        camera = self.plotter.get_camera()
        mtx = camera.view_transform_matrix
        # inverting the view transform matrix and multiplying by it will undo any rotations and transforms.
        mtx.invert()

        # grab the world coordinates of the user's picked point
        picker = vtk.vtkPropPicker()
        click_pos = obj.GetInteractor().GetEventPosition()
        renderer = obj.GetCurrentRenderer()
        picker.Pick(click_pos[0], click_pos[1], 0, renderer)
        pos = picker.GetPickPosition()  # TODO: figure out why pos is (0, 0, 0)
        pt = [pos[0], pos[1], pos[2], 1]  # matrix multiply expects a 4-element vector

        # now multiply the picked position by the inverse view transform matrix to undo any transforms
        orig_pt = mtx.multiply_point(pt)

        #cell_id = picker.GetCellId()
        #bounds = picker.GetActor().GetBounds()

        num_cells_rng, num_cells_defl = len(self.model.cell_size_range), len(self.model.cell_size_defl)
        #cell_defl, cell_rng = cells.cell_id // num_cells_defl, picker.cell_id % num_cells_rng
        #rng_min, rng_max = self.model.gridlines_range[cell_rng + 1], self.model.gridlines_range[cell_rng]
        #defl_min, defl_max = self.model.gridlines_defl[cell_defl + 1], self.model.gridlines_defl[cell_defl]
        #extent = (defl_min, defl_max, rng_min, rng_max, 0.1, 0.1)
        # Find PK for selected cell
        #pk = picker.mapper.input.cell_data.scalars[picker.cell_id]

        # Pick position for any portion of the grid has a negative Z value if viewed from the top.
        # This means we can differentiate appropriate grid clicks from inappropriate ones (viewed from the bottom)
        # and from other actors in the scene by simply filtering on Z value.
        vtk.vtkInteractorStyleTrackballCamera.OnLeftButtonUp(self)


# noinspection PyProtectedMember
class MayaviController:
    def __init__(self, model, view, working_dir):
        self.model = model
        self.view = view
        self.working_dir = working_dir
        self.plotter = plotter = Plotter(model)
        self.dispatcher = None
        self.cb = CellBounds(plotter)

        # set up window controls and events
        view.rdoSample.setChecked(True)
        self.set_window_events(view)

        if model.az_averaging and model.dtl_file is not None:
            self.setup_detailed_output_frames(model, view)
        else:
            view.frmAzimuth.setVisible(False)
            view.frmDetail.setVisible(False)

        # when this code is called, the sample points or burstpoints in the plotter are initialized only.
        # They cannot be drawn until the Mayavi widget is created, and the scene is activated (which fires
        # plotter.update_plot).
        if model.dtl_file is not None:
            points = model.get_sample_points() if view.rdoSample.isChecked() else model.get_burst_points()
            az = view.buttonGroup.checkedId() if model.az_averaging else int(model.attack_az)
            self.plotter.update_point_detail(az, points)
        self.mayavi_widget = MayaviQWidget(plotter, view.frmMayavi)
        layout = QtGui.QGridLayout(view.frmMayavi)
        layout.addWidget(self.mayavi_widget, 1, 1)

        fig = self.plotter.scene.mlab.gcf()
        fig.scene.interactor.interactor_style = CustomInteractor(model, plotter)

    def set_window_events(self, view):
        view.closeEvent = self.closeEvent
        view.rdoSample.clicked.connect(self.on_rdo_sample)
        view.rdoBurst.clicked.connect(self.on_rdo_burst)
        view.btnSave.clicked.connect(self.on_btn_save_clicked)
        view.btnHome.clicked.connect(self.on_btn_home_clicked)
        view.btnAxes.clicked.connect(self.on_btn_axes_clicked)
        view.btnClearSel.clicked.connect(self.on_btn_clear_clicked)

    def setup_detailed_output_frames(self, model, view):
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

    # TODO: revisit access for this -- why am I grabbing the az from plotter for instance
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

    # noinspection PyUnusedLocal
    def on_rdo_azimuth_clicked(self, button):
        self.view.txtInfo.setPlainText("")
        self.update_radius_params()
        outline = self.plotter.outline
        self.print_point_details(self.plotter.pid, outline.x_mid, outline.y_mid, outline.z_mid)

    def on_rdo_sample(self):
        self.view.txtInfo.setPlainText("")
        self._set_lbl_azimuth_text()
        self.update_radius_params()
        outline = self.plotter.outline
        self.print_point_details(self.plotter.pid, outline.x_mid, outline.y_mid, outline.z_mid)

    def on_rdo_burst(self):
        self.view.txtInfo.setPlainText("")
        self._set_lbl_azimuth_text()
        self.update_radius_params()
        outline = self.plotter.outline
        self.print_point_details(self.plotter.pid, outline.x_mid, outline.y_mid, outline.z_mid)

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
        self.plotter.plot_detail()

