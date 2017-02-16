import os
from ConfigParser import SafeConfigParser

__author__ = 'brandon.corfman'


class IniParser(object):
    def __init__(self, dlg):
        self.dlg = dlg
        self.dir = None
        self.x, self.y, self.width, self.height = None, None, None, None
        self.case = None
        self.aof = None
        self.term_vel = None
        self.burst_height = None
        self.blast_volume = None
        self.pk_surface = None
        self.parser = SafeConfigParser()

    def read_ini_file(self):
        ini_path = os.path.abspath(os.curdir) + os.sep + 'jmaeout.ini'
        if os.path.exists(ini_path):
            self.parser.read(ini_path)
            self.dir = self.parser.get('settings', 'directory')
            geometry = self.parser.get('settings', 'geometry').split(',')
            self.x, self.y = int(geometry[0]), int(geometry[1])
            self.width, self.height = int(geometry[2]), int(geometry[3])
            self.case = self.parser.get('settings', 'case')
            self.aof = self.parser.get('settings', 'aof')
            self.term_vel = self.parser.get('settings', 'term_vel')
            self.burst_height = self.parser.get('settings', 'burst_height')
            self.blast_volume = self.parser.get('settings', 'blast_volume')
            self.pk_surface = self.parser.get('settings', 'pk_surface')
        else:
            self.dir = os.path.abspath(os.curdir)
            self.write_ini_file()

    def write_ini_file(self):
        ini_path = os.path.abspath(os.curdir) + os.sep + 'jmaeout.ini'
        if not self.parser.has_section('settings'):
            self.parser.add_section('settings')
        self.parser.set('settings', 'directory', self.dir)
        rect = self.dlg.geometry()
        self.x, self.y, self.width, self.height = rect.x(), rect.y(), rect.width(), rect.height()
        self.parser.set('settings', 'geometry', '{0},{1},{2},{3}'.format(self.x, self.y, self.width, self.height))
        self.case = self.dlg.lstCase.currentItem().text() if self.dlg.lstCase.currentItem() else ''
        self.parser.set('settings', 'case', self.case)
        self.aof = self.dlg.cboAOF.currentText() or ''
        self.parser.set('settings', 'aof', self.aof)
        self.term_vel = self.dlg.cboTermVel.currentText() or ''
        self.parser.set('settings', 'term_vel', self.term_vel)
        self.burst_height = self.dlg.cboBurstHeight.currentText() or ''
        self.parser.set('settings', 'burst_height', self.burst_height)
        self.blast_volume = self.dlg.cboBlastVolume.currentText() or ''
        self.parser.set('settings', 'blast_volume', self.blast_volume)
        self.pk_surface = self.dlg.cboPkSurface.currentText() or ''
        self.parser.set('settings', 'pk_surface', self.pk_surface)
        with open(ini_path, 'w') as f:
            self.parser.write(f)
