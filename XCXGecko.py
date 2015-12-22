#!/usr/bin/python

import socket
import struct
import sys
import time
import traceback
import webbrowser

from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QDockWidget
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QMainWindow
from PyQt4.QtGui import QScrollArea
from PyQt4.QtGui import QTabWidget
from PyQt4.QtGui import QTextEdit

from gui.CodeParser import *
from gui.CustomGeckoWidget import *
from gui.XCXWidget import *
from pygecko.tcpgecko import TCPGecko


class StatusWidget(QDockWidget):
  def __init__(self, parent=None):
    super(QDockWidget, self).__init__('Status', parent)
    self.setFeatures(QDockWidget.DockWidgetMovable)

    self.txt_log = QTextEdit(self)
    self.txt_log.setReadOnly(False)
    self.setWidget(self.txt_log)

    self.setMaximumHeight(120)

  @pyqtSlot(str, str)
  def onLog(self, txt, color='black'):
    now = time.strftime('%x %X')
    html = '<span style="color:%s"><b>[%s]</b>: %s</span><br>' % (color, now, txt)
    self.txt_log.insertHtml(html)
    scroll_bar = self.txt_log.verticalScrollBar()
    scroll_bar.setValue(scroll_bar.maximum())


class XCXGeckoMainWindow(QMainWindow):
  read = pyqtSignal(str) # code_label
  poke = pyqtSignal(str, int) # code_label, new_val
  word_read = pyqtSignal(str, int) # txt_addr, word_val
  log = pyqtSignal(str, str) # msg, color

  def __init__(self):
    super(XCXGeckoMainWindow, self).__init__()
    self.ip = None
    self.conn = None

    parse_error = None
    try:
      self.codes = parse_codes('xcx_v1.0.1e.txt')
    except BaseException, e:
      parse_error = str(e)
      self.codes = {}

    # Setup window
    self.setGeometry(200, 200, 620, 700)
    self.setWindowTitle('XCXGecko')
    self.setWindowIcon(QIcon('img/logo.ico'))

    # Create toolbars
    self.txt_ip = QLineEdit('192.168.0.133', self)
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
    self.wdg_xcx = XCXWidget(self.codes, None)
    self.wdg_xcx.read.connect(self.read)
    self.wdg_xcx.poke.connect(self.poke)
    self.word_read.connect(self.wdg_xcx.word_read)
    self.wdg_xcx.log.connect(self.log)
    self.scr_xcx = QScrollArea(self)
    self.scr_xcx.setWidget(self.wdg_xcx)
    self.scr_xcx.setWidgetResizable(True)
    self.scr_xcx.setMinimumWidth(self.wdg_xcx.minimumWidth())
    self.scr_xcx.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scr_xcx.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    self.wdg_custom = CustomGeckoWidget(self.codes, None)
    self.wdg_custom.read.connect(self.read)
    self.wdg_custom.poke.connect(self.poke)
    self.word_read.connect(self.wdg_custom.word_read)
    self.wdg_custom.log.connect(self.log)
    self.scr_custom = QScrollArea(self)
    self.scr_custom.setWidget(self.wdg_custom)
    self.scr_custom.setWidgetResizable(True)
    self.scr_custom.setMinimumWidth(self.wdg_custom.minimumWidth())
    self.scr_custom.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.scr_custom.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    self.wdg_tabs = QTabWidget(self)
    self.wdg_tabs.addTab(self.scr_xcx, 'XCX')
    self.wdg_tabs.addTab(self.scr_custom, 'Custom Codes')

    self.setCentralWidget(self.wdg_tabs)

    if parse_error is not None:
      self.log.emit('Initialization failed: %s' % parse_error, 'red')
      traceback.print_exc()

    self.read.connect(self.onRead)
    self.poke.connect(self.onPoke)

    self.show()

  def closeEvent(self, event):
    if self.conn is not None:
      self.conn.s.close()
      self.conn = None
      self.ip = None
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
      self.ip = self.txt_ip.text()
      try:
        self.log.emit('Connecting to Wii U on %s...' % self.ip, 'black')
        self.conn = TCPGecko(self.ip)
        self.log.emit('Connected to Wii U on %s' % self.ip, 'green')

        # Auto-read all code addrs # DISABLED FOR NOW SINCE IT TAKES SOME TIME AND BLOCKS
        # self.log.emit('Reading memory for %d code entries' % len(self.codes), 'black')
        # for code_label in self.codes:
        #   self.read.emit(code_label)

      except socket.timeout:
        self.log.emit('Timed out while connecting to Wii U on %s' % self.ip, 'red')
      except socket.error:
        self.log.emit('Failed to connect to Wii U on %s' % self.ip, 'red')

  @pyqtSlot()
  def onDisc(self):
    if self.conn is not None:
      self.conn.s.close()
      self.log.emit('Disconnected from Wii U on %s' % self.ip, 'green')
    self.conn = None
    self.ip = None

  @pyqtSlot(str)
  def onRead(self, code_label):
    try:
      if self.conn is None:
        raise BaseException('not connected to Wii U')

      code = self.codes[str(code_label)]
      if code.num_mem_words != 1:
        raise BaseException('XCXGecko safety check (only supports reading 1 word currently)')
      if code.is_ptr:
        ptr_val = self.conn.readmem(code.base_addr, 4)
        ptr_val = struct.unpack('>I', ptr_val)[0]
        mem_addr = ptr_val+code.ptr_offset
      else:
        mem_addr = code.base_addr

      # Read from one or more 32-bit memory addresses
      val_mem_chr = self.conn.readmem(mem_addr, code.num_mem_words*4)
      val_words = struct.unpack('>' + ('I' * code.num_mem_words), val_mem_chr)

      for val_word in val_words:
        self.word_read.emit(code.txt_addr, val_word)
        break # Currently only support reading 1 word per request

    except BaseException, e:
      self.log.emit('Memory read failed: %s' % str(e), 'red')
      traceback.print_exc()

  @pyqtSlot(str, int)
  def onPoke(self, code_label, new_val):
    try:
      if self.conn is None:
        raise BaseException('not connected to Wii U')

      code = self.codes[str(code_label)]
      if code.num_mem_words != 1:
        raise BaseException('XCXGecko safety check (only supports reading 1 word currently)')
      if code.is_ptr:
        ptr_val = self.conn.readmem(code.base_addr, 4)
        ptr_val = struct.unpack('>I', ptr_val)[0]
        mem_addr = ptr_val+code.ptr_offset
      else:
        mem_addr = code.base_addr

      # Determine bit shift (needed if bit_offset != 0 and/or num_bytes < 4)
      lshift_bits = (32 - code.num_bytes * 8 - code.bit_rshift)
      if lshift_bits < 0:
        raise BaseException('improper code (negative lshift_bits)')  # either num_bytes > 4, or bit_rshift is wrong

      # Compute updated 32-bit value to addr
      if code.num_bytes == 4 and code.bit_rshift == 0:
        new_word = new_val
        # print 'Poke(0x%08X, 0x%08X)' % (mem_addr, new_word)
      else:
        old_word = self.conn.readmem(mem_addr, 4)
        old_word = struct.unpack('>I', old_word)[0]
        word_mask = ((256**code.num_bytes) - 1) << lshift_bits
        new_word = (old_word & ~word_mask) | (new_val << lshift_bits)
        # print ('Poke(0x%08X, bytes=%d, bit_offset=%d, 0x%%0%dX) == Poke(0x%08X, from=0x%08X, to=0x%08X)' %
        #   (mem_addr, code.num_bytes, code.bit_rshift, code.num_bytes*2, mem_addr, old_word, new_word)) % new_val

      self.conn.pokemem(mem_addr, new_word)

    except BaseException, e:
      self.log.emit('Memory poke failed: %s' % str(e), 'red')
      traceback.print_exc()


if __name__ == '__main__':
  app = QApplication(sys.argv)
  gui = XCXGeckoMainWindow()
  sys.exit(app.exec_())
