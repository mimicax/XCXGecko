import traceback

from PyQt4.QtCore import QSize
from PyQt4.QtCore import QTimer
from PyQt4.QtCore import Qt
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QFrame
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPlainTextEdit
from PyQt4.QtGui import QPushButton


class CustomCodeFrame(QFrame):
  poke = pyqtSignal(str, int) # code_label, new_val
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, data_store, parent=None):
    super(CustomCodeFrame, self).__init__(parent)
    self.d = data_store

    self.tmr_reset_bg_clr = QTimer(self)
    self.tmr_reset_bg_clr.setInterval(500) # ms
    self.tmr_reset_bg_clr.timeout.connect(self.resetBGColor)

    self.txt_label = QLineEdit(self)
    self.txt_label.setMaximumWidth(160)
    self.txt_label.setPlaceholderText('Label')

    self.txt_codes = QPlainTextEdit(self)
    self.txt_codes.setMaximumHeight(66)
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

  def onPoke(self):
    # Parse "<ADDR> <WORD>" or "POKE <ADDR> <WORD>" lines
    codes = []
    line_count = 0
    try:
      for line in str(self.txt_codes.toPlainText()).split('\n'):
        line_count += 1
        line = line.strip()
        if len(line) <= 0 or line[0] == '#':
          continue
        tokens = line.split()
        if len(tokens) == 3 and tokens[0] == 'POKE' and len(tokens[1]) == 8 and len(tokens[2]) == 8:
          addr = tokens[1]
          word = tokens[2]
        elif len(tokens) == 2 and len(tokens[0]) == 8 and len(tokens[1]) == 8:
          addr = tokens[0]
          word = tokens[1]
        else:
          raise BaseException('invalid format, expecting POKE XXXXXXXX YYYYYYYY')
        addr_val = int(addr, 16)
        word_val = int(word, 16)
        codes.append((addr_val, word_val))
    except BaseException, e:
      traceback.print_exc()
      self.log.emit('Failed to parse line %d: %s' % (line_count, str(e)), 'red')
      self.setErrorBGColor()
      return

    if len(codes) <= 0:
      self.log.emit('Poke failed: no codes found', 'red')
      self.setErrorBGColor()
      return

    # Sequentially poke codes
    for addr_val, word_val in codes:
      self.poke.emit('%08X' % addr_val, word_val)
