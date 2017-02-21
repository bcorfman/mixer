import os
import re
from PySide import QtGui
from textlabel import TextLabel
from inifile import IniParser
from datamodel import DataModel
from collections import OrderedDict


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
        self.dlg.btnDisplay.setEnabled(False)
        self.plotter = None
        self.model = None
        self.blast_comps = OrderedDict()

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
        file_prefix = self.getFileMatch()
        if not file_prefix:
            return

        self.update_model(file_prefix)
        for bid in self.model.blast_vol.keys():
            for ci, comp in enumerate(self.model.comp_list):
                if ci == bid - 1:
                    self.blast_comps[comp.name] = bid
        if self.blast_comps.items():
            self.dlg.cboBlastVolume.addItems(self.blast_comps.keys())
            self.dlg.cboBlastVolume.setEnabled(True)
        else:
            self.dlg.cboBlastVolume.setEnabled(False)
        self.dlg.cboPkSurface.addItems(['Matrix'])

    def onBtnChoose(self):
        # noinspection PyTypeChecker
        d = QtGui.QFileDialog.getExistingDirectory(None, 'Open Directory', self.start_dir,
                                                   QtGui.QFileDialog.ShowDirsOnly |
                                                   QtGui.QFileDialog.DontResolveSymlinks)
        if d:
            self.dlg.lblDirectory.setText('Directory: ' + d)
            self.ini_parser.dir = d
            self.ini_parser.write_ini_file()
            self.out_files = [os.path.splitext(x)[0] for x in os.listdir(d) if x.endswith('.out')]
            self.populateListBox()

    # noinspection PyUnusedLocal
    def onLstCase_ItemClicked(self, item):
        self.populateComboBoxes()
        self.ini_parser.write_ini_file()
        self.dlg.btnDisplay.setEnabled(True)

    # noinspection PyUnusedLocal
    def onDialogChanged(self, idx):
        file_prefix = self.getFileMatch()
        if not file_prefix:
            return
        self.update_model(file_prefix)
        self.ini_parser.write_ini_file()

    def onBtnDisplay(self):
        from plot3d import Plotter
        file_prefix = self.getFileMatch()
        plotter = Plotter(file_prefix, self.dlg)
        plotter.plot_data(self.model, self.blast_comps[self.dlg.cboBlastVolume.currentText()])

    def aboutToQuit(self):
        self.ini_parser.write_ini_file()

    def getFileMatch(self):
        dlg = self.dlg
        prefix = dlg.lstCase.currentItem().text() + '_'
        suffix = '_' + dlg.cboAOF.currentText() + '-' + dlg.cboTermVel.currentText()
        suffix += '-' + dlg.cboBurstHeight.currentText()
        file_lst = [f for f in self.out_files if re.search('^' + prefix + '\d+' + suffix + '$', f)]
        return file_lst[0] if len(file_lst) == 1 else ''

    def update_model(self, file_prefix):
        try:
            self.model = DataModel()
            self.model.read_and_transform_all_files(self.ini_parser.dir + os.sep + file_prefix + '.out')
        except IOError, e:
            QtGui.QMessageBox.warning(QtGui.QWidget(), "File error",
                                      "Cannot find %s in the directory you chose." % e.filename,
                                      QtGui.QMessageBox.StandardButton.Ok)

