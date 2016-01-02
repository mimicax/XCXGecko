import struct

from PyQt4.QtCore import QByteArray
from PyQt4.QtCore import QSize
from PyQt4.QtCore import QTimer
from PyQt4.QtCore import Qt
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QFrame
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QFont
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPlainTextEdit
from PyQt4.QtGui import QPushButton

from gecko_utils import parse_custom_codes


class CustomCodeFrame(QFrame):
  poke_code = pyqtSignal(str, int, QByteArray) # code_set_label, code_id, new_bytes
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, code_set, parent=None):
    super(CustomCodeFrame, self).__init__(parent)
    self.cs = code_set

    self.tmr_reset_bg_clr = QTimer(self)
    self.tmr_reset_bg_clr.setInterval(500) # ms
    self.tmr_reset_bg_clr.timeout.connect(self.resetBGColor)

    self.txt_label = QLineEdit(self)
    self.txt_label.setMaximumWidth(160)
    self.txt_label.setPlaceholderText('Label')

    self.txt_codes = QPlainTextEdit(self)
    self.txt_codes.setMaximumHeight(66)
    font = QFont('Monospace')
    font.setStyleHint(QFont.TypeWriter)
    self.txt_codes.setFont(font)
    self.txt_codes.cursorPositionChanged.connect(self.resetBGColor)

    icon_height = self.txt_label.height()*8/15

    self.btn_poke = QPushButton(self)
    self.btn_poke.setIcon(QIcon('img/flaticon/draw39.png'))
    self.btn_poke.setIconSize(QSize(icon_height, icon_height))
    self.btn_poke.setFixedSize(QSize(icon_height*1.5, icon_height*1.5))
    self.btn_poke.setAutoFillBackground(True)
    self.btn_poke.setStyleSheet('background-color: white')
    self.btn_poke.setToolTip('Poke memory')
    self.btn_poke.clicked.connect(self.onPoke)

    self.layout = QHBoxLayout(self)
    self.layout.addWidget(self.txt_label)
    self.layout.setAlignment(self.txt_label, Qt.AlignTop)
    self.layout.addWidget(self.txt_codes)
    self.layout.setAlignment(self.txt_codes, Qt.AlignTop)
    self.layout.addWidget(self.btn_poke)
    self.layout.setAlignment(self.btn_poke, Qt.AlignTop)
    self.layout.setContentsMargins(0, 2, 0, 2)

  def setAlternateBGColor(self):
    self.setStyleSheet('CustomCodeFrame { background-color:rgb(248,248,248) }')

  def setErrorBGColor(self):
    self.txt_codes.setStyleSheet('background-color: rgb(255,128,128)')
    self.tmr_reset_bg_clr.start()

  def resetBGColor(self):
    if self.tmr_reset_bg_clr.isActive():
      self.tmr_reset_bg_clr.stop()
      self.txt_codes.setStyleSheet('background-color: white')

  @pyqtSlot()
  def onPoke(self):
    try:
      parse_custom_codes(self.cs, str(self.txt_codes.toPlainText()))
    except SyntaxError, e:
      self.log.emit(str(e), 'red')
      self.setErrorBGColor()
      return

    if len(self.cs.c) <= 0:
      self.log.emit('POKE failed: no codes found', 'red')
      self.setErrorBGColor()
      return

    # Sequentially poke codes
    for code in self.cs.c:
      raw_bytes = struct.pack('>Q', code.dft_value)[-code.num_bytes:]
      self.poke_code.emit(code.label, code.id, QByteArray(raw_bytes))
