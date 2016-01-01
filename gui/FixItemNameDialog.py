from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QGridLayout
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPushButton

from gform import *


class FixItemNameDialog(QDialog):
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, type_txt, id_txt, parent=None):
    super(FixItemNameDialog, self).__init__(parent)
    self.type = type_txt
    self.id = id_txt

    self.setWindowTitle('Add/Correct Item Name')

    self.layout = QGridLayout(self)

    self.layout.addWidget(QLabel('Type:'), 0, 0)
    self.txt_type = QLineEdit(type_txt, self)
    self.txt_type.setDisabled(True)
    self.layout.addWidget(self.txt_type, 0, 1)

    self.layout.addWidget(QLabel('ID:'), 1, 0)
    self.txt_id = QLineEdit(id_txt, self)
    self.txt_id.setDisabled(True)
    self.layout.addWidget(self.txt_id, 1, 1)

    self.layout.addWidget(QLabel('Item Name:'), 2, 0)
    self.txt_name = QLineEdit(self)
    self.layout.addWidget(self.txt_name, 2, 1)

    self.layout.addWidget(QLabel('Contributor:'), 3, 0)
    self.txt_contributor = QLineEdit(self)
    self.txt_contributor.setPlaceholderText('anonymous')
    self.layout.addWidget(self.txt_contributor, 3, 1)

    self.btn_submit = QPushButton('Submit', self)
    self.btn_submit.clicked.connect(self.onSubmit)
    self.layout.addWidget(self.btn_submit, 4, 0)
    self.btn_cancel = QPushButton('Cancel', self)
    self.btn_cancel.clicked.connect(self.reject)
    self.layout.addWidget(self.btn_cancel, 4, 1)

  def onSubmit(self):
    self.btn_submit.setDisabled(True)
    name = str(self.txt_name.text())
    if len(name) <= 0:
      self.log.emit('Specify item name before submitting', 'red')
      self.btn_submit.setDisabled(False)
      return
    contributor = str(self.txt_contributor.text())
    if len(contributor) <= 0:
      contributor = 'anonymous'
    try:
      gform_submit_item_name(self.type, self.id, name, contributor)
    except BaseException, e:
      self.log.emit('Failed: %s' % str(e), 'red')
      self.reject()
    self.log.emit('Uploaded item name [%s] for TYPE=%s ID=%s; thank you for contributing!' %
                  (name, self.type, self.id), 'green')
    self.accept()
