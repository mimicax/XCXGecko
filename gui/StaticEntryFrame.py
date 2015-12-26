import struct

from PyQt4.QtCore import QByteArray
from PyQt4.QtCore import QSize
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QFrame
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel

from QLMRPushButton import *
from ValueComboBox import *


class StaticEntryFrame(QFrame):
  read = pyqtSignal(str) # code_label
  poke = pyqtSignal(str, int) # code_label, new_val
  readmem = pyqtSignal(int, int) # start_addr, num_bytes
  writestr = pyqtSignal(int, QByteArray) # start_addr, ascii_bytes
  log = pyqtSignal(str, str) # msg, color

  CUR_VAL_MODES = ['dec', 'hex', 'float', 'ascii']
  UINT8_VALUES = ['0', '0xFF']
  UINT16_VALUES = ['0', '0xFFFF']
  UINT32_VALUES = ['0', '0xFFFFFFFF']

  def __init__(self, code, label=None, parent=None):
    super(StaticEntryFrame, self).__init__(parent)
    self.code = code
    self.cur_val = None
    self.cur_val_mode = 0

    if label is None:
      label = self.code.label
    self.lbl_label = QLabel(label, self)
    if self.code is not None:
      self.lbl_label.setToolTip(self.code.txt_addr)

    self.val_newval = ValueComboBox([], 4, self)
    self.val_newval.setToolTip('New value')
    self.val_newval.setFixedWidth(120)

    icon_height = self.val_newval.height()*5/6
    self.icon_size = QSize(icon_height, icon_height)
    self.read_icon = QIcon('img/flaticon/open135.png')
    self.poke_icon = QIcon('img/flaticon/draw39.png')

    self.btn_curval = QLMRPushButton(' Fetch Value', self)
    self.btn_curval.setIcon(self.read_icon)
    self.btn_curval.setIconSize(self.icon_size)
    self.btn_curval.setToolTip('Read value from memory')
    self.btn_curval.clicked.connect(self.readCurVal)
    self.btn_curval.right_clicked.connect(self.toggleCurValMode)
    self.btn_curval.setFixedWidth(120)

    self.btn_poke = QPushButton(self)
    self.btn_poke.setIcon(self.poke_icon)
    self.btn_poke.setIconSize(self.icon_size)
    self.btn_poke.setFixedSize(QSize(icon_height*1.5, icon_height*1.5))
    self.btn_poke.setAutoFillBackground(True)
    self.btn_poke.setStyleSheet('background-color: white')
    self.btn_poke.setToolTip('Poke new value into memory')
    self.btn_poke.clicked.connect(self.onPoke)

    self.layout = QHBoxLayout(self)
    self.layout.addWidget(self.lbl_label)
    self.layout.addWidget(self.btn_curval)
    self.layout.addWidget(self.val_newval)
    self.layout.addWidget(self.btn_poke)
    self.layout.setContentsMargins(0, 2, 0, 2)

    self.val_newval.log.connect(self.log)

    self.updateUI()
    self.show()

  def updateUI(self):
    num_bytes = 4
    dft_values = []
    if self.code is not None:
      num_bytes = self.code.num_bytes
      if self.code.num_bytes == 1:
        dft_values += self.UINT8_VALUES
      elif self.code.num_bytes == 2:
        dft_values += self.UINT16_VALUES
      elif self.code.num_bytes == 4:
        dft_values += self.UINT32_VALUES
      if self.code.dft_value is not None:
        dft_values.append(self.code.dft_value)

    if self.cur_val is None:
      self.btn_curval.setText(' Fetch Value')
      self.btn_curval.setIcon(self.read_icon)
      self.btn_curval.setIconSize(self.icon_size)
    else:
      cur_val_dec = str(self.cur_val)
      self.btn_curval.setText(cur_val_dec)
      self.btn_curval.setIcon(QIcon())
      self.val_newval.lineEdit().setText(cur_val_dec)

    self.val_newval.updateValues(dft_values, num_bytes)

    if self.code is None:
      self.lbl_label.setToolTip('Code not available')
      self.btn_curval.setDisabled(True)
      self.val_newval.setDisabled(True)
      self.btn_poke.setDisabled(True)
    else:
      self.lbl_label.setToolTip(self.code.txt_addr)
      self.btn_curval.setDisabled(False)
      self.val_newval.setDisabled(False)
      self.btn_poke.setDisabled(False)

  def changeCode(self, new_code):
    self.code = new_code
    self.cur_val = None
    self.updateUI()

  def setAlternateBGColor(self):
    self.setStyleSheet('StaticEntryFrame { background-color:rgb(248,248,248) }')

  @pyqtSlot(str, int)
  def onWordRead(self, txt_addr, word_val):
    if self.code is None:
      return
    if txt_addr == self.code.txt_addr:
      if word_val < 0:
        self.cur_val = 0x100000000 - word_val
      else:
        self.cur_val = word_val
      if self.code.num_bytes < 4 or self.code.bit_rshift != 0:
        lshift_bits = (32 - self.code.num_bytes * 8 - self.code.bit_rshift)
        if lshift_bits < 0:
          return # improper code (negative lshift_bits)
        word_mask = ((256**self.code.num_bytes) - 1) << lshift_bits
        self.cur_val = (word_val & word_mask) >> lshift_bits

      if self.code.is_ascii:
        val_str = struct.pack('>I', self.cur_val)
        self.cur_val_mode = 3
      elif self.code.is_float:
        val_str = str(struct.unpack('>f', struct.pack('>I', self.cur_val))[0])
        self.cur_val_mode = 2
      else:
        val_str = str(self.cur_val)
        self.cur_val_mode = 0
      self.btn_curval.setText(val_str)
      self.btn_curval.setIcon(QIcon())
      self.val_newval.lineEdit().setText(val_str)

  @pyqtSlot(int, int, QByteArray)
  def onBlockRead(self, addr_start, num_bytes, raw_bytes):
    if (self.code is not None) and (self.code.is_ascii) and (not self.code.is_ptr) and \
       (addr_start == self.code.base_addr) and (num_bytes == self.code.num_bytes+1):
      val_str = raw_bytes.data()
      eos_idx = val_str.find('\0')
      if eos_idx >= 0:
        val_str = val_str[:eos_idx]
      try:
        val_str = val_str.decode('utf-8')
      except UnicodeDecodeError, e:
        val_str = val_str[:-1].decode('utf-8')

      self.cur_val_mode = 3
      self.btn_curval.setText(val_str)
      self.btn_curval.setIcon(QIcon())
      self.val_newval.lineEdit().setText(val_str)

  def toggleCurValMode(self):
    if self.code is None or self.cur_val is None:
      return
    self.cur_val_mode += 1
    try:
      if self.cur_val_mode == 1: # hex
        fmt = '0x%%0%dX' % self.code.num_bytes
        val_str = fmt % self.cur_val
      elif self.cur_val_mode == 2: # float
        val_str = str(struct.unpack('>f', struct.pack('>I', self.cur_val))[0])
      elif self.cur_val_mode == 3: # ascii
        val_str = struct.pack('>I', self.cur_val)
      else: # assume mode 0 by default
        self.cur_val_mode = 0
        val_str = str(self.cur_val)
    except struct.error, e:
      self.cur_val_mode = 0
      val_str = str(self.cur_val)
    self.btn_curval.setText(val_str)

  def readCurVal(self):
    if self.code is None:
      return
    if self.code.is_ascii and not self.code.is_ptr:
      self.readmem.emit(self.code.base_addr, self.code.num_bytes+1)
    elif self.code.num_mem_words == 1:
      self.read.emit(self.code.label)
    else:
      self.log.emit('Missing support for codes straddling across multiple memory words', 'red')

  def onPoke(self):
    if self.code is None:
      return
    try:
      # Process ASCII code
      if self.code.is_ascii:
        if self.code.is_ptr:
          self.log.emit('Missing support for ASCII pointer codes', 'red')
        else:
          new_qbytes = self.val_newval.currentText().toUtf8()
          if len(new_qbytes) > self.code.num_bytes:
            new_qbytes = new_qbytes[:self.code.num_bytes]
          try:
            str(new_qbytes).decode('utf-8')
          except UnicodeDecodeError, e:
            new_qbytes = new_qbytes[:-1]
          if new_qbytes[-1] != '\0':
            new_qbytes.append('\0')

          # Poke and update
          self.writestr.emit(self.code.base_addr, new_qbytes)
          self.readmem.emit(self.code.base_addr, self.code.num_bytes+1)
        return

      # Process decimal code: transform val to decimal
      new_val_str = self.val_newval.getValue()
      if self.code.is_float:
        if len(new_val_str) > 2 and new_val_str[:2] == '0x':
          new_val_dec = int(str(new_val_str[2:]), 16)
        else:
          new_val_dec = struct.unpack('>I', struct.pack('>f', float(new_val_str)))[0]
      else:
        val_cap = 256 ** self.code.num_bytes
        if len(new_val_str) > 2 and new_val_str[:2] == '0x':
          new_val_dec = int(str(new_val_str[2:]), 16)
        else:
          new_val_dec = int(new_val_str)
        if new_val_dec > val_cap or new_val_dec < -val_cap / 2:
          self.log.emit('Requested value does not fit in %d bytes' % self.code.num_bytes, 'red')
          self.val_newval.setErrorBGColor()
          return
        if new_val_dec < 0:
          new_val_dec += val_cap

        # Poke and update
        if self.code.num_mem_words != 1:
          self.log.emit('Missing support for codes straddling across multiple memory words', 'red')
        else:
          self.poke.emit(self.code.label, new_val_dec)
          self.read.emit(self.code.label)

    except ValueError, e:
      self.log.emit('Memory poke failed: %s' % str(e), 'red')
      self.val_newval.setErrorBGColor()
