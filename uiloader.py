__author__ = 'brandon.corfman'

import os
from PySide import QtCore, QtUiTools
from PySide import QtXml


def loadUiWidget(uifilename, parent=None):
    loader = QtUiTools.QUiLoader()
    uifile = QtCore.QFile(os.path.join(os.path.dirname(os.path.abspath(__file__)), uifilename))
    uifile.open(QtCore.QFile.ReadOnly)
    ui = loader.load(uifile, parent)
    uifile.close()
    return ui