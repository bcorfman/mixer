import sys
import os
os.environ['ETS_TOOLKIT'] = 'qt4'
os.environ['QT_API'] = 'pyqt'
# although pyqt4_hook looks like an unused import in PyCharm, this is code for correct PyQt runtime dependencies
# to be loaded (before any of the other PyQt4 imports are done). Further comments inside the module itself.
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
    # center the dialog by default
    desk_rect = desktop.screenGeometry(desktop.screenNumber(QtGui.QCursor.pos()))
    screen_height, screen_width = desk_rect.height(), desk_rect.width()
    param_dlg.setGeometry((screen_width - width) / 2 + desk_rect.left(),
                          (screen_height - height) / 2 + desk_rect.top(), width, height)
    # create an .ini file with reasonable defaults, or read from the current one.
    ini_parser = IniParser(param_dlg)
    ini_parser.read_ini_file()
    # move/size the dialog at the saved coordinates from the .ini file
    param_dlg.setGeometry(ini_parser.x, ini_parser.y, ini_parser.width, ini_parser.height)
    # grab the list of the .out files from the directory specified in the .ini file.
    out_files = [os.path.splitext(x)[0] for x in os.listdir(ini_parser.dir) if x.endswith('.out')]
    # Stage follows a Model-View-Controller (MVC) design pattern. The dialog already created above is
    # the View, and the Controller is created below. The Model is created after the user selects a valid JMAE case.
    param_dlg_ctlr = ParamController(app, param_dlg, ini_parser.dir, out_files)

    param_dlg.show()
    app.exec_()
    # deleteLater() causes the event loop to delete the widget after all pending events have been delivered to it
    # and prevents errors on close.
    app.deleteLater()
    sys.exit()


if __name__ == '__main__':
    main()

