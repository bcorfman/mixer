import os
from fnmatch import fnmatch
from PyQt4.QtGui import QFileDialog, QApplication
from PyQt4.QtCore import Qt
from textlabel import TextLabel
from inifile import IniParser
from datamodel import DataModel
from uiloader import load_ui_widget
from mayavicontroller import MayaviController


# noinspection SpellCheckingInspection
class ParamController:
    def __init__(self, app, dlg, start_dir, out_files):
        self.win = None
        self.start_dir = start_dir
        self.out_files = out_files
        self.dlg = dlg
        dlg.lblDirectory = TextLabel(self.dlg, objectName='lblDirectory')
        dlg.lblDirectory.setText('Directory: ' + start_dir)
        dlg.lblDirectory.setGeometry(30, 20, 251, 16)
        choose_btn = self.dlg.lblLayout.itemAt(0).widget()
        dlg.lblLayout.removeWidget(choose_btn)
        dlg.lblLayout.addWidget(dlg.lblDirectory)
        dlg.lblLayout.addWidget(choose_btn)
        dlg.frame.setLayout(dlg.lblLayout)
        dlg.btnDisplay.setEnabled(False)
        self.ini_parser = IniParser(dlg)
        self.ini_parser.dir = start_dir
        self._populate_list_box()
        self.controllers = []
        self.model = None
        self.stop_events = False
        dlg.btnChoose.clicked.connect(self.on_btn_choose)
        dlg.lstCase.itemClicked.connect(self.on_case_item_clicked)
        dlg.btnDisplay.clicked.connect(self.on_btn_display)
        dlg.cboAOF.currentIndexChanged.connect(self.on_dialog_changed)
        dlg.cboTermVel.currentIndexChanged.connect(self.on_dialog_changed)
        dlg.cboBurstHeight.currentIndexChanged.connect(self.on_dialog_changed)
        app.aboutToQuit.connect(self.about_to_quit)

    def _populate_list_box(self):
        """ Parse case names from output file list and use them to fill Case list box."""
        cases = set((x.rsplit('-', 2)[0].rsplit('_', 2)[0] for x in self.out_files))
        self.dlg.lstCase.clear()
        if cases:
            self.dlg.lstCase.addItems(sorted(cases))
        self.dlg.cboAOF.clear()
        self.dlg.cboTermVel.clear()
        self.dlg.cboBurstHeight.clear()

    def _populate_combo_boxes(self, case_prefix):
        """ Parses the terminal conditions from the case name, and use them to fill in combos."""
        dlg = self.dlg
        self.stop_events = True
        aofs = set((x.rsplit('-', 2)[0].rsplit('_', 2)[2] for x in self.out_files if x.startswith(case_prefix)))
        vels = set((x.rsplit('-', 2)[1] for x in self.out_files if x.startswith(case_prefix)))
        heights = set((x.rsplit('-', 2)[2] for x in self.out_files if x.startswith(case_prefix)))
        dlg.cboAOF.clear()
        dlg.cboTermVel.clear()
        dlg.cboBurstHeight.clear()
        if aofs:
            lst = [(float(aof), aof) for aof in aofs]
            lst = [aof for _, aof in sorted(lst)]
            dlg.cboAOF.addItems(lst)
        if vels:
            lst = [(float(vel), vel) for vel in vels]
            lst = [vel for _, vel in sorted(lst)]
            dlg.cboTermVel.addItems(lst)
        if heights:
            lst = [(float(h), h) for h in heights]
            lst = [h for _, h in sorted(lst)]
            dlg.cboBurstHeight.addItems(lst)
        dlg.cboPkSurface.clear()
        dlg.cboPkSurface.addItems(['Matrix'])
        self.stop_events = False

    # noinspection PyArgumentList
    def on_btn_choose(self):
        """ Event handler for directory chooser. """
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
        """ Updates the underlying DataModel to reflect the selected case. """
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
        """ Fires when any of the terminal conditions combo boxes are changed and updates the underlying DataModel
        and the user .ini file to reflect the changes. """
        if self.stop_events:
            return
        file_prefix = self._get_file_match()
        if not file_prefix:
            return
        self._update_model(file_prefix)
        self.ini_parser.write_ini_file()

    # noinspection PyArgumentList
    def on_btn_display(self):
        """ Shows the chosen 3D scene. """
        # TODO: Showing the hourglass here doesn't work since the parsing isn't in a separate thread and hangs
        # TODO: up the GUI.
        # noinspection PyArgumentList
        QApplication.setOverrideCursor(Qt.WaitCursor)  # show hourglass cursor
        file_prefix = self._get_file_match()
        plotter_win = load_ui_widget('mayavi_win.ui')
        plotter_win.setWindowTitle(file_prefix)
        controller = MayaviController(self.model, plotter_win, self.start_dir)
        self.controllers.append(controller)
        plotter_win.show()
        QApplication.restoreOverrideCursor()  # show standard arrow cursor

    def about_to_quit(self):
        """ Fires when the app is about to end, and writes out the user preferences to an .ini file. """
        self.ini_parser.write_ini_file()

    def _get_file_match(self):
        """ Returns which file in the chosen directory matches the selected case name and terminal conditions."""
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

    # noinspection PyArgumentList
    def _update_model(self, file_prefix):
        """ Parses the files associated with a chosen case. Reports any parsing errors at the bottom of the dialog. """
        dlg = self.dlg
        QApplication.setOverrideCursor(Qt.WaitCursor)  # show hourglass cursor
        try:
            self.model = DataModel()
            self.model.read_and_transform_all_files(self.ini_parser.dir + os.path.sep + file_prefix + '.out')
            dlg.lblErrorReport.setText("")
            dlg.btnDisplay.setEnabled(True)
        except Exception as e:
            dlg.lblErrorReport.setText(str(e))
            dlg.btnDisplay.setEnabled(False)
        QApplication.restoreOverrideCursor()   # show standard arrow cursor

