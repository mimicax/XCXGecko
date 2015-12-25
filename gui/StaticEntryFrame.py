import struct

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

    self.icon_size = QSize(self.val_newval.height(), self.val_newval.height())
    self.read_icon = QIcon('img/flaticon/open135.png')
    self.poke_icon = QIcon('img/flaticon/draw39.png')

    self.btn_curval = QLMRPushButton(' Fetch Value', self)
    self.btn_curval.setIcon(self.read_icon)
    self.btn_curval.setIconSize(self.icon_size)
    self.btn_curval.setToolTip('Read value from memory')
    self.btn_curval.clicked.connect(self.updateCurVal)
    self.btn_curval.right_clicked.connect(self.toggleCurValMode)
    self.btn_curval.setFixedWidth(120)

    self.btn_poke = QPushButton(self)
    self.btn_poke.setIcon(self.poke_icon)
    self.btn_poke.setIconSize(self.icon_size)
    self.btn_poke.setFixedSize(self.icon_size)
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

  @pyqtSlot(str, str)
  def onWordRead(self, txt_addr, word_val):
    if self.code is None:
      return
    if txt_addr == self.code.txt_addr:
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

  def toggleCurValMode(self):
    if self.code is None or self.cur_val is None:
      return
    self.cur_val_mode += 1
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
    self.btn_curval.setText(val_str)

  def updateCurVal(self):
    if self.code is None:
      return
    if self.code.num_mem_words != 1:
      self.log.emit('Missing support for codes straddling across multiple memory words', 'red')
    else:
      self.read.emit(self.code.label)

  def onPoke(self):
    if self.code is None:
      return
    if self.code.is_ascii:
      self.log.emit('Missing support for ASCII codes', 'red')
      return

    # Transform val to decimal
    try:
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
    except ValueError, e:
      self.log.emit('Memory poke failed: %s' % str(e), 'red')
      self.val_newval.setErrorBGColor()

    if self.code.num_mem_words != 1:
      self.log.emit('Missing support for codes straddling across multiple memory words', 'red')
    else:
      self.poke.emit(self.code.label, new_val_dec)
      self.read.emit(self.code.label)
