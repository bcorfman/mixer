# -*- mode: python -*-

block_cipher = None

def getinstalldir(package):
    from importlib import import_module
    import inspect

    module = import_module(package)
    return os.path.dirname(inspect.getsourcefile(module))

a = Analysis(['stage.py'],
             pathex=[''],
             binaries=None,
             datas=[('paramdlg.ui', './'),
                    ('mayavi_win.ui', './'),
                    ('Dimension_16xLG.png', './'),
                    ('house_16xLG.png', './'),
                    ('save_16xLG.png', '.'),
                    ('2000px-Crystal_Clear_app_3d.svg.png', './'),
                    ('LICENSE', '.'),
                    ('README.txt', '.')],
             hiddenimports=['multiprocessing', ''],
             hookspath=[],
             runtime_hooks=['rthook_qtapi.py', 'rthook_pyqt4.py'],
             excludes=['Tkinter', 'FixTk', 'PyQt5', 'pyface.wx', 'traitsui.wx', 'IPython', 'wx', 'PyQt4.QtXml',
             'PyQt4.QtSql', 'PyQt4.QtAssistant', 'posix', 'pickle', 'urllib', 'java', 'java.lang'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=False,
          name='stage',
          debug=True,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='stage')