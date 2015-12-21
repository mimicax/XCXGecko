from PyQt4.QtCore import QSize
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QFrame
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QPushButton

from CodeParser import Code
from ValueComboBox import *


class StaticEntryFrame(QFrame):
  read = pyqtSignal(str) # code_label
  poke = pyqtSignal(str, int) # code_label, new_val
  log = pyqtSignal(str, str) # msg, color

  UINT8_VALUES = ['0', '0xFF']
  UINT16_VALUES = ['0', '0xFFFF']
  UINT32_VALUES = ['0', '0xFFFFFFFF']

  def __init__(self, code, label=None, parent=None):
    super(StaticEntryFrame, self).__init__(parent)
    self.code = code
    self.cur_val = None

    dft_values = []
    if self.code.num_bytes == 1:
      dft_values += self.UINT8_VALUES
    elif self.code.num_bytes == 2:
      dft_values += self.UINT16_VALUES
    elif self.code.num_bytes == 4:
      dft_values += self.UINT32_VALUES
    if self.code.dft_value is not None:
      dft_values.append(self.code.dft_value)

    if label is None:
      label = self.code.label
    self.lbl_label = QLabel(label, self)
    self.lbl_label.setToolTip(self.code.txt_addr)

    self.btn_curval = QPushButton(str(self.cur_val), self)
    self.btn_curval.setToolTip('Read value from memory')
    self.btn_curval.clicked.connect(self.updateCurVal)
    self.btn_curval.setFixedWidth(100)

    self.val_newval = ValueComboBox(dft_values, self.code.num_bytes, self)
    self.val_newval.setToolTip('New value')
    self.val_newval.setFixedWidth(100)

    icon_size = QSize(self.val_newval.height(), self.val_newval.height())
    self.btn_poke = QPushButton(self)
    self.btn_poke.setIcon(QIcon('img/flaticon/pen29.png'))
    self.btn_poke.setIconSize(icon_size)
    self.btn_poke.setFixedSize(icon_size)
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

    self.show()

  def setAlternateBGColor(self):
    self.setStyleSheet('StaticEntryFrame { background-color:rgb(248,248,248) }')

  @pyqtSlot(str, str)
  def onWordRead(self, txt_addr, word_val):
    if txt_addr == self.code.txt_addr:
      if self.code.num_bytes == 4 and self.code.bit_rshift == 0:
        self.cur_val = word_val
      else:
        lshift_bits = (32 - self.code.num_bytes * 8 - self.code.bit_rshift)
        if lshift_bits < 0:
          return # improper code (negative lshift_bits)
        word_mask = ((256**self.code.num_bytes) - 1) << lshift_bits
        self.cur_val = (word_val & word_mask) >> lshift_bits

      val_dec = str(self.cur_val)
      self.btn_curval.setText(val_dec)
      self.val_newval.lineEdit().setText(val_dec)

  def updateCurVal(self):
    if self.code.num_mem_words != 1:
      self.log.emit('Missing support for codes straddling across multiple memory words', 'red')
    else:
      self.read.emit(self.code.label)

  def onPoke(self):
    # Transform val to decimal
    new_val = self.val_newval.getValue()
    val_cap = 256 ** self.code.num_bytes
    if len(new_val) > 2 and new_val[:2] == '0x':
      new_val_dec = int(str(new_val[2:]), 16)
    else:
      new_val_dec = int(new_val)
    if new_val_dec > val_cap or new_val_dec < -val_cap / 2:
      self.log.emit('Requested value does not fit in %d bytes' % self.code.num_bytes, 'red')
      self.val_newval.setErrorBGColor()
      return
    if new_val_dec < 0:
      new_val_dec += val_cap

    if self.code.num_mem_words != 1:
      self.log.emit('Missing support for codes straddling across multiple memory words', 'red')
    else:
      self.poke.emit(self.code.label, new_val_dec)
      self.read.emit(self.code.label)
