import os
from fnmatch import fnmatch
from PyQt4.QtGui import QFileDialog, QApplication
from PyQt4.QtCore import Qt
from textlabel import TextLabel
from inifile import IniParser
from datamodel import DataModel


class ParamController:
    def __init__(self, dlg, start_dir, out_files):
        self.win = None
        self.start_dir = start_dir
        self.out_files = out_files
        self.dlg = dlg
        self.dlg.lblDirectory = TextLabel(self.dlg, objectName='lblDirectory')
        self.dlg.lblDirectory.setText('Directory: ' + start_dir)
        self.dlg.lblDirectory.setGeometry(30, 20, 251, 16)
        choose_btn = self.dlg.lblLayout.itemAt(0).widget()
        self.dlg.lblLayout.removeWidget(choose_btn)
        self.dlg.lblLayout.addWidget(self.dlg.lblDirectory)
        self.dlg.lblLayout.addWidget(choose_btn)
        self.dlg.frame.setLayout(self.dlg.lblLayout)
        self.ini_parser = IniParser(self.dlg)
        self.ini_parser.dir = start_dir
        self._populate_list_box()
        self.dlg.btnDisplay.setEnabled(False)
        self.plotter = None
        self.model = None
        self.stop_events = False

    def _populate_list_box(self):
        cases = set((x.rsplit('-', 2)[0].rsplit('_', 2)[0] for x in self.out_files))
        self.dlg.lstCase.clear()
        if cases:
            self.dlg.lstCase.addItems(sorted(cases))
        self.dlg.cboAOF.clear()
        self.dlg.cboTermVel.clear()
        self.dlg.cboBurstHeight.clear()

    def _populate_combo_boxes(self, case_prefix):
        self.stop_events = True
        aofs = set((x.rsplit('-', 2)[0].rsplit('_', 2)[2] for x in self.out_files if x.startswith(case_prefix)))
        vels = set((x.rsplit('-', 2)[1] for x in self.out_files if x.startswith(case_prefix)))
        heights = set((x.rsplit('-', 2)[2] for x in self.out_files if x.startswith(case_prefix)))
        self.dlg.cboAOF.clear()
        self.dlg.cboTermVel.clear()
        self.dlg.cboBurstHeight.clear()
        if aofs:
            lst = [(float(aof), aof) for aof in aofs]
            lst = [aof for _, aof in sorted(lst)]
            self.dlg.cboAOF.addItems(lst)
        if vels:
            lst = [(float(vel), vel) for vel in vels]
            lst = [vel for _, vel in sorted(lst)]
            self.dlg.cboTermVel.addItems(lst)
        if heights:
            lst = [(float(h), h) for h in heights]
            lst = [h for _, h in sorted(lst)]
            self.dlg.cboBurstHeight.addItems(lst)
        self.dlg.cboPkSurface.clear()
        self.dlg.cboPkSurface.addItems(['Matrix'])
        self.stop_events = False

    def on_btn_choose(self):
        # noinspection PyTypeChecker
        d = QFileDialog.getExistingDirectory(None, 'Open Directory', self.start_dir,
                                             QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if d:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.dlg.lblDirectory.setText('Directory: ' + d)
            self.ini_parser.dir = d
            self.ini_parser.write_ini_file()
            self.out_files = [os.path.splitext(x)[0] for x in os.listdir(d) if x.endswith('.out')]
            self._populate_list_box()
            QApplication.restoreOverrideCursor()

    # noinspection PyUnusedLocal
    def on_case_item_clicked(self, item):
        if self.stop_events:
            return False
        self._populate_combo_boxes(item.text())
        self.ini_parser.write_ini_file()
        file_prefix = self._get_file_match()
        if not file_prefix:
            return False
        self._update_model(file_prefix)

    # noinspection PyUnusedLocal
    def on_dialog_changed(self, idx):
        if self.stop_events:
            return
        file_prefix = self._get_file_match()
        if not file_prefix:
            return
        self._update_model(file_prefix)
        self.ini_parser.write_ini_file()

    def on_btn_display(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        from plot3d import Plotter
        file_prefix = self._get_file_match()
        plotter = Plotter(file_prefix, self.dlg)
        plotter.plot_data(self.model)
        QApplication.restoreOverrideCursor()

    def about_to_quit(self):
        self.ini_parser.write_ini_file()

    def _get_file_match(self):
        dlg = self.dlg
        case = dlg.lstCase.currentItem()
        aof = dlg.cboAOF.currentText()
        term_vel = dlg.cboTermVel.currentText()
        burst_height = dlg.cboBurstHeight.currentText()
        if not case or not aof or not term_vel or not burst_height:
            return ''
        prefix = case.text() + '_'
        suffix = '_' + aof + '-' + term_vel + '-' + burst_height
        file_lst = [f for f in self.out_files if fnmatch(f, prefix + '*' + suffix)]
        return file_lst[0] if len(file_lst) == 1 else ''

    def _update_model(self, file_prefix):
        try:
            self.model = DataModel()
            self.model.read_and_transform_all_files(self.ini_parser.dir + os.sep + file_prefix + '.out')
            self.dlg.lblErrorReport.setText("")
            self.dlg.btnDisplay.setEnabled(True)
        except Exception as e:
            self.dlg.lblErrorReport.setText(str(e))
            self.dlg.btnDisplay.setEnabled(False)
