import operator

from PyQt4.QtCore import QByteArray
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

from StaticEntryFrame import *


class RawCodesWidget(QWidget):
  read_code = pyqtSignal(str, int) # code_set_label, code_id
  code_read = pyqtSignal(str, int, QByteArray) # code_set_label, code_id, raw_bytes
  poke_code = pyqtSignal(str, int, QByteArray) # code_set_label, code_id, new_bytes
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, data_store, parent=None):
    super(RawCodesWidget, self).__init__(parent)
    self.d = data_store
    self.entries = []

    code_sets = []
    for key in self.d.codes.keys():
      cs = self.d.codes[key]
      if not cs.hidden:
        code_sets.append((cs.c[0].id, cs))
    code_sets.sort(key=lambda c: c[0])
    for id, cs in code_sets:
      self.entries.append(StaticEntryFrame(cs.c[0], cs.label, self))
      for idx in xrange(1, len(cs.c)):
        self.entries.append(StaticEntryFrame(cs.c[idx], '...', self))

    self.layout = QVBoxLayout(self)
    if len(self.entries) > 0:
      even = True
      for entry in self.entries:
        even = not even
        if even:
          entry.setAlternateBGColor()
        self.layout.addWidget(entry)
    else:
      self.layout.addWidget(QLabel('No extra codes found in DB'))
    self.layout.addStretch()
    self.layout.setSpacing(0)

    for entry in self.entries:
      entry.read_code.connect(self.read_code)
      self.code_read.connect(entry.onCodeRead)
      entry.poke_code.connect(self.poke_code)
      entry.log.connect(self.log)

    self.setStyleSheet('RawCodesWidget {background-color: white}')
