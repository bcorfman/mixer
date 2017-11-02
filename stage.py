import sys
import os
os.environ['ETS_TOOLKIT'] = 'qt4'
os.environ['QT_API'] = 'pyqt'
import pyqt4_hook
from PyQt4 import QtGui
from paramcontroller import ParamController
from uiloader import load_ui_widget
from inifile import IniParser


# noinspection PyArgumentList
def main():
    print('Running in ' + os.getcwd() + '.\n')
    app = QtGui.QApplication.instance()
    param_dlg = load_ui_widget('paramdlg.ui')
    geo = param_dlg.frameGeometry()
    height, width = geo.height(), geo.width()
    desktop = app.desktop()
    # noinspection PyArgumentList
    desk_rect = desktop.screenGeometry(desktop.screenNumber(QtGui.QCursor.pos()))
    screen_height, screen_width = desk_rect.height(), desk_rect.width()
    param_dlg.setGeometry((screen_width - width) / 2 + desk_rect.left(),
                          (screen_height - height) / 2 + desk_rect.top(), width, height)
    ini_parser = IniParser(param_dlg)
    ini_parser.read_ini_file()
    param_dlg.setGeometry(ini_parser.x, ini_parser.y, ini_parser.width, ini_parser.height)
    out_files = [os.path.splitext(x)[0] for x in os.listdir(ini_parser.dir) if x.endswith('.out')]
    param_dlg_ctlr = ParamController(app, param_dlg, ini_parser.dir, out_files)

    param_dlg.show()
    app.exec_()
    app.deleteLater()
    sys.exit()


if __name__ == '__main__':
    main()

