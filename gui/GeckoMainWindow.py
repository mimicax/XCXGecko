import math
import socket
import struct
import traceback
import urllib2

from PyQt4.QtCore import QByteArray
from PyQt4.QtCore import QString
from PyQt4.QtCore import Qt
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QMainWindow
from PyQt4.QtGui import QScrollArea
from PyQt4.QtGui import QTabWidget

from gui.CustomCodesWidget import CustomCodesWidget
from gui.RawCodesWidget import RawCodesWidget
from gui.StatusWidget import StatusWidget
from gui.gecko_utils import DataStore
from gui.gecko_utils import parse_codes
from pygecko.tcpgecko import TCPGecko


class GeckoMainWindow(QMainWindow):
  read_code = pyqtSignal(str, int) # code_set_label, code_id
  code_read = pyqtSignal(str, int, QByteArray) # code_set_label, code_id, raw_bytes
  poke_code = pyqtSignal(str, int, QByteArray) # code_set_label, code_id, new_bytes

  read_block = pyqtSignal(int, int) # start_addr, num_bytes
  block_read = pyqtSignal(int, int, QByteArray) # start_addr, num_bytes, raw_bytes
  poke_block = pyqtSignal(int, QByteArray, bool) # start_addr, raw_bytes, is_ascii

  log = pyqtSignal(str, str) # msg, color

  def __init__(self):
    super(GeckoMainWindow, self).__init__()
    self.conn = None
    self.initInterface()

  def initInterface(self): # Facilitate inheritance
    (init_msgs, init_errors) = self.initData()

    self.initUI()

    for init_error in init_errors:
      self.log.emit(init_error, 'red')
    for init_msg in init_msgs:
      self.log.emit(init_msg, 'black')

    self.show()

  def initData(self):
    self.d = DataStore()

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

      if self.d.config['loadiine_v4_pygecko']:
        num_codes_adjusted = 0
        for k, cs in self.d.codes.iteritems():
          for c in cs.c:
            # Do not bother fixing addr_txt
            c.addr_base -= 20480
            num_codes_adjusted += 1
        init_msgs.append('Adjusted %d codes for Loadiine v4 + pyGecko' % num_codes_adjusted)

    except BaseException, e:
      init_errors.append(str(e))
      self.d.codes = {}

    return init_msgs, init_errors

  def initUI(self):
    self.initToolbars()

    # Setup status window
    self.wdg_status = StatusWidget(self)
    self.log.connect(self.wdg_status.onLog)
    self.addDockWidget(Qt.BottomDockWidgetArea, self.wdg_status)
    self.wdg_status.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)

    self.wdg_tabs = QTabWidget(self)
    self.initTabbedWidgets()
    self.setCentralWidget(self.wdg_tabs)

    self.read_code.connect(self.onReadCode)
    self.poke_code.connect(self.onPokeCode)
    self.read_block.connect(self.onReadBlock)
    self.poke_block.connect(self.onPokeBlock)

  def initToolbars(self):
    # Create toolbars
    self.txt_ip = QLineEdit(self.d.ip, self)
    self.txt_ip.setMaxLength(16)
    self.txt_ip.setFixedWidth(140)
    self.txt_ip.setPlaceholderText('Wii U IP')
    self.txt_ip.setToolTip('Wii U IP')
    self.txt_ip.setStyleSheet('background-color: white')

    self.act_conn = QAction(QIcon('img/flaticon/connector3.png'), 'Connect to Wii U', self)
    self.act_conn.setShortcut('Ctrl-C')
    self.act_conn.triggered.connect(self.onConn)

    self.act_disc = QAction(QIcon('img/flaticon/delete85.png'), 'Disconnect from Wii U', self)
    self.act_disc.setShortcut('Ctrl-D')
    self.act_disc.triggered.connect(self.onDisc)

    self.tbr_conn = self.addToolBar('Wii U Connection')
    self.tbr_conn.addWidget(self.txt_ip)
    self.tbr_conn.addAction(self.act_conn)
    self.tbr_conn.addAction(self.act_disc)

  def initTabbedWidgets(self):
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

    self.wdg_tabs = QTabWidget(self)
    self.wdg_tabs.addTab(self.scr_raw_codes, 'Other Codes')
    self.wdg_tabs.addTab(self.scr_custom, 'Custom Codes')

    self.setCentralWidget(self.wdg_tabs)

  def closeEvent(self, event):
    if self.conn is not None:
      self.conn.s.close()
      self.conn = None
      self.d.connected = False
      self.txt_ip.setStyleSheet('background-color: white')
    event.accept()

  @pyqtSlot()
  def onConn(self):
    if self.conn is None:
      self.d.ip = self.txt_ip.text()
      try:
        self.txt_ip.setStyleSheet('background-color: rgb(255,255,196)')
        self.txt_ip.repaint()
        self.log.emit('Connecting to Wii U on %s...' % self.d.ip, 'black')
        self.conn = TCPGecko(self.d.ip)
        self.d.connected = True
        self.txt_ip.setStyleSheet('background-color: rgb(196,255,196)')
        self.log.emit('Connected to Wii U on %s' % self.d.ip, 'green')

      except socket.timeout:
        self.log.emit('Timed out while connecting to Wii U on %s' % self.d.ip, 'red')
        self.d.connected = False
        self.txt_ip.setStyleSheet('background-color: white')
      except socket.error:
        self.log.emit('Failed to connect to Wii U on %s' % self.d.ip, 'red')
        self.d.connected = False
        self.txt_ip.setStyleSheet('background-color: white')

  @pyqtSlot()
  def onDisc(self):
    if self.conn is not None:
      self.conn.s.close()
      self.log.emit('Disconnected from Wii U on %s' % self.d.ip, 'green')
    self.txt_ip.setStyleSheet('background-color: white')
    self.conn = None
    self.d.connected = False

  @pyqtSlot(str, int)
  def onReadCode(self, code_set_label, code_id):
    cs_label = str(code_set_label)
    try:
      if self.conn is None:
        raise IOError('not connected to Wii U')

      # Find and validate designated code
      if self.d.codes is None or not (cs_label in self.d.codes):
        return
      cs = self.d.codes[cs_label]
      code = None
      for c in cs.c:
        if c.id == code_id:
          code = c
          break
      if code is None:
        raise LookupError('failed to find code')
      if code.bit_rshift < 0 or code.bit_rshift >= 32:
        raise ValueError('bit_rshift out of [0, 31] range')

      # Read pointer base
      if code.is_ptr:
        if self.d.config['verbose_read']:
          self.log.emit('READ %08X %d' % (code.addr_base, 4), 'blue')
        ptr_val = self.conn.readmem(code.addr_base, 4)
        ptr_val = struct.unpack('>I', ptr_val)[0]
        addr_base = ptr_val + code.ptr_offset
      else: # not code.is_ptr
        addr_base = code.addr_base

      # Read memory addresses
      read_num_bytes = int(math.ceil(float(code.bit_rshift + code.num_bytes*8)/8))
      if self.d.config['verbose_read']:
        self.log.emit('READ %08X %d' % (addr_base, read_num_bytes), 'blue')
      raw_bytes = self.conn.readmem(addr_base, read_num_bytes)

      # Return ASCII code bytes immediately
      if code.is_ascii:
        if code.bit_rshift != 0:
          raise ValueError('no support for bit-shifted ASCII code')
        code_qbytes = QByteArray(raw_bytes)
        self.code_read.emit(code_set_label, code_id, code_qbytes)
        return

      # Handle bit_rshift
      byte_offset = code.bit_rshift / 8
      lshift_bits = code.bit_rshift % 8
      if lshift_bits == 0:
        code_bytes = raw_bytes[byte_offset:(byte_offset+code.num_bytes)]
      else: # read into long, then bit lshift
        long_bytes = raw_bytes[byte_offset:(byte_offset+8)]
        if len(long_bytes) < 8:
          long_bytes += '\00' * (8 - len(long_bytes))
        long_val = struct.unpack('>Q', long_bytes)[0]
        lshift_long_val = (long_val << lshift_bits) & 0xFFFFFFFFFFFFFFFF
        code_bytes = struct.pack('>Q', lshift_long_val)[:code.num_bytes]

      # Return code bytes
      code_qbytes = QByteArray(code_bytes)
      self.code_read.emit(code_set_label, code_id, code_qbytes)

    except (IOError, ValueError), e:
      self.log.emit('READ %s [%d] failed: %s' % (cs_label, code_id, str(e)), 'red')
    except BaseException, e:
      self.log.emit('READ %s [%d] failed: %s' % (cs_label, code_id, str(e)), 'red')
      traceback.print_exc()

  @pyqtSlot(int, int)
  def onReadBlock(self, addr_start, num_bytes):
    try:
      if self.conn is None:
        raise IOError('not connected to Wii U')

      if self.d.config['verbose_read']:
        self.log.emit('READ %08X %d' % (addr_start, num_bytes), 'blue')
      raw_bytes = self.conn.readmem(addr_start, num_bytes)
      qt_bytes = QByteArray(raw_bytes)
      self.block_read.emit(addr_start, num_bytes, qt_bytes)

    except IOError, e:
      self.log.emit('READ BLOCK failed: %s' % str(e), 'red')
    except BaseException, e:
      self.log.emit('READ BLOCK failed: %s' % str(e), 'red')
      traceback.print_exc()

  @pyqtSlot(str, int, QByteArray)
  def onPokeCode(self, code_set_label, code_id, new_qbytes):
    cs_label = str(code_set_label)
    new_bytes = bytes(new_qbytes)
    try:
      if self.conn is None:
        raise IOError('not connected to Wii U')

      # Find and validate designated code
      cs = None
      if self.d.codes is not None and cs_label in self.d.codes:
        cs = self.d.codes[cs_label]
      elif self.d.custom_codes is not None and cs_label in self.d.custom_codes:
        cs = self.d.custom_codes[cs_label]
      else:
        return

      code = None
      for c in cs.c:
        if c.id == code_id:
          code = c
          break
      if code is None:
        raise LookupError('failed to find code')
      if code.bit_rshift < 0 or code.bit_rshift >= 32:
        raise ValueError('bit_rshift out of [0, 31] range')

      # Read pointer base
      if code.is_ptr:
        if self.d.config['verbose_read']:
          self.log.emit('READ %08X %d' % (code.addr_base, 4), 'blue')
        ptr_val = self.conn.readmem(code.addr_base, 4)
        ptr_val = struct.unpack('>I', ptr_val)[0]
        addr_base = ptr_val + code.ptr_offset
      else: # not code.is_ptr
        addr_base = code.addr_base

      # Handle ASCII code separately
      if code.is_ascii:
        if code.bit_rshift != 0:
          raise ValueError('no support for bit-shifted ASCII code')
        if self.d.config['verbose_poke_str']:
          msg = 'WRITESTR %08X %s' % (addr_base, new_bytes)
          self.log.emit(QString.fromUtf8(msg), 'blue')
        self.conn.writestr(addr_base, new_bytes)
        self.onReadCode(code_set_label, code_id) # return updated value from memory to caller
        return

      # Prepare word-aligned data
      word_offset = code.bit_rshift / 32
      lshift_bits = code.bit_rshift % 32
      if lshift_bits != 0: # read 2-word block into long, then bit-mask new bytes
        old_long_bytes = self.conn.readmem(addr_base + word_offset, 8)
        old_long_val = struct.unpack('>Q', old_long_bytes)[0]
        lshift_mask = 64 - lshift_bits - code.num_bytes*8
        mask = (256**code.num_bytes - 1) << lshift_mask
        new_unshifted_bytes = '\00'*(8-code.num_bytes) + new_bytes
        new_unshifted_val = struct.unpack('>Q', new_unshifted_bytes)[0]
        new_long_val = (old_long_val & ~mask) | (new_unshifted_val << lshift_mask)
        new_bytes = struct.pack('>Q', new_long_val)

      # Poke 1/2 words
      if len(new_bytes) <= 4:
        new_bytes += '\00' * (4 - len(new_bytes))
        new_word = struct.unpack('>I', new_bytes)[0]
        if self.d.config['verbose_poke']:
          self.log.emit('POKE %08X %08X' % (addr_base + word_offset, new_word), 'blue')
        self.conn.pokemem(addr_base, new_word)
      elif len(new_bytes) <= 8:
        new_bytes += '\00' * (8 - len(new_bytes))
        new_words = struct.unpack('>II', new_bytes)
        if self.d.config['verbose_poke']:
          self.log.emit('POKE %08X %08X' % (addr_base + word_offset, new_words[0]), 'blue')
        self.conn.pokemem(addr_base, new_words[0])
        if self.d.config['verbose_poke']:
          self.log.emit('POKE %08X %08X' % (addr_base + word_offset + 4, new_words[1]), 'blue')
        self.conn.pokemem(addr_base+4, new_words[1])
      else:
        raise NotImplementedError('no support for >8-byte code')

      # Return updated value from memory to caller
      self.onReadCode(code_set_label, code_id)

    except (IOError, ValueError, NotImplementedError), e:
      self.log.emit('POKE %s [%d] failed: %s' % (cs_label, code_id, str(e)), 'red')
    except BaseException, e:
      self.log.emit('POKE %s [%d] failed: %s' % (cs_label, code_id, str(e)), 'red')
      traceback.print_exc()

  @pyqtSlot(int, QByteArray, bool)
  def onPokeBlock(self, addr_start, raw_qbytes, is_ascii):
    try:
      if self.conn is None:
        raise IOError('not connected to Wii U')

      raw_bytes = bytes(raw_qbytes)
      if is_ascii and self.d.config['verbose_poke_str']:
        msg = 'WRITESTR %08X %s' % (addr_start, raw_bytes)
        self.log.emit(QString.fromUtf8(msg), 'blue')
      elif not is_ascii and self.d.config['verbose_poke_str']:
        if len(raw_bytes) <= 8:
          long_bytes = ('\00' * (8 - len(raw_bytes))) + raw_bytes
          long_val = struct.unpack('>Q', long_bytes)[0]
          fmt = 'POKE %%08X %%0%dX' % (len(raw_bytes) * 2)
          msg = fmt % (addr_start, long_val)
        elif is_ascii:
          msg = 'POKE %08X %s' % (addr_start, raw_bytes)
        else:
          first_word = struct.unpack('>I', raw_bytes[:4])[0]
          msg = 'POKE %08X %08X ... (%d bytes)' % (addr_start, first_word, len(raw_bytes))
        self.log.emit(msg, 'blue')
      self.conn.writestr(addr_start, raw_bytes)

    except IOError, e:
      self.log.emit('WRITESTR failed: %s' % str(e), 'red')
    except BaseException, e:
      self.log.emit('WRITESTR failed: %s' % str(e), 'red')
      traceback.print_exc()
