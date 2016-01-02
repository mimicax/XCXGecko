import time

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDockWidget
from PyQt4.QtGui import QFont
from PyQt4.QtGui import QTextEdit


class StatusWidget(QDockWidget):
  def __init__(self, parent=None):
    super(QDockWidget, self).__init__('Status', parent)
    self.setFeatures(QDockWidget.DockWidgetMovable)

    self.txt_log = QTextEdit(self)
    self.txt_log.setReadOnly(False)
    font = QFont('Monospace')
    font.setStyleHint(QFont.TypeWriter)
    self.txt_log.setFont(font)
    self.setWidget(self.txt_log)

    self.setMaximumHeight(120)

  @pyqtSlot(str, str)
  def onLog(self, txt, color='black'):
    now = time.strftime('%x %X')
    html = '<span style="color:%s"><b>[%s]</b>: %s</span><br>' % (color, now, txt)
    self.txt_log.insertHtml(html)
    scroll_bar = self.txt_log.verticalScrollBar()
    scroll_bar.setValue(scroll_bar.maximum())
