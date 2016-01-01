from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from CustomCodeFrame import *


class CustomCodesWidget(QWidget):
  poke_code = pyqtSignal(str, int, QByteArray) # code_set_label, code_id, new_bytes
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, data_store, parent=None):
    super(CustomCodesWidget, self).__init__(parent)
    self.d = data_store
    self.entries = []

    self.btn_add = QPushButton('Add Entry', self)
    self.btn_add.clicked.connect(self.onAdd)

    self.layout = QVBoxLayout(self)
    self.layout.addWidget(self.btn_add)
    self.layout.addStretch()
    self.layout.setSpacing(0)

    self.setStyleSheet('CustomCodesWidget {background-color: white}')

  @pyqtSlot()
  def onAdd(self):
    entry_id = len(self.entries) + 1
    new_cs = CodeSet('__CUSTOM__%d' % entry_id)
    self.d.custom_codes[new_cs.label] = new_cs

    new_entry = CustomCodeFrame(new_cs, self)
    new_entry.poke_code.connect(self.poke_code)
    new_entry.log.connect(self.log)

    self.entries.append(new_entry)
    if entry_id % 2 == 0:
      new_entry.setAlternateBGColor()
    self.layout.insertWidget(len(self.entries), new_entry)
