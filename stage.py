import sys
import os
from PySide import QtGui, QtCore
from paramcontroller import ParamController
from uiloader import loadUiWidget
from inifile import IniParser

if __name__ == '__main__':
    print('Running in ' + os.getcwd() + '.\n')
    try:
        app = QtGui.QApplication(sys.argv)
    except RuntimeError:
        app = QtCore.QCoreApplication.instance(sys.argv)
    param_dlg = loadUiWidget('paramdlg.ui')
    geo = param_dlg.frameGeometry()
    height, width = geo.height(), geo.width()
    x, y = geo.x(), geo.y()
    desktop = app.desktop()
    desk_rect = desktop.screenGeometry(desktop.screenNumber(QtGui.QCursor.pos()))
    screen_height, screen_width = desk_rect.height(), desk_rect.width()
    param_dlg.setGeometry((screen_width - width) / 2 + desk_rect.left(),
                          (screen_height - height) / 2 + desk_rect.top(), width, height)
    ini_parser = IniParser(param_dlg)
    ini_parser.read_ini_file()
    param_dlg.setGeometry(ini_parser.x, ini_parser.y, ini_parser.width, ini_parser.height)
    out_files = [os.path.splitext(x)[0] for x in os.listdir(ini_parser.dir) if x.endswith('.out')]
    param_dlg_ctlr = ParamController(param_dlg, ini_parser.dir, out_files)

    param_dlg.btnChoose.clicked.connect(param_dlg_ctlr.onBtnChoose)
    param_dlg.lstCase.itemClicked.connect(param_dlg_ctlr.onLstCase_ItemClicked)
    param_dlg.btnDisplay.clicked.connect(param_dlg_ctlr.onBtnDisplay)
    param_dlg.cboAOF.currentIndexChanged.connect(param_dlg_ctlr.onDialogChanged)
    param_dlg.cboTermVel.currentIndexChanged.connect(param_dlg_ctlr.onDialogChanged)
    param_dlg.cboBurstHeight.currentIndexChanged.connect(param_dlg_ctlr.onDialogChanged)
    app.aboutToQuit.connect(param_dlg_ctlr.aboutToQuit)
    param_dlg.show()
    app.exec_()
