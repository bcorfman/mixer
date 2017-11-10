from PyQt4 import QtGui
from PyQt4.QtGui import QFileDialog
from math import sqrt
import vtk
from mayavi_qt import MayaviQWidget
from plot3d import Plotter
from access import CellBounds, PointBounds


# Right-click functionality for PK callouts on the matrix grid.
# I use the custom interactor here because Mayavi has no built-in prop picker.
class CustomInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, model, view, plotter):
        self.model = model
        self.view = view
        self.plotter = plotter
        self.right_btn_event_id = self.AddObserver('RightButtonReleaseEvent', self.on_right_button_release)
        self.cb = self.plotter.access_obj = CellBounds(plotter)
        self.extent = None

    def on_right_button_release(self, obj, eventType):
        # A fast hardware property picker that returns world coordinates.
        picker = vtk.vtkPropPicker()
        click_pos = obj.GetInteractor().GetEventPosition()
        renderer = obj.GetCurrentRenderer()
        cmd = obj.GetCommand(self.right_btn_event_id)
        # if not aborted, the mouse will continue its "pan" functionality as if middle button was held down.
        cmd.SetAbortFlag(1)
        picker.Pick(click_pos[0], click_pos[1], 0, renderer)
        pos = picker.GetPickPosition()
        z = pos[2]
        # Pick position for any portion of the grid has a negative Z value if viewed from the top.
        # This means we can differentiate appropriate grid clicks from inappropriate ones (viewed from the bottom)
        # and from other actors in the scene by simply filtering on Z value.
        if z < 0:
            pk, extent = self.get_cell_info(pos)
            # if user clicks the same cell twice, hide the PK callout.
            if extent == self.extent or pk is None:
                self.cb.hide()
                self.extent = None
            else:
                # hide existing selection
                self.plotter.access_obj.hide()
                # highlight the selected cell, and display the PK callout above it.
                self.cb.display(extent, pk)
                self.extent = extent

        vtk.vtkInteractorStyleTrackballCamera.OnRightButtonUp(self)

    # If the picked point falls inside matrix gridlines, this function will return the corresponding
    # (PK, extent coordinates) of the grid cell. Outside of the grid cell, it will return (None, None).
    def get_cell_info(self, selection_point):
        defl = selection_point[1]
        rng = selection_point[0]
        defl_index = None
        gridlines_defl = self.model.gridlines_defl
        gridlines_range = self.model.gridlines_range
        for i in range(len(gridlines_defl) - 1):
            if gridlines_defl[i] >= defl >= gridlines_defl[i+1]:
                defl_index = i
                break
        rng_index = None
        for i in range(len(gridlines_range) - 1):
            if gridlines_range[i] >= rng >= gridlines_range[i+1]:
                rng_index = i
                break
        if defl_index is None or rng_index is None:
            return None, None
        else:
            pk = self.model.pks[rng_index, defl_index]
            extent = (self.model.gridlines_defl[defl_index+1], self.model.gridlines_defl[defl_index],
                      self.model.gridlines_range[rng_index+1], self.model.gridlines_range[rng_index],
                      0.1, 0.1)
            return pk, extent


# noinspection PyProtectedMember
class MayaviController:
    def __init__(self, model, view, working_dir):
        self.model = model
        self.view = view
        self.working_dir = working_dir
        self.plotter = plotter = Plotter(model)
        self.dispatcher = None
        vtk.vtkObject.GlobalWarningDisplayOff()

        # set up window controls and events
        view.rdoBurst.setChecked(True)
        self.set_window_events(view)

        if model.az_averaging and model.dtl_file is not None:
            self.setup_detailed_output_frames(model, view)
        elif model.dtl_file is not None:
            view.frmAzimuth.setVisible(False)
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

        self.interactor = CustomInteractor(model, view, plotter)
        fig = self.plotter.scene.mayavi_scene
        fig.scene.interactor.interactor_style = self.interactor

        def picker_callback(pick):
            """ This gets called when left button is clicked. """
            # only allow a pick if the chosen actor is in the list of burstpoint (not sample point) objects
            if pick.actor in self.plotter.burstpoint_glyphs.actor.actors and view.rdoBurst.isChecked():
                # Find which data point corresponds to the point picked:
                # we have to account for the fact that each data point is
                # represented by a glyph with several points
                point_id = pick.point_id // plotter.burstpoint_array.shape[0]

                # If the no points have been selected, we have '-1'
                if point_id != -1:
                    # Retrieve the coordinates corresponding to that data
                    # point -- point ids start at 1, so add 1 to 0-based indexing.
                    pid = plotter.pid = point_id + 1

                    # hide existing selection
                    self.plotter.access_obj.hide()

                    # Move the outline to the data point.
                    # Add an outline to show the selected point and center it on the first
                    # data point.
                    self.update_point_details(pid)

        picker = fig.on_mouse_pick(picker_callback)
        picker.tolerance = 0.005  # Decrease tolerance, so that we can more easily select a precise point

    def update_point_details(self, pid):
        model = self.model
        view = self.view
        pts = model.get_sample_points() if view.rdoSample.isChecked() else model.get_burst_points()
        azim = view.buttonGroup.checkedId() if model.az_averaging else int(model.attack_az)
        x, y, z = pts[pid][azim][0], pts[pid][azim][1], pts[pid][azim][2]
        extent = x - 0.5, x + 0.5, y - 0.5, y + 0.5, z - 0.5, z + 0.5
        radius = self.dist_to_active_comps(x, y, z)
        pb = self.plotter.access_obj = PointBounds(self.plotter)
        pb.display(pid, extent, radius, model.attack_az, model.aof, model.frag_ids, model.frag_zones)
        self.print_point_details(pid, pb.x_mid, pb.y_mid, pb.z_mid)

    def dist_to_active_comps(self, x, y, z):
        model = self.model
        dist = 0.0
        for i in model.frag_ids:
            cmp_x, cmp_y, cmp_z = model.comps[i].x, model.comps[i].y, model.comps[i].z
            dist = max(sqrt((x - cmp_x) ** 2 + (y - cmp_y) ** 2 + (z - cmp_z) ** 2), dist)
        return dist

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
                if model.comp_pk[pid][az][cid] > 0.0:
                    # surf_names is 0 indexed, but JMAE surface IDs start at 1.
                    surf_name = model.surf_names[model.surface_hit[pid][az] - 1]
                    output += '      Surf hit: {0}\n'.format(surf_name)
            elif cid in model.blast_ids:
                output += '   Blast PK for {0}: {1:.2f}\n'.format(model.comps[cid].name,
                                                                  model.comp_pk[pid][az][cid])
            elif cid in model.frag_ids:
                output += '   Frag PK for {0}: {1:.2f}\n'.format(model.comps[cid].name,
                                                                 model.comp_pk[pid][az][cid])
                zones = model.frag_zones[pid][az][cid]
                if zones:
                    for z in range(len(zones)):
                        output += '      Zone {0}, {1}-{2} degrees\n'.format(zones[z][0], zones[z][1], zones[z][2])
                else:
                    output += 'None\n'

        self.view.txtInfo.setPlainText(output)

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
        self.plotter.access_obj.hide()
        self.view.txtInfo.setPlainText("")

    # noinspection PyUnusedLocal
    def on_rdo_azimuth_clicked(self, button):
        pid = self.plotter.pid
        self.view.txtInfo.setPlainText("")
        self.update_radius_params()
        obj = self.plotter.access_obj
        obj.hide()
        if obj.is_cell_outline():
            self.update_point_details(pid)

    def on_rdo_sample(self):
        pid = self.plotter.pid
        self.view.txtInfo.setPlainText("")
        self._set_lbl_azimuth_text()
        self.update_radius_params()
        obj = self.plotter.access_obj
        obj.hide()
        if not obj.is_cell_outline():
            self.update_point_details(pid)

    def on_rdo_burst(self):
        pid = self.plotter.pid
        self.view.txtInfo.setPlainText("")
        self._set_lbl_azimuth_text()
        self.update_radius_params()
        obj = self.plotter.access_obj
        obj.hide()
        if not obj.is_cell_outline():
            self.update_point_details(pid)

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

