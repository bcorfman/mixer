import os
from PySide import QtGui
from textlabel import TextLabel
from inifile import IniParser


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
        self.populateListBox()

    def populateListBox(self):
        cases = set((x.rsplit('-', 2)[0].rsplit('_', 2)[0] for x in self.out_files))
        self.dlg.lstCase.clear()
        if cases:
            self.dlg.lstCase.addItems(sorted(cases))
        self.dlg.cboAOF.clear()
        self.dlg.cboTermVel.clear()
        self.dlg.cboBurstHeight.clear()

    def populateComboBoxes(self):
        aofs = set((x.rsplit('-', 2)[0].rsplit('_', 2)[2] for x in self.out_files))
        vels = set((x.rsplit('-', 2)[1] for x in self.out_files))
        heights = set((x.rsplit('-', 2)[2] for x in self.out_files))
        self.dlg.cboAOF.clear()
        self.dlg.cboTermVel.clear()
        self.dlg.cboBurstHeight.clear()
        if aofs:
            lst = [(int(aof), aof) for aof in aofs]
            lst = [aof for _, aof in sorted(lst)]
            self.dlg.cboAOF.addItems(lst)
        if vels:
            lst = [(int(vel), vel) for vel in vels]
            lst = [vel for _, vel in sorted(lst)]
            self.dlg.cboTermVel.addItems(lst)
        if heights:
            lst = [(int(h), h) for h in heights]
            lst = [h for _, h in sorted(lst)]
            self.dlg.cboBurstHeight.addItems(lst)
        self.dlg.cboBlastVolume.addItems(['M-Kill'])  # TODO: add these from output file parse
        self.dlg.cboPkSurface.addItems(['Matrix'])

    def onBtnChoose(self):
        d = QtGui.QFileDialog.getExistingDirectory(None, 'Open Directory', self.start_dir,
                                                   QtGui.QFileDialog.ShowDirsOnly |
                                                   QtGui.QFileDialog.DontResolveSymlinks)
        if d:
            self.dlg.lblDirectory.setText('Directory: ' + d)
            self.ini_parser.dir = d
            self.ini_parser.write_ini_file()
            self.out_files = [os.path.splitext(x)[0] for x in os.listdir(d) if x.endswith('.out')]
            self.populateListBox()

    def onLstCase_ItemClicked(self, item):
        self.populateComboBoxes()
        self.ini_parser.write_ini_file()

    def onDialogChanged(self, idx):
        self.ini_parser.write_ini_file()

    def onBtnDisplay(self):
        from plot3d import Plotter
        case = self.ini_parser.case
        term_conds = '_' + self.ini_parser.aof + '-' + self.ini_parser.term_vel + '-' + self.ini_parser.burst_height
        file_lst = [f for f in self.out_files if f.startswith(case) and f.endswith(term_conds)]
        if len(file_lst) == 0:
            QtGui.QMessageBox.critical(self.dlg, 'Error', 'The output filename is not found.', QtGui.QMessageBox.Close)
            return
        if len(file_lst) > 1:
            QtGui.QMessageBox.critical(self.dlg, 'Error', 'More than one filename matches the current selection. ' +
                                                          'Cannot resolve the correct filename.',
                                       QtGui.QMessageBox.Close)
            return
        plotter = Plotter(case + term_conds, self.dlg)
        plotter.initialize(self.ini_parser.dir + os.sep + file_lst[0] + '.out')

    def aboutToQuit(self):
        self.ini_parser.write_ini_file()
