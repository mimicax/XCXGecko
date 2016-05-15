import struct

from PyQt4.QtCore import QByteArray
from PyQt4.QtCore import QSize
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QFrame
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QPushButton

from QLMRPushButton import QLMRPushButton
from ValueComboBox import ValueComboBox


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)


class StaticEntryFrame(QFrame):
  read_code = pyqtSignal(str, int) # code_set_label, code_id
  poke_code = pyqtSignal(str, int, QByteArray) # code_set_label, code_id, new_bytes
  log = pyqtSignal(str, str) # msg, color

  DISPLAY_MODES = enum('DEC', 'HEX', 'FLOAT', 'ASCII')
  UINT8_VALUES = ['0', '0xFF']
  UINT16_VALUES = ['0', '0xFFFF']
  UINT32_VALUES = ['0', '0xFFFFFFFF']

  def __init__(self, code, label=None, parent=None):
    super(StaticEntryFrame, self).__init__(parent)
    self.code = code
    self.cur_bytes = None
    self.display_mode = StaticEntryFrame.DISPLAY_MODES.DEC

    if label is None:
      label = self.code.label
    self.lbl_label = QLabel(label, self)

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
    self.btn_curval.clicked.connect(self.readCode)
    self.btn_curval.right_clicked.connect(self.toggleCurValMode)
    self.btn_curval.setFixedWidth(120)

    self.btn_poke = QPushButton(self)
    self.btn_poke.setIcon(self.poke_icon)
    self.btn_poke.setIconSize(self.icon_size)
    self.btn_poke.setFixedSize(QSize(icon_height*1.5, icon_height*1.5))
    self.btn_poke.setAutoFillBackground(True)
    self.btn_poke.setStyleSheet('background-color: white')
    self.btn_poke.setToolTip('Poke new value into memory')
    self.btn_poke.clicked.connect(self.pokeCode)

    self.layout = QHBoxLayout(self)
    self.layout.addWidget(self.lbl_label)
    self.layout.addWidget(self.btn_curval)
    self.layout.addWidget(self.val_newval)
    self.layout.addWidget(self.btn_poke)
    self.layout.setContentsMargins(0, 2, 0, 2)

    self.val_newval.log.connect(self.log)

    self.updateUI()

  def updateUI(self):
    num_bytes = 4
    dft_values = []
    if self.code is not None:
      num_bytes = self.code.num_bytes
      if self.code.dft_value is not None:
        if self.code.is_float and isinstance(self.code.dft_value, int):
          value_raw = struct.pack('>I', self.code.dft_value)
          value_float = struct.unpack('>f', value_raw)[0]
          dft_values.append(str(value_float))
        else:
          dft_values.append(str(self.code.dft_value))
      if not self.code.is_ascii and not self.code.is_float:
        if self.code.num_bytes == 1:
          dft_values += StaticEntryFrame.UINT8_VALUES
        elif self.code.num_bytes == 2:
          dft_values += StaticEntryFrame.UINT16_VALUES
        elif self.code.num_bytes == 4:
          dft_values += StaticEntryFrame.UINT32_VALUES

    if self.cur_bytes is None:
      self.btn_curval.setText(' Fetch Value')
      self.btn_curval.setIcon(self.read_icon)
      self.btn_curval.setIconSize(self.icon_size)
    else:
      if self.display_mode == StaticEntryFrame.DISPLAY_MODES.DEC:
        cur_long = struct.unpack('>Q', ('\00'*(8 - len(self.cur_bytes)) + self.cur_bytes))[0]
        val_str = str(cur_long)
      elif self.display_mode == StaticEntryFrame.DISPLAY_MODES.FLOAT:
        val_str = str(struct.unpack('>f', self.cur_bytes)[0])
      elif self.display_mode == StaticEntryFrame.DISPLAY_MODES.ASCII:
        val_str = self.cur_bytes.encode('utf-8')
      else: # Assume HEX by default
        cur_long = struct.unpack('>Q', ('\00'*(8 - len(self.cur_bytes)) + self.cur_bytes))[0]
        fmt = '0x%%0%dX' % (self.code.num_bytes*2)
        val_str = fmt % cur_long
      self.btn_curval.setText(val_str)
      self.btn_curval.setIcon(QIcon())
      self.val_newval.lineEdit().setText(val_str)

    self.val_newval.updateValues(dft_values, num_bytes)

    if self.code is None:
      self.btn_curval.setDisabled(True)
      self.val_newval.setDisabled(True)
      self.btn_poke.setDisabled(True)
    else:
      self.btn_curval.setDisabled(False)
      self.val_newval.setDisabled(False)
      self.btn_poke.setDisabled(False)

  def changeCode(self, new_code):
    self.code = new_code
    self.cur_bytes = None
    self.updateUI()

  def setAlternateBGColor(self):
    self.setStyleSheet('StaticEntryFrame { background-color:rgb(248,248,248) }')

  def toggleCurValMode(self):
    if self.code is None or self.cur_bytes is None:
      return
    self.display_mode += 1
    try:
      if self.display_mode == StaticEntryFrame.DISPLAY_MODES.HEX:
        cur_long = struct.unpack('>Q', ('\00'*(8 - len(self.cur_bytes)) + self.cur_bytes))[0]
        fmt = '0x%%0%dX' % (self.code.num_bytes*2)
        val_str = fmt % cur_long
      elif self.display_mode == StaticEntryFrame.DISPLAY_MODES.FLOAT:
        val_str = str(struct.unpack('>f', self.cur_bytes)[0])
      elif self.display_mode == StaticEntryFrame.DISPLAY_MODES.ASCII:
        val_str = self.cur_bytes.encode('utf-8')
      else: # assume DEC by default
        self.display_mode = StaticEntryFrame.DISPLAY_MODES.DEC
        cur_long = struct.unpack('>Q', ('\00'*(8 - len(self.cur_bytes)) + self.cur_bytes))[0]
        val_str = str(cur_long)
    except struct.error, e:
      self.display_mode = StaticEntryFrame.DISPLAY_MODES.DEC
      cur_long = struct.unpack('>Q', ('\00'*(8 - len(self.cur_bytes)) + self.cur_bytes))[0]
      val_str = str(cur_long)
    except UnicodeDecodeError, e:
      self.display_mode = StaticEntryFrame.DISPLAY_MODES.DEC
      cur_long = struct.unpack('>Q', ('\00'*(8 - len(self.cur_bytes)) + self.cur_bytes))[0]
      val_str = str(cur_long)
    self.btn_curval.setText(val_str)

  @pyqtSlot()
  def readCode(self):
    if self.code is None:
      return
    self.read_code.emit(self.code.label, self.code.id)

  @pyqtSlot(str, int, QByteArray)
  def onCodeRead(self, code_set_label, code_id, raw_qbytes):
    if self.code is None:
      return
    if self.code.label != code_set_label or self.code.id != code_id:
      return

    self.cur_bytes = bytes(raw_qbytes)
    if self.code.is_ascii:
      val_str = self.cur_bytes
      eos_idx = val_str.find('\00')
      if eos_idx >= 0:
        val_str = val_str[:eos_idx]
      parse_failed = False
      try:
        val_str = val_str.decode('utf-8')
      except UnicodeDecodeError, e:
        parse_failed = True # hack to prevent try inside catch
      if parse_failed:
        try:
          val_str = val_str[:-1].decode('utf-8')
        except UnicodeDecodeError, e:
          self.log.emit('Could not decode ASCII content', 'red')
          val_str = ''
      self.display_mode = StaticEntryFrame.DISPLAY_MODES.ASCII
    elif self.code.is_float:
      val_str = str(struct.unpack('>f', self.cur_bytes)[0])
      self.display_mode = StaticEntryFrame.DISPLAY_MODES.FLOAT
    else:
      cur_long = struct.unpack('>Q', ('\00'*(8 - len(self.cur_bytes)) + self.cur_bytes))[0]
      if self.display_mode == StaticEntryFrame.DISPLAY_MODES.DEC:
        val_str = str(cur_long)
      else:
        self.display_mode = StaticEntryFrame.DISPLAY_MODES.HEX
        fmt = '0x%%0%dX' % (self.code.num_bytes*2)
        val_str = fmt % cur_long
    self.btn_curval.setText(val_str)
    self.btn_curval.setIcon(QIcon())
    self.val_newval.lineEdit().setText(val_str)

  @pyqtSlot()
  def pokeCode(self):
    if self.code is None:
      return
    try:
      # Process ASCII code
      if self.code.is_ascii:
        new_qbytes = self.val_newval.currentText().toUtf8()
        if len(new_qbytes) > self.code.num_bytes:
          new_qbytes = new_qbytes[:self.code.num_bytes]
        try:
          str(new_qbytes).decode('utf-8')
        except UnicodeDecodeError, e:
          new_qbytes = new_qbytes[:-1]
        if len(new_qbytes) < self.code.num_bytes:
          new_qbytes += ('\00' * self.code.num_bytes)

        # Poke and update
        self.poke_code.emit(self.code.label, self.code.id, new_qbytes)
        return

      # Convert desired value into raw bytes
      new_val_str = self.val_newval.getValue()
      if len(new_val_str) <= 0:
        self.log.emit('Missing code value', 'red')
        self.val_newval.setErrorBGColor()
        return
      if len(new_val_str) > 2 and new_val_str[:2] == '0x':
        if len(new_val_str) != 2 + self.code.num_bytes*2:
          self.log.emit('Invalid hex value, code expects %d hex' % (self.code.num_bytes*2), 'red')
          self.val_newval.setErrorBGColor()
          return
        new_val = int(str(new_val_str[2:]), 16)
        new_bytes = struct.pack('>Q', new_val)[-self.code.num_bytes:]
      elif self.code.is_float:
        new_bytes = struct.pack('>f', float(new_val_str))
      else:
        new_val = int(new_val_str)
        val_cap = 256 ** self.code.num_bytes
        if new_val > val_cap or new_val < -val_cap / 2:
          self.log.emit('Requested code value does not fit in %d bytes' % self.code.num_bytes, 'red')
          self.val_newval.setErrorBGColor()
          return
        if new_val < 0:
          new_val += val_cap
        new_bytes = struct.pack('>Q', new_val)[-self.code.num_bytes:]

      # Poke code
      new_qbytes = QByteArray(new_bytes)
      self.poke_code.emit(self.code.label, self.code.id, new_qbytes)

    except ValueError, e:
      self.log.emit('Parser failed: %s' % str(e), 'red')
      self.val_newval.setErrorBGColor()
