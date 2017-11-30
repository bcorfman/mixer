from PyQt4 import uic


def load_ui_widget(filename):
    """ Loads QTDesigner .ui file from disk and returns a window/dialog. """
    return uic.loadUi(filename)

