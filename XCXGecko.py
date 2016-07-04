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
from gui.gecko_utils import parse_codes
from xcxgui.XCXWidget import XCXWidget
from xcxgui.GearModWidget import GearModWidget
from xcxgui.ItemIDWidget import ItemIDWidget
from xcxgui.xcx_utils import XCXDataStore
from xcxgui.xcx_utils import parse_item_db
from xcxgui.gear_utils import parse_gear_db


class XCXGeckoMainWindow(GeckoMainWindow):
  def __init__(self):
    GeckoMainWindow.__init__(self)

  def initInterface(self):
    self.d = XCXDataStore()

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
      self.d.parseCfg('config.ini')
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

      item_db_path = self.d.config['item_id_db']
      if item_db_path.find('http') == 0:
        try:
          item_id_db_txt = urllib2.urlopen(item_db_path).read()
        except IOError, e:
          init_errors.append('Failed to load %s: %s' % (item_db_path, str(e)))
          item_db_path = self.d.config['local_item_id_db']
          with open(item_db_path) as f:
            item_id_db_txt = f.read()
      else:
        with open(item_db_path) as f:
          item_id_db_txt = f.read()
      (self.d.item_ids, self.d.item_lines, self.d.item_types) = parse_item_db(item_id_db_txt)
      init_msgs.append('Item ID DB: ' + item_db_path)

      gear_db_path = self.d.config['gear_id_db']
      if gear_db_path.find('http') == 0:
        try:
          gear_id_db_txt = urllib2.urlopen(gear_db_path).read()
        except IOError, e:
          init_errors.append('Failed to load %s: %s' % (gear_db_path, str(e)))
          gear_db_path = self.d.config['local_gear_id_db']
          with open(gear_db_path) as f:
            gear_id_db_txt = f.read()
      else:
        with open(gear_db_path) as f:
          gear_id_db_txt = f.read()
      self.d.gear_ids = parse_gear_db(gear_id_db_txt)
      init_msgs.append('Gear ID DB: ' + gear_db_path)

    except BaseException, e:
      init_errors.append(str(e))
      self.d.codes = {}
      self.d.item_ids = []

    return init_msgs, init_errors

  def initUI(self):
    GeckoMainWindow.initUI(self)

    # Setup window
    self.setGeometry(200, 200, 620, 700)
    self.setWindowTitle('XCXGecko')
    self.setWindowIcon(QIcon('img/logo.ico'))

  def initTabbedWidgets(self): # overload parent fn
    self.wdg_offset = ScanOffsetWidget(self.d, 'Funds Modifier', self)
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

    # wdg_xcx must be initialized before wdg_raw_codes, so that cs.hidden can be updated
    self.wdg_xcx = XCXWidget(self.d, self)
    self.wdg_xcx.read_code.connect(self.read_code)
    self.code_read.connect(self.wdg_xcx.code_read)
    self.wdg_xcx.poke_code.connect(self.poke_code)
    self.wdg_xcx.read_block.connect(self.read_block)
    self.block_read.connect(self.wdg_xcx.block_read)
    self.wdg_xcx.poke_block.connect(self.poke_block)
    self.set_code_offset.connect(self.wdg_xcx.set_code_offset)
    self.wdg_xcx.log.connect(self.log)
    self.scr_xcx = QScrollArea(self)
    self.scr_xcx.setWidget(self.wdg_xcx)
    self.scr_xcx.setWidgetResizable(True)
    self.scr_xcx.setMinimumWidth(self.wdg_xcx.minimumWidth())
    self.scr_xcx.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scr_xcx.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    has_gear_mod = False
    self.wdg_gear_mod = GearModWidget(self.d, self)
    self.wdg_gear_mod.read_block.connect(self.read_block)
    self.block_read.connect(self.wdg_gear_mod.block_read)
    self.wdg_gear_mod.poke_block.connect(self.poke_block)
    self.set_code_offset.connect(self.wdg_gear_mod.set_code_offset)
    self.wdg_gear_mod.log.connect(self.log)
    self.scr_gear_mod = QScrollArea(self)
    self.scr_gear_mod.setWidget(self.wdg_gear_mod)
    self.scr_gear_mod.setWidgetResizable(True)
    self.scr_gear_mod.setMinimumWidth(self.wdg_gear_mod.minimumWidth())
    self.scr_gear_mod.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scr_gear_mod.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    has_gear_mod = True

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

    # self.wdg_item_id = ItemIDWidget()
    # self.wdg_item_id.read_block.connect(self.read_block)
    # self.block_read.connect(self.wdg_item_id.onBlockRead)
    # self.wdg_item_id.poke_block.connect(self.poke_block)
    # self.wdg_item_id.log.connect(self.log)

    self.wdg_tabs.addTab(self.scr_xcx, 'XCX')
    if has_gear_mod:
      self.wdg_tabs.addTab(self.scr_gear_mod, 'Gear Mod')
    self.wdg_tabs.addTab(self.scr_raw_codes, 'Other Codes')
    self.wdg_tabs.addTab(self.scr_custom, 'Custom Codes')
    self.wdg_tabs.addTab(self.scr_offset, 'Global Address Offset')
    # self.wdg_tabs.addTab(self.wdg_item_id, 'Item ID')

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

  logo = QPixmap('img/logo.png').scaledToWidth(200)
  splash = QSplashScreen(logo)
  splash.showMessage('XCXGecko: Loading GUI...')
  splash.show()

  gui = XCXGeckoMainWindow()
  splash.finish(gui)
  sys.exit(app.exec_())
