import struct
import traceback

from PyQt4.QtCore import Qt
from PyQt4.QtCore import QByteArray
from PyQt4.QtCore import QTimer
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QAbstractItemView
from PyQt4.QtGui import QGridLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QTableWidget
from PyQt4.QtGui import QTableWidgetItem
from PyQt4.QtGui import QWidget

from gui.gecko_utils import parse_dec_or_hex, to_signed_hex_str
from gui.ValueComboBox import ValueComboBox


class ScanOffsetWidget(QWidget):
  read_block = pyqtSignal(int, int) # start_addr, num_bytes
  add_code_offset = pyqtSignal(str) # signed_offset_str
  log = pyqtSignal(str, str) # msg, color

  def __init__(self, data_store, code_name, parent=None):
    super(ScanOffsetWidget, self).__init__(parent)
    self.d = data_store
    self.code = None
    self.range_diff = 0x2000

    self.scan_count = 0
    self.cand_addrs = []
    self.scan_addr_start = 0
    self.scan_num_bytes = 0

    self.layout = QGridLayout(self)

    # Obtain key
    ok = False
    try:
      for key in self.d.codes.keys():
        if key.find(code_name) == 0:
          code_name = key
          break
      self.code = self.d.codes[code_name].c[0]
      if self.code.is_ascii:
        self.layout.addWidget(QLabel('Initialization Failed: ASCII-valued code not supported'))
      elif self.code.is_float:
        self.layout.addWidget(QLabel('Initialization Failed: float-valued code not supported'))
      elif self.code.is_ptr:
        self.layout.addWidget(QLabel('Initialization Failed: pointer code not supported'))
      elif self.code.bit_rshift is not 0:
        self.layout.addWidget(QLabel('Initialization Failed: code with bit-shifted base addr not supported'))
      elif not (self.code.num_bytes == 1 or self.code.num_bytes == 2 or self.code.num_bytes == 4):
        self.layout.addWidget(QLabel('Initialization Failed: only 1-/2-/4-byte code supported'))
      else:
        ok = True
    except KeyError, err:
      self.layout.addWidget(QLabel('Initialization Failed: could not find %s in codes' % code_name))

    # Populate GUI
    if ok:
      self.lbl_name = QLabel('Code Name:', self)
      self.layout.addWidget(self.lbl_name, 0, 0)

      self.txt_name = QLineEdit(self.code.label, self)
      self.txt_name.setReadOnly(True)
      self.layout.addWidget(self.txt_name, 0, 1)

      self.lbl_orig_addr = QLabel('Orig Address:', self)
      self.layout.addWidget(self.lbl_orig_addr, 1, 0)

      self.txt_orig_addr = QLineEdit('0x%08X' % self.code.addr_base, self)
      self.txt_orig_addr.setReadOnly(True)
      self.layout.addWidget(self.txt_orig_addr, 1, 1)

      self.txt_magn = QLineEdit(self)
      self.txt_magn.setPlaceholderText('(+/- range)')
      self.layout.addWidget(self.txt_magn, 1, 2)

      self.btn_upd_range = QPushButton(self)
      self.btn_upd_range.setIcon(QIcon('img/flaticon/horizontal-resize.png'))
      self.btn_upd_range.setToolTip('Update Scan Range')
      self.btn_upd_range.setStyleSheet('background-color: white')
      self.btn_upd_range.clicked.connect(self.onUpdateRange)
      self.layout.addWidget(self.btn_upd_range, 1, 3)

      self.lbl_range = QLabel('Scan From/To:', self)
      self.layout.addWidget(self.lbl_range, 2, 0)

      self.txt_range_min = QLineEdit('0x%08X' % (self.code.addr_base - self.range_diff), self)
      self.layout.addWidget(self.txt_range_min, 2, 1)

      self.txt_range_max = QLineEdit('0x%08X' % (self.code.addr_base + self.range_diff), self)
      self.layout.addWidget(self.txt_range_max, 2, 2)

      self.btn_reset = QPushButton(self)
      self.btn_reset.setIcon(QIcon('img/flaticon/update-arrow.png'))
      self.btn_reset.setToolTip('Reset Search')
      self.btn_reset.setStyleSheet('background-color: white')
      self.btn_reset.clicked.connect(self.onReset)
      self.layout.addWidget(self.btn_reset, 2, 3)

      self.lbl_value = QLabel('Current Value:', self)
      self.layout.addWidget(self.lbl_value, 3, 0)

      self.txt_value = ValueComboBox([0, self.code.dft_value], self.code.num_bytes, self)
      self.layout.addWidget(self.txt_value, 3, 1)

      self.btn_scan = QPushButton(self)
      self.btn_scan.setIcon(QIcon('img/flaticon/magnifier13.png'))
      self.btn_scan.setToolTip('Scan')
      self.btn_scan.setStyleSheet('background-color: white')
      self.btn_scan.clicked.connect(self.onScan)
      self.layout.addWidget(self.btn_scan, 3, 3)

      self.tbl_cand = QTableWidget(0, 3, self)
      self.tbl_cand.setHorizontalHeaderLabels(['#', 'Cand. Address', 'Cand. Offset'])
      self.tbl_cand.verticalHeader().setVisible(False)
      self.tbl_cand.horizontalHeader().setStretchLastSection(True)
      self.tbl_cand.setSelectionBehavior(QAbstractItemView.SelectRows)
      self.tbl_cand.setSelectionMode(QAbstractItemView.SingleSelection)
      self.tbl_cand.setShowGrid(True)
      self.tbl_cand.cellClicked.connect(self.onChooseCand)
      self.layout.addWidget(self.tbl_cand, 4, 0, 1, 4)

      self.lbl_offset = QLabel('Code Offset:', self)
      self.layout.addWidget(self.lbl_offset, 5, 0)

      self.txt_offset = QLineEdit('+0', self)
      self.layout.addWidget(self.txt_offset, 5, 1)

      self.btn_accept = QPushButton(self)
      self.btn_accept.setIcon(QIcon('img/flaticon/verification15.png'))
      self.btn_accept.setToolTip('Accept Offset')
      self.btn_accept.setStyleSheet('background-color: white')
      self.btn_accept.clicked.connect(self.onAcceptOffset)
      self.layout.addWidget(self.btn_accept, 5, 3)

    self.setStyleSheet('ScanOffsetWidget {background-color: white}')

    if ok:
      self.onReset()


  @pyqtSlot()
  def onReset(self):
    self.scan_count = 0
    self.cand_addrs = []
    self.scan_addr_start = 0
    self.scan_num_bytes = 0

    self.txt_magn.setEnabled(True)
    self.btn_upd_range.setEnabled(True)
    self.txt_range_min.setEnabled(True)
    self.txt_range_max.setEnabled(True)
    self.txt_offset.setText('+0')
    for idx in xrange(self.tbl_cand.rowCount()):
      self.tbl_cand.removeRow(idx)


  @pyqtSlot()
  def onUpdateRange(self):
    res = parse_dec_or_hex(self.txt_magn.text())
    if res is None:
      self.log.emit('Failed to parse +/- range (valid ex: 114, 0xF0)', 'red')
      return
    elif res[0] <= 0:
      self.log.emit('Specified +/- range must be non-negative', 'red')
      return
    elif (res[0] % self.code.num_bytes) is not 0:
      self.log.emit('Specified +/- range must be a multiple of code width (%s)' % self.code.num_bytes, 'red')
      return
    scan_min = self.code.addr_base - res[0]
    scan_max = self.code.addr_base + res[0]
    if scan_min < 0x10000000:
      self.log.emit('Desired lower bound (0x%08X) is out of range [0x10000000, 0x50000000)' % scan_min, 'red')
      return
    elif scan_max + self.code.num_bytes >= 0x50000000:
      self.log.emit('Desired upper bound (0x%08X) is out of range [0x10000000, 0x50000000)' % scan_max, 'red')
      return
    self.scan_addr_start = scan_min
    self.scan_num_bytes = scan_max - scan_min + self.code.num_bytes
    self.txt_range_min.setText('0x%08X' % scan_min)
    self.txt_range_max.setText('0x%08X' % scan_max)


  @pyqtSlot()
  def onScan(self):
    # Validate txt_value
    res = parse_dec_or_hex(self.txt_value.getValue())
    if res is None:
      self.log.emit('Failed to parse Current Value: must be either DEC or HEX format', 'red')
      return
    elif res[0] < 0:
      self.log.emit('Failed to parse Current Value: must be positive ', 'red')
      return

    if self.scan_count == 0: # Initial scan
      # Parse range min and max
      scan_min = parse_dec_or_hex(self.txt_range_min.text())
      if scan_min is None:
        self.log.emit('Failed to parse Scan From address (format: 0xABCDEF01)', 'red')
        return
      scan_min = scan_min[0]
      if scan_min < 0x10000000:
        self.log.emit('Specified lower bound (0x%08X) is out of range [0x10000000, 0x50000000)' % scan_min, 'red')
        return
      elif ((self.code.addr_base - scan_min) % self.code.num_bytes) is not 0:
        self.log.emit('Specified lower bound (0x%08X) must be within %d-multiple of orig. code address' % (scan_min, self.code.num_bytes), 'red')
        return
      scan_max = parse_dec_or_hex(self.txt_range_max.text())
      if scan_max is None:
        self.log.emit('Failed to parse Scan To address (format: 0xABCDEF01)', 'red')
        return
      scan_max = scan_max[0]
      if scan_max + self.code.num_bytes >= 0x50000000:
        self.log.emit('Specified upper bound (0x%08X) is out of range [0x10000000, 0x50000000)' % scan_max, 'red')
        return
      elif ((scan_max - self.code.addr_base) % self.code.num_bytes) is not 0:
        self.log.emit('Specified upper bound (0x%08X) must be within %d-multiple of orig. code address' % (scan_max, self.code.num_bytes), 'red')
        return
      self.scan_addr_start = scan_min
      self.scan_num_bytes = scan_max - scan_min + self.code.num_bytes
      if self.scan_num_bytes > 0x100000: # heuristically-chosen threshold
        self.log.emit('Scan range (%d bytes) will take too long for pyGecko; specify smaller address range or use Gecko.NET instead' % self.scan_num_bytes, 'red')
        return

    elif len(self.cand_addrs) == 0: # No more candidates left
      self.log.emit('No more candidate addresses remaining; press Reset instead', 'red')
      return

    else: # Non-initial scan
      self.scan_addr_start = self.cand_addrs[0]
      self.scan_num_bytes = self.cand_addrs[-1] - self.cand_addrs[0] + self.code.num_bytes

    self.log.emit('Reading %d bytes from 0x%08X... (GUI will appear non responsive/crashed until done)' % (self.scan_num_bytes, self.scan_addr_start), 'green')
    QTimer.singleShot(10, lambda: self.read_block.emit(self.scan_addr_start, self.scan_num_bytes))


  @pyqtSlot(int, int, QByteArray)
  def onBlockRead(self, addr_start, num_bytes, raw_bytes):
    if addr_start == self.scan_addr_start and num_bytes == self.scan_num_bytes:
      # Validate txt_value
      res = parse_dec_or_hex(self.txt_value.getValue())
      if res is None:
        self.log.emit('Failed to parse Current Value: must be either DEC or HEX format', 'red')
        return
      elif res[0] < 0:
        self.log.emit('Failed to parse Current Value: must be positive', 'red')
        return
      if self.code.num_bytes == 1:
        value_bytes = struct.pack('>B', res[0])
      elif self.code.num_bytes == 2:
        value_bytes = struct.pack('>H', res[0])
      elif self.code.num_bytes == 4:
        value_bytes = struct.pack('>I', res[0])
      else:
        self.log.emit('INTERNAL ERROR: code has %d bytes' % self.code.num_bytes, 'red')
        return

      range_bytes = str(raw_bytes)
      if self.scan_count == 0: # List matching-valued addresses in initial scan
        self.cand_addrs = []
        byte_offset = 0
        while byte_offset < num_bytes:
          addr_curr = addr_start + byte_offset
          if range_bytes[byte_offset:(byte_offset+self.code.num_bytes)] == value_bytes:
            self.cand_addrs.append(addr_curr)
          byte_offset += self.code.num_bytes

      else: # Reduce matching-valued addresses in non-initial scan
        if len(self.cand_addrs) == 0:
          self.log.emit('No more candidate addresses remaining; press Reset instead', 'red')
          return
        idx = 0
        while idx < len(self.cand_addrs):
          addr_curr = self.cand_addrs[idx]
          byte_offset = addr_curr - addr_start
          if byte_offset < 0 or (byte_offset+self.code.num_bytes) > num_bytes:
            self.log.emit('INTERNAL ERROR: byte_offset (%d) out of range [0, %d)' % (byte_offset, num_bytes-self.code.num_bytes), 'red')
            return
          if range_bytes[byte_offset:(byte_offset+self.code.num_bytes)] == value_bytes:
            idx += 1
          else:
            self.cand_addrs.pop(idx)

      # Update scan count
      if self.scan_count == 0:
        self.txt_magn.setEnabled(False)
        self.btn_upd_range.setEnabled(False)
        self.txt_range_min.setEnabled(False)
        self.txt_range_max.setEnabled(False)
      self.scan_count += 1

      # Re-populate table
      exp_rows = len(self.cand_addrs)
      num_rows = self.tbl_cand.rowCount()
      if num_rows > exp_rows:
        for idx in xrange(num_rows-1, exp_rows-1, -1):
          self.tbl_cand.removeRow(idx)
      elif num_rows < exp_rows:
        for idx in xrange(num_rows, exp_rows):
          self.tbl_cand.insertRow(idx)
      for idx in xrange(exp_rows):
        cand_addr = self.cand_addrs[idx]
        item = QTableWidgetItem('%d' % (idx+1))
        item.setTextAlignment(Qt.AlignCenter)
        self.tbl_cand.setItem(idx, 0, item)

        item = QTableWidgetItem('0x%08X' % cand_addr)
        item.setTextAlignment(Qt.AlignCenter)
        self.tbl_cand.setItem(idx, 1, item)

        offset = cand_addr - self.code.addr_base
        item = QTableWidgetItem('%d (%s)' % (offset, to_signed_hex_str(offset)))
        item.setTextAlignment(Qt.AlignCenter)
        self.tbl_cand.setItem(idx, 2, item)

      self.log.emit('Offset scan found %d candidate addresses' % len(self.cand_addrs), 'black')


  @pyqtSlot(int, int)
  def onChooseCand(self, row, col):
    if row < 0 or row >= len(self.cand_addrs):
      self.log.emit('INTERNAL ERROR: selected row (%d) out of range (%d)' % (row, len(self.cand_addrs)), 'red')
      return
    cand_addr = self.cand_addrs[row]
    offset = cand_addr - self.code.addr_base
    self.txt_offset.setText('%d (%s)' % (offset, to_signed_hex_str(offset)))


  @pyqtSlot()
  def onAcceptOffset(self):
    # Parse offset
    txt = self.txt_offset.text()
    idx_parenthesis = txt.indexOf('(')
    if idx_parenthesis >= 0:
      txt = txt[:idx_parenthesis]
    offset, is_hex = parse_dec_or_hex(txt)
    txt_offset = '%d (%s)' % (offset, to_signed_hex_str(offset))
    self.add_code_offset.emit(txt_offset)
    self.log.emit('Added and updated code offset: %s' % txt_offset, 'black')
