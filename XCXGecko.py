#!/usr/bin/python

import socket
import sys
import webbrowser

from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QMainWindow
from PyQt4.QtGui import QScrollArea
from PyQt4.QtGui import QTabWidget

from gui.CustomCodesWidget import *
from gui.ItemIDWidget import *
from gui.RawCodesWidget import *
from gui.StatusWidget import *
from gui.XCXWidget import *
from pygecko.tcpgecko import TCPGecko


class XCXGeckoMainWindow(QMainWindow):
  read = pyqtSignal(str) # code_label
  word_read = pyqtSignal(str, int) # txt_addr, word_val
  poke = pyqtSignal(str, int) # code_label, new_val
  readmem = pyqtSignal(int, int) # start_addr, num_bytes
  block_read = pyqtSignal(int, int, QByteArray) # start_addr, num_bytes, raw_bytes
  writestr = pyqtSignal(int, QByteArray) # start_addr, ascii_bytes
  log = pyqtSignal(str, str) # msg, color

  def __init__(self):
    super(XCXGeckoMainWindow, self).__init__()
    self.conn = None

    (init_msgs, init_errors) = self.initData()

    self.initUI()

    for init_error in init_errors:
      self.log.emit(init_error, 'red')
    for init_msg in init_msgs:
      self.log.emit(init_msg, 'black')

  def initData(self):
    self.d = DataStore()

    init_msgs = []
    init_errors = []
    try:
      self.d.config = parse_cfg_file('config.ini')
      self.d.ip = self.d.config['wiiu_ip']

      if self.d.config['code_db'].find('http') == 0:
        try:
          code_db_txt = urllib2.urlopen(self.d.config['code_db']).read()
          init_msgs.append('Code DB: ' + self.d.config['code_db'])
        except BaseException, e:
          init_errors.append('Failed to load %s: %s' % (self.d.config['code_db'], str(e)))
          with open(self.d.config['local_code_db']) as f:
            code_db_txt = f.read()
            init_msgs.append('Code DB: ' + self.d.config['local_code_db'])
      else:
        with open(self.d.config['code_db']) as f:
          code_db_txt = f.read()
          init_msgs.append('Code DB: ' + self.d.config['code_db'])
      self.d.codes = parse_codes(code_db_txt)

      if self.d.config['item_id_db'].find('http') == 0:
        try:
          item_id_db_txt = urllib2.urlopen(self.d.config['item_id_db']).read()
          init_msgs.append('Item ID DB: ' + self.d.config['item_id_db'])
        except BaseException, e:
          init_errors.append('Failed to load %s: %s' % (self.d.config['item_id_db'], str(e)))
          with open(self.d.config['local_item_id_db']) as f:
            item_id_db_txt = f.read()
            init_msgs.append('Item ID DB: ' + self.d.config['local_item_id_db'])
      else:
        with open(self.d.config['item_id_db']) as f:
          item_id_db_txt = f.read()
          init_msgs.append('Item ID DB: ' + self.d.config['item_id_db'])
      (self.d.item_ids, self.d.item_lines, self.d.item_types) = parse_item_db(item_id_db_txt)

    except BaseException, e:
      init_errors.append(str(e))
      self.d.codes = {}
      self.d.item_ids = []

    return init_msgs, init_errors

  def initUI(self):
    # Setup window
    self.setGeometry(200, 200, 620, 700)
    self.setWindowTitle('XCXGecko')
    self.setWindowIcon(QIcon('img/logo.ico'))

    # Create toolbars
    self.txt_ip = QLineEdit(self.d.ip, self)
    self.txt_ip.setMaxLength(16)
    self.txt_ip.setFixedWidth(140)
    self.txt_ip.setPlaceholderText('Wii U IP')
    self.txt_ip.setToolTip('Wii U IP')

    self.act_conn = QAction(QIcon('img/flaticon/connector3.png'), 'Connect to Wii U', self)
    self.act_conn.setShortcut('Ctrl-C')
    self.act_conn.triggered.connect(self.onConn)

    self.act_disc = QAction(QIcon('img/flaticon/delete85.png'), 'Disconnect from Wii U', self)
    self.act_disc.setShortcut('Ctrl-D')
    self.act_disc.triggered.connect(self.onDisc)

    self.act_home = QAction(QIcon('img/flaticon/home4.png'), 'Open Github project page', self)
    self.act_home.triggered.connect(self.onHomeURL)

    self.act_bugs = QAction(QIcon('img/flaticon/error2.png'), 'Open Github bugs page', self)
    self.act_bugs.triggered.connect(self.onBugsURL)

    self.tbr_conn = self.addToolBar('Wii U Connection')
    self.tbr_conn.addWidget(self.txt_ip)
    self.tbr_conn.addAction(self.act_conn)
    self.tbr_conn.addAction(self.act_disc)

    self.tbr_links = self.addToolBar('Links')
    self.tbr_links.addAction(self.act_home)
    self.tbr_links.addAction(self.act_bugs)

    # Setup status window
    self.wdg_status = StatusWidget(self)
    self.log.connect(self.wdg_status.onLog)
    self.addDockWidget(Qt.BottomDockWidgetArea, self.wdg_status)
    self.wdg_status.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)

    # Setup tabbed widgets
    self.wdg_xcx = XCXWidget(self.d, self)
    self.wdg_xcx.read.connect(self.read)
    self.word_read.connect(self.wdg_xcx.word_read)
    self.wdg_xcx.poke.connect(self.poke)
    self.wdg_xcx.readmem.connect(self.readmem)
    self.block_read.connect(self.wdg_xcx.block_read)
    self.wdg_xcx.writestr.connect(self.writestr)
    self.wdg_xcx.log.connect(self.log)
    self.scr_xcx = QScrollArea(self)
    self.scr_xcx.setWidget(self.wdg_xcx)
    self.scr_xcx.setWidgetResizable(True)
    self.scr_xcx.setMinimumWidth(self.wdg_xcx.minimumWidth())
    self.scr_xcx.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scr_xcx.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    self.wdg_raw_codes = RawCodesWidget(self.d, self)
    self.wdg_raw_codes.read.connect(self.read)
    self.word_read.connect(self.wdg_raw_codes.word_read)
    self.wdg_raw_codes.poke.connect(self.poke)
    self.wdg_raw_codes.readmem.connect(self.readmem)
    self.block_read.connect(self.wdg_raw_codes.block_read)
    self.wdg_raw_codes.writestr.connect(self.writestr)
    self.wdg_raw_codes.log.connect(self.log)
    self.scr_raw_codes = QScrollArea(self)
    self.scr_raw_codes.setWidget(self.wdg_raw_codes)
    self.scr_raw_codes.setWidgetResizable(True)
    self.scr_raw_codes.setMinimumWidth(self.wdg_raw_codes.minimumWidth())
    self.scr_raw_codes.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scr_raw_codes.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    self.wdg_custom = CustomCodesWidget(self.d, self)
    self.wdg_custom.read.connect(self.read)
    self.word_read.connect(self.wdg_custom.word_read)
    self.wdg_custom.poke.connect(self.poke)
    self.wdg_custom.readmem.connect(self.readmem)
    self.block_read.connect(self.wdg_custom.block_read)
    self.wdg_custom.writestr.connect(self.writestr)
    self.wdg_custom.log.connect(self.log)
    self.scr_custom = QScrollArea(self)
    self.scr_custom.setWidget(self.wdg_custom)
    self.scr_custom.setWidgetResizable(True)
    self.scr_custom.setMinimumWidth(self.wdg_custom.minimumWidth())
    self.scr_custom.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scr_custom.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    self.wdg_item_id = ItemIDWidget()
    self.wdg_item_id.read.connect(self.read)
    self.wdg_item_id.poke.connect(self.poke)
    self.word_read.connect(self.wdg_item_id.onWordRead)
    self.wdg_item_id.log.connect(self.log)

    self.wdg_tabs = QTabWidget(self)
    self.wdg_tabs.addTab(self.scr_xcx, 'XCX')
    self.wdg_tabs.addTab(self.scr_raw_codes, 'Other Codes')
    self.wdg_tabs.addTab(self.scr_custom, 'Custom Codes')
    self.wdg_tabs.addTab(self.wdg_item_id, 'Item ID')

    self.setCentralWidget(self.wdg_tabs)

    self.read.connect(self.onRead)
    self.poke.connect(self.onPoke)
    self.readmem.connect(self.onReadMem)
    self.writestr.connect(self.onWriteStr)

    self.show()

  def closeEvent(self, event):
    if self.conn is not None:
      self.conn.s.close()
      self.conn = None
      self.d.connected = False
    event.accept()

  @pyqtSlot()
  def onHomeURL(self):
    webbrowser.open('https://github.com/mimicax/XCXGecko')

  @pyqtSlot()
  def onBugsURL(self):
    webbrowser.open('https://github.com/mimicax/XCXGecko/issues')

  @pyqtSlot()
  def onConn(self):
    if self.conn is None:
      self.d.ip = self.txt_ip.text()
      try:
        self.log.emit('Connecting to Wii U on %s...' % self.d.ip, 'black')
        self.conn = TCPGecko(self.d.ip)
        self.d.connected = True
        self.log.emit('Connected to Wii U on %s' % self.d.ip, 'green')

      except socket.timeout:
        self.log.emit('Timed out while connecting to Wii U on %s' % self.d.ip, 'red')
        self.d.connected = False
      except socket.error:
        self.log.emit('Failed to connect to Wii U on %s' % self.d.ip, 'red')
        self.d.connected = False

  @pyqtSlot()
  def onDisc(self):
    if self.conn is not None:
      self.conn.s.close()
      self.log.emit('Disconnected from Wii U on %s' % self.d.ip, 'green')
    self.conn = None
    self.d.connected = False

  @pyqtSlot(str)
  def onRead(self, code_txt):
    try:
      if self.conn is None:
        raise BaseException('not connected to Wii U')

      code_txt = str(code_txt)
      if self.d.codes is not None and code_txt in self.d.codes:
        cs = self.d.codes[code_txt]
        for code in cs.c:
          if code.is_ptr:
            if self.d.config['verbose_read']:
              self.log.emit('READ %08X %d' % (code.addr_base, 4), 'blue')
            ptr_val = self.conn.readmem(code.addr_base, 4)
            ptr_val = struct.unpack('>I', ptr_val)[0]
            addr_base = ptr_val + code.ptr_offset
          else: # not code.is_ptr
            addr_base = code.addr_base
  
          # Read from a single 32-bit memory addresses
          num_bytes = 4
          if self.d.config['verbose_read']:
            self.log.emit('READ %08X %d' % (addr_base, num_bytes), 'blue')
          val_mem_chr = self.conn.readmem(addr_base, num_bytes)
          val_word = struct.unpack('>I', val_mem_chr)[0]
          self.word_read.emit(code.addr_txt, val_word)
          
      else: # read raw address
        addr_base = int(code_txt, 16)
        if self.d.config['verbose_read']:
          self.log.emit('READ %08X %d' % (addr_base, 4), 'blue')
        val_mem_chr = self.conn.readmem(addr_base, 4)
        val_word = struct.unpack('>I', val_mem_chr)[0]
        self.word_read.emit(code_txt, val_word)

    except BaseException, e:
      self.log.emit('Memory read failed: %s' % str(e), 'red')
      traceback.print_exc()

  @pyqtSlot(int, int)
  def onReadMem(self, start_addr, num_bytes):
    try:
      if self.conn is None:
        raise BaseException('not connected to Wii U')

      if self.d.config['verbose_read']:
        self.log.emit('READ %08X %d' % (start_addr, num_bytes), 'blue')
      raw_bytes = self.conn.readmem(start_addr, num_bytes)
      qt_bytes = QByteArray(raw_bytes)
      self.block_read.emit(start_addr, num_bytes, qt_bytes)

    except BaseException, e:
      self.log.emit('Block memory read failed: %s' % str(e), 'red')
      traceback.print_exc()

  @pyqtSlot(str, int)
  def onPoke(self, code_txt, new_val):
    try:
      if self.conn is None:
        raise BaseException('not connected to Wii U')

      code_txt = str(code_txt)
      if self.d.codes is not None and code_txt in self.d.codes:
        cs = self.d.codes[code_txt]
        for code in cs.c:
          if code.is_ptr:
            if self.d.config['verbose_read']:
              self.log.emit('READ %08X %d' % (code.addr_base, 4), 'blue')
            ptr_val = self.conn.readmem(code.addr_base, 4)
            ptr_val = struct.unpack('>I', ptr_val)[0]
            mem_addr = ptr_val + code.ptr_offset
          else: # not code.is_ptr
            mem_addr = code.addr_base
  
          # Determine bit shift of word value buffer (required if bit_offset != 0 and/or num_bytes < 4)
          lshift_bits = (32 - code.num_bytes * 8 - code.bit_rshift)
          if lshift_bits < 0:
            raise ValueError('invalid code - negative lshift_bits')  # either num_bytes > 4, or bit_rshift is wrong
  
          # Compute updated 32-bit value to addr
          if code.num_bytes == 4 and code.bit_rshift == 0:
            new_word = new_val
          else:
            if self.d.config['verbose_read']:
              self.log.emit('READ %08X %d' % (mem_addr, 4), 'blue')
            old_word = self.conn.readmem(mem_addr, 4)
            old_word = struct.unpack('>I', old_word)[0]
            word_mask = ((256**code.num_bytes) - 1) << lshift_bits
            new_word = (old_word & ~word_mask) | (new_val << lshift_bits)

          if self.d.config['verbose_poke']:
            self.log.emit('POKE %08X %08X' % (mem_addr, new_word), 'blue')
          self.conn.pokemem(mem_addr, new_word)

      else: # poke raw address
        mem_addr = int(code_txt, 16)
        new_word = new_val

        if self.d.config['verbose_poke']:
          self.log.emit('POKE %08X %08X' % (mem_addr, new_word), 'blue')
        self.conn.pokemem(mem_addr, new_word)

    except BaseException, e:
      self.log.emit('Memory poke failed: %s' % str(e), 'red')
      traceback.print_exc()

  @pyqtSlot(int, QByteArray)
  def onWriteStr(self, start_addr, raw_qbytes):
    try:
      if self.conn is None:
        raise BaseException('not connected to Wii U')

      raw_bytes = bytes(raw_qbytes)
      if self.d.config['verbose_poke_str']:
        msg = 'WRITESTR %08X %s' % (start_addr, bytes(raw_bytes))
        self.log.emit(QString.fromUtf8(msg), 'blue')
      self.conn.writestr(start_addr, raw_bytes)

    except BaseException, e:
      self.log.emit('Memory writestr failed: %s' % str(e), 'red')
      traceback.print_exc()


if __name__ == '__main__':
  app = QApplication(sys.argv)
  gui = XCXGeckoMainWindow()
  sys.exit(app.exec_())


# TODO: re-write read and poke API: takes raw addr int + num_bytes [+val], or code label str [+val]
# TODO: separate GeckoGUI vs XCXGecko
