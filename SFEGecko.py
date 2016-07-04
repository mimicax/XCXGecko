#!/usr/bin/python

import sys
import urllib2
import webbrowser
import traceback

from PyQt4.QtCore import Qt
from PyQt4.QtCore import QString
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QPixmap
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QScrollArea
from PyQt4.QtGui import QSplashScreen

from gui.CustomCodesWidget import CustomCodesWidget
from gui.GeckoMainWindow import GeckoMainWindow
from gui.RawCodesWidget import RawCodesWidget
from gui.ScanOffsetWidget import ScanOffsetWidget
from gui.gecko_utils import parse_codes, DataStore


class SFEGeckoMainWindow(GeckoMainWindow):
  def __init__(self):
    GeckoMainWindow.__init__(self)

  def initInterface(self):
    self.d = DataStore()

    (init_msgs, init_errors) = self.initData()

    self.initUI()

    for init_error in init_errors:
      self.log.emit(init_error, 'red')
    for init_msg in init_msgs:
      self.log.emit(init_msg, 'black')

    self.show()

  def initData(self): # override parent fn
    init_msgs = []
    init_errors = []
    try:
      self.d.parseCfg('sfe_config.ini')
      self.d.ip = self.d.config['wiiu_ip']

      code_db_path = self.d.config['code_db']
      if code_db_path.find('http') == 0:
        try:
          code_db_txt = urllib2.urlopen(code_db_path).read()
        except IOError, e:
          init_errors.append('Failed to load %s: %s' % (code_db_path, str(e)))
          code_db_path = self.d.config['local_code_db']
          with open(code_db_path) as f:
            code_db_txt = f.read()
      else:
        with open(self.d.config['code_db']) as f:
          code_db_txt = f.read()
      self.d.codes = parse_codes(code_db_txt)
      init_msgs.append('Code DB: ' + code_db_path)

      print self.d.codes['1-Star Prestige']

    except BaseException, e:
      init_errors.append(str(e))
      self.d.codes = {}
      self.d.item_ids = []

    return init_msgs, init_errors

  def initUI(self):
    GeckoMainWindow.initUI(self)

    # Setup window
    self.setGeometry(200, 200, 620, 700)
    self.setWindowTitle('#FEGecko')
    self.setWindowIcon(QIcon('img/logo.ico'))

  def initTabbedWidgets(self): # overload parent fn
    self.wdg_offset = ScanOffsetWidget(self.d, 'Money', self)
    self.wdg_offset.read_block.connect(self.read_block)
    self.wdg_offset.add_code_offset.connect(self.add_code_offset)
    self.block_read.connect(self.wdg_offset.onBlockRead)
    self.wdg_offset.log.connect(self.log, Qt.DirectConnection)
    self.scr_offset = QScrollArea(self)
    self.scr_offset.setWidget(self.wdg_offset)
    self.scr_offset.setWidgetResizable(True)
    self.scr_offset.setMinimumWidth(self.wdg_offset.minimumWidth())
    self.scr_offset.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scr_offset.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    # wdg_sfe must be initialized before wdg_raw_codes, so that cs.hidden can be updated
    # self.wdg_sfe = XCXWidget(self.d, self)
    # self.wdg_sfe.read_code.connect(self.read_code)
    # self.code_read.connect(self.wdg_sfe.code_read)
    # self.wdg_sfe.poke_code.connect(self.poke_code)
    # self.wdg_sfe.read_block.connect(self.read_block)
    # self.block_read.connect(self.wdg_sfe.block_read)
    # self.wdg_sfe.poke_block.connect(self.poke_block)
    # self.set_code_offset.connect(self.wdg_sfe.set_code_offset)
    # self.wdg_sfe.log.connect(self.log)
    # self.scr_sfe = QScrollArea(self)
    # self.scr_sfe.setWidget(self.wdg_sfe)
    # self.scr_sfe.setWidgetResizable(True)
    # self.scr_sfe.setMinimumWidth(self.wdg_sfe.minimumWidth())
    # self.scr_sfe.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    # self.scr_sfe.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    self.wdg_raw_codes = RawCodesWidget(self.d, self)
    self.wdg_raw_codes.read_code.connect(self.read_code)
    self.code_read.connect(self.wdg_raw_codes.code_read)
    self.wdg_raw_codes.poke_code.connect(self.poke_code)
    self.wdg_raw_codes.log.connect(self.log)
    self.scr_raw_codes = QScrollArea(self)
    self.scr_raw_codes.setWidget(self.wdg_raw_codes)
    self.scr_raw_codes.setWidgetResizable(True)
    self.scr_raw_codes.setMinimumWidth(self.wdg_raw_codes.minimumWidth())
    self.scr_raw_codes.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scr_raw_codes.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    self.wdg_custom = CustomCodesWidget(self.d, self)
    self.wdg_custom.poke_code.connect(self.poke_code)
    self.wdg_custom.log.connect(self.log)
    self.scr_custom = QScrollArea(self)
    self.scr_custom.setWidget(self.wdg_custom)
    self.scr_custom.setWidgetResizable(True)
    self.scr_custom.setMinimumWidth(self.wdg_custom.minimumWidth())
    self.scr_custom.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scr_custom.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    self.wdg_tabs.addTab(self.scr_offset, 'Global Address Offset')
    self.wdg_tabs.addTab(self.scr_raw_codes, 'Other Codes')
    self.wdg_tabs.addTab(self.scr_custom, 'Custom Codes')

  def initToolbars(self):
    GeckoMainWindow.initToolbars(self)

    self.act_home = QAction(QIcon('img/flaticon/home4.png'), 'Open Github project page', self)
    self.act_home.triggered.connect(self.onHomeURL)

    self.act_bugs = QAction(QIcon('img/flaticon/error2.png'), 'Open Github bugs page', self)
    self.act_bugs.triggered.connect(self.onBugsURL)

    self.tbr_links = self.addToolBar('Links')
    self.tbr_links.addAction(self.act_home)
    self.tbr_links.addAction(self.act_bugs)


  @pyqtSlot()
  def onHomeURL(self):
    webbrowser.open('https://github.com/mimicax/XCXGecko')

  @pyqtSlot()
  def onBugsURL(self):
    webbrowser.open('https://github.com/mimicax/XCXGecko/issues')


if __name__ == '__main__':
  app = QApplication(sys.argv)

  #logo = QPixmap('img/logo.png').scaledToWidth(200)
  #splash = QSplashScreen(logo)
  #splash.showMessage('XCXGecko: Loading GUI...')
  #splash.show()

  gui = SFEGeckoMainWindow()
  #splash.finish(gui)
  sys.exit(app.exec_())
