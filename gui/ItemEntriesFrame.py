from PyQt4.QtCore import QSize
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QComboBox
from PyQt4.QtGui import QFrame
from PyQt4.QtGui import QGridLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPushButton

from common import *


class ItemEntriesFrame(QFrame):
  read = pyqtSignal(str) # code_label
  poke = pyqtSignal(str, int) # code_label, new_val
  log = pyqtSignal(str, str) # msg, color

  UINT8_VALUES = ['0', '0xFF']
  UINT16_VALUES = ['0', '0xFFFF']
  UINT32_VALUES = ['0', '0xFFFFFFFF']

  MISSING_ITEM_NAME = '[NOT IN DB]'

  def __init__(self, type_val, addr_start, label, max_slots, names, ids, parent=None):
    super(ItemEntriesFrame, self).__init__(parent)
    self.type_val = type_val
    self.addr_start = addr_start
    self.names = names
    self.ids = ids
    self.name_list = []

    self.slot_id = 0
    self.cur_addr = self.addr_start + 3*4*self.slot_id
    self.cur_addr_str = '%08X' % self.cur_addr
    self.cur_val = None

    self.lbl_label = QLabel(label, self)
    self.lbl_label.setToolTip('Type: %02X' % self.type_val)

    self.txt_slot = QComboBox(self)
    for slot_id in xrange(max_slots):
      self.txt_slot.addItem('Slot %03d' % (slot_id+1))
    self.txt_slot.currentIndexChanged[int].connect(self.onChangeSlot)

    self.btn_search = QPushButton(' Search Slots for ID', self)
    self.btn_search.setIcon(QIcon('img/flaticon/magnifier13.png'))
    self.btn_search.clicked.connect(self.onSearchForID)

    self.icon_size = QSize(self.txt_slot.height(), self.txt_slot.height())

    self.btn_read = QPushButton(self)
    self.btn_read.setIcon(QIcon('img/flaticon/open135.png'))
    self.btn_read.setIconSize(self.icon_size)
    self.btn_read.setFixedSize(self.icon_size)
    self.btn_read.setStyleSheet('background-color: white')
    self.btn_read.setToolTip('Read value from memory')
    self.btn_read.clicked.connect(self.onReadVal)

    self.txt_id = QLineEdit(self)
    self.txt_id.setToolTip('ID (hex)')
    self.txt_id.setMaxLength(3)
    self.txt_id.textChanged.connect(self.fetchName)

    self.cmb_names = QComboBox(self)
    self.cmb_names.setEditable(True)
    name_list = sorted(names.values())
    self.cmb_names.addItems(name_list)
    self.cmb_names.lineEdit().setText(self.MISSING_ITEM_NAME)
    self.cmb_names.currentIndexChanged[str].connect(self.fetchID)

    self.txt_amount = QLineEdit(self)
    self.txt_amount.setToolTip('Amount')
    self.txt_amount.setMaxLength(3)

    self.btn_poke = QPushButton(self)
    self.btn_poke.setIcon(QIcon('img/flaticon/draw39.png'))
    self.btn_poke.setIconSize(self.icon_size)
    self.btn_poke.setFixedSize(self.icon_size)
    self.btn_poke.setStyleSheet('background-color: white')
    self.btn_poke.setToolTip('Poke new value into memory')
    self.btn_poke.clicked.connect(self.onPokeVal)

    self.layout = QGridLayout(self)
    self.layout.addWidget(self.lbl_label, 0, 0)
    self.layout.addWidget(self.txt_slot, 0, 1)
    self.layout.addWidget(self.btn_search, 0, 2)
    self.layout.addWidget(self.btn_read, 0, 3)
    self.layout.addWidget(self.txt_id, 1, 0)
    self.layout.addWidget(self.cmb_names, 1, 1)
    self.layout.addWidget(self.txt_amount, 1, 2)
    self.layout.addWidget(self.btn_poke, 1, 3)

    self.updateUI()
    self.show()

  def updateUI(self):
    if self.cur_val is None:
      self.txt_id.setText('')
      self.cmb_names.lineEdit().setText(self.MISSING_ITEM_NAME)
      return

    # Validate current value
    (type_val, id_val, amount) = parse_item_word(self.cur_val)
    if type_val != self.type_val and type_val != 0:
      self.log.emit('Coding error: val(%s)=%08X, type (%02X) != expected (%02X)' %
                    (self.cur_addr_str, self.cur_val, type_val, self.type_val), 'red')
      return

    # Update UI
    self.txt_id.setText('%03X' % id_val)
    self.fetchName()
    self.txt_amount.setText(str(amount))

  def setAlternateBGColor(self):
    self.setStyleSheet('ItemEntriesFrame { background-color:rgb(248,248,248) }')

  @pyqtSlot(int)
  def onChangeSlot(self, slot_id):
    self.slot_id = slot_id
    self.cur_addr = self.addr_start + 3*4*self.slot_id
    self.cur_addr_str = '%08X' % self.cur_addr
    self.txt_id.setText('')
    self.cmb_names.lineEdit().setText(self.MISSING_ITEM_NAME)
    self.onReadVal()

  @pyqtSlot()
  def onSearchForID(self):
    self.log.emit('Item search feature not implemented yet', 'red')

  @pyqtSlot()
  def fetchName(self):
    try:
      id_val = int(str(self.txt_id.text()), 16)
    except ValueError, e:
      return
    name = self.MISSING_ITEM_NAME
    if id_val in self.names:
      name = self.names[id_val]
    self.cmb_names.lineEdit().setText(name)

  @pyqtSlot(str)
  def fetchID(self, name):
    name = str(name)
    id_str = ''
    if name in self.ids:
      id_str = '%02X' % self.ids[name]
    self.txt_id.setText(id_str)

  @pyqtSlot()
  def onReadVal(self):
    self.read.emit(self.cur_addr_str)

  @pyqtSlot()
  def onPokeVal(self):
    try:
      if self.cur_val is None:
        raise BaseException('for safety, must read item memory before poking')

      (type_val, id_val, cur_amount) = parse_item_word(self.cur_val)
      if self.type_val == 0 or cur_amount == 0:
        raise BaseException('cannot poke empty item slot')

      id_txt = str(self.txt_id.text())
      if len(id_txt) <= 0:
        raise BaseException('item ID not specified')

      id_val = int(id_txt, 16)
      if id_val <= 0 or id_val > Item.MAX_ID_VAL:
        raise BaseException('item ID not in [0, %d] range' % Item.MAX_ID_VAL)

      amount_txt = str(self.txt_amount.text())
      if len(amount_txt) <= 0:
        raise BaseException('amount not specified')

      new_amount = int(amount_txt)
      if new_amount < 0 or new_amount > 0xFF:
        raise BaseException('item amount not in [0, 255] range')

      val_word = form_item_word(self.type_val, id_val, new_amount)
      self.poke.emit(self.cur_addr_str, val_word)
      self.read.emit(self.cur_addr_str)

    except BaseException, e:
      #traceback.print_exc()
      self.log.emit('Memory poke failed: ' + str(e), 'red')

  @pyqtSlot(str, int)
  def onWordRead(self, txt_addr, word_val):
    if txt_addr == self.cur_addr_str:
      self.cur_val = word_val
      self.updateUI()
