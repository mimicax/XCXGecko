from PyQt4.QtCore import Qt
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QPushButton


class QLMRPushButton(QPushButton):
  middle_clicked = pyqtSignal()
  right_clicked = pyqtSignal()

  def __init__(self, label='', parent=None):
    super(QLMRPushButton, self).__init__(label, parent)

  def mousePressEvent(self, mouse_event):
    if mouse_event.buttons() == Qt.LeftButton:
      self.clicked.emit(self.isChecked())
    elif mouse_event.buttons() == Qt.MiddleButton:
      self.middle_clicked.emit()
    elif mouse_event.buttons() == Qt.RightButton:
      self.right_clicked.emit()
