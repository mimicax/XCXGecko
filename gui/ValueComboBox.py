from PyQt4.QtCore import QString
from PyQt4.QtCore import QTimer
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QColor
from PyQt4.QtGui import QComboBox
from PyQt4.QtGui import QCursor
from PyQt4.QtGui import QMenu
from PyQt4.QtGui import QPalette


class ValueComboBox(QComboBox):
  log = pyqtSignal(str, str)

  def __init__(self, dft_values=None, val_bytes=1, parent=None):
    super(ValueComboBox, self).__init__(parent)
    self.val_bytes = val_bytes
    self.val_cap = pow(256, self.val_bytes)

    self.tmr_reset_bg_clr = QTimer(self)
    self.tmr_reset_bg_clr.setInterval(500) # ms
    self.tmr_reset_bg_clr.timeout.connect(self.resetBGColor)

    self.setEditable(True)
    for v in dft_values:
      self.addItem(str(v))

    self.setContextMenuPolicy(Qt.CustomContextMenu)
    self.connect(self, SIGNAL("customContextMenuRequested(const QPoint &)"), self.onMenu)

    self.highlighted[int].connect(self.resetBGColor)
    self.editTextChanged[str].connect(self.resetBGColor)
    self.activated.connect(self.resetBGColor)
    self.currentIndexChanged.connect(self.updateValue)

  def onMenu(self):
    menu = QMenu(self)

    act_dec2hex = QAction('Dec to Hex', self)
    act_dec2hex.triggered.connect(self.onDec2Hex)
    menu.addAction(act_dec2hex)

    menu.addSeparator()

    act_hex2dec = QAction('Hex to Dec', self)
    act_hex2dec.triggered.connect(self.onHex2Dec)
    menu.addAction(act_hex2dec)

    menu.exec_(QCursor.pos())

  def setErrorBGColor(self):
    pal = self.palette()
    pal.setColor(QPalette.Base, QColor(255, 128, 128))
    self.setPalette(pal)
    self.tmr_reset_bg_clr.start()

  def resetBGColor(self):
    if self.tmr_reset_bg_clr.isActive():
      self.tmr_reset_bg_clr.stop()
      pal = self.palette()
      pal.setColor(QPalette.Base, QColor(255, 255, 255))
      self.setPalette(pal)

  def onDec2Hex(self):
    val = self.getValue()
    try:
      dec = int(val)
      if 0 > dec >= -self.val_cap/2:
        dec += self.val_cap
      elif dec >= self.val_cap:
        raise ValueError('value out of range')
      fmt = '0x%%0%dX' % (self.val_bytes*2)
      hx = fmt % dec
      self.lineEdit().setText(hx)
    except ValueError:
      self.log.emit('Failed to convert %s to Hex' % val, 'red')
      self.setErrorBGColor()

  def onHex2Dec(self):
    val = self.getValue()
    try:
      if len(val) > 2 and val[:2] == '0x':
        val = val[2:]
      dec = int(val, 16)
      if dec >= self.val_cap:
        raise ValueError('value out of range')
      self.lineEdit().setText(QString(str(dec)))
    except ValueError:
      self.log.emit('Failed to convert %s to Dec' % val, 'red')
      self.setErrorBGColor()

  def getValue(self):
    txt = self.currentText()
    idx_parenthesis = txt.indexOf('(')
    if idx_parenthesis >= 0:
      txt = txt[:idx_parenthesis]
    return str(txt.trimmed())

  def updateValue(self): # Remove parentheses when selecting from dropdown
    val = self.getValue()
    self.lineEdit().setText(val)
