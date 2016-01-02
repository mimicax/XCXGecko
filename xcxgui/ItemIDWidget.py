import struct

from PyQt4.QtCore import QByteArray
from PyQt4.QtCore import QDir
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QFileDialog
from PyQt4.QtGui import QFont
from PyQt4.QtGui import QGridLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPlainTextEdit
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QWidget

from xcx_utils import Item
from xcx_utils import parse_item_db


class ItemIDWidget(QWidget):
  read_block = pyqtSignal(int, int) # start_addr, num_bytes
  poke_block = pyqtSignal(int, QByteArray, bool) # start_addr, raw_bytes, is_ascii

  log = pyqtSignal(str, str)  # msg, color

  def __init__(self, parent=None):
    super(ItemIDWidget, self).__init__(parent)
    self.custom_db = dict()
    self.custom_db_lines = []
    self.item_types = []

    self.layout = QGridLayout(self)

    self.lbl_path_db = QLabel('DB not loaded', self)
    self.layout.addWidget(self.lbl_path_db, 0, 0, 1, 2)
    self.btn_load_db = QPushButton(' Load Custom DB', self)
    self.btn_load_db.setIcon(QIcon('img/flaticon/file186.png'))
    self.btn_load_db.clicked.connect(self.loadDB)
    self.layout.addWidget(self.btn_load_db, 0, 2)
    self.btn_save_db = QPushButton(' Save Custom DB', self)
    self.btn_save_db.setIcon(QIcon('img/flaticon/save31.png'))
    self.btn_save_db.clicked.connect(self.saveDB)
    self.layout.addWidget(self.btn_save_db, 0, 3)

    self.txt_addr = QLineEdit(self)
    self.txt_addr.setPlaceholderText('Memory Address')
    self.txt_addr.setMaxLength(10)
    self.layout.addWidget(self.txt_addr, 1, 0)

    self.btn_curval = QPushButton(' Fetch Value', self)
    self.btn_curval.setIcon(QIcon('img/flaticon/open135.png'))
    self.btn_curval.clicked.connect(self.onReadWord)
    self.layout.addWidget(self.btn_curval, 1, 1)

    self.ico_auto_incr_off = QIcon('img/flaticon/delete85.png')
    self.ico_auto_incr_on = QIcon('img/flaticon/verification15.png')
    self.btn_auto_incr = QPushButton(' Auto Increment: OFF', self)
    self.btn_auto_incr.setIcon(self.ico_auto_incr_off)
    self.btn_auto_incr.setCheckable(True)
    self.btn_auto_incr.setChecked(False)
    self.btn_auto_incr.clicked.connect(self.onAutoIncrChanged)
    self.layout.addWidget(self.btn_auto_incr, 1, 3)

    self.txt_type = QLineEdit(self)
    self.txt_type.setMaxLength(2)
    self.txt_type.setPlaceholderText('Type')
    self.txt_type.editingFinished.connect(self.fetchName)
    self.layout.addWidget(self.txt_type, 2, 0)

    self.txt_id = QLineEdit(self)
    self.txt_id.setMaxLength(3)
    self.txt_id.setPlaceholderText('ID')
    self.txt_id.editingFinished.connect(self.fetchName)
    self.layout.addWidget(self.txt_id, 2, 1)

    self.txt_amount = QLineEdit(self)
    self.txt_amount.setMaxLength(3)
    self.txt_amount.setPlaceholderText('Amount')
    self.layout.addWidget(self.txt_amount, 2, 2)

    self.btn_poke = QPushButton(' Poke Memory', self)
    self.btn_poke.setIcon(QIcon('img/flaticon/draw39.png'))
    self.btn_poke.clicked.connect(self.onPokeWord)
    self.layout.addWidget(self.btn_poke, 2, 3)

    self.lbl_name = QLabel('Name: [NOT IN DB]', self)
    self.layout.addWidget(self.lbl_name, 3, 0, 1, 2)

    self.txt_new_name = QLineEdit(self)
    self.txt_new_name.setPlaceholderText('Add/Modify Item Name')
    self.txt_new_name.returnPressed.connect(self.updateName)
    self.layout.addWidget(self.txt_new_name, 3, 2, 1, 2)

    self.txt_db = QPlainTextEdit(self)
    self.txt_db.setReadOnly(True)
    font = QFont('Monospace')
    font.setStyleHint(QFont.TypeWriter)
    self.txt_db.setFont(font)
    self.layout.addWidget(self.txt_db, 4, 0, 1, 4)

    self.layout.setColumnStretch(0, 1)
    self.layout.setColumnStretch(1, 1)
    self.layout.setColumnStretch(2, 1)
    self.layout.setColumnStretch(3, 1)
    self.layout.setSpacing(5)
    # self.layout.setContentsMargins(2, 2, 2, 2)

    self.setStyleSheet('ItemIDWidget { background-color: white; }')

  def getAddrWord(self):
    addr_txt = self.txt_addr.text()
    addr_word = None
    try:
      if len(addr_txt) == 8:
        addr_word = int(str(addr_txt), 16)
      elif len(addr_txt) == 10 and addr_txt[:2] == '0x':
        addr_word = int(str(addr_txt[2:]), 16)
      else:
        addr_word = None
    except ValueError, e:
      addr_word = None
    return addr_word

  @pyqtSlot()
  def loadDB(self):
    # Get DB path
    path = QFileDialog.getOpenFileName(self, 'Load Custom DB', QDir.currentPath() + '/codes', '*.txt')
    if len(path) <= 0:
      return
    pwd = QDir(QDir.currentPath())
    rel_path = pwd.relativeFilePath(path)
    if len(rel_path) > 2 and rel_path[:2] != '..':
      path = rel_path

    try:
      with open(str(path), 'r') as f:
        db_txt = f.read()
        self.custom_db, self.custom_db_lines, self.item_types = parse_item_db(db_txt)
      self.txt_db.setPlainText('\n'.join(self.custom_db_lines))
      self.lbl_path_db.setText(path)
      self.log.emit('Loaded custom Item ID DB', 'black')
    except SyntaxError, e:
      self.log.emit(str(e), 'red')
    except IOError, e:
      self.log.emit('Failed to load Item ID DB: ' + str(e), 'red')
    except BaseException, e:
      self.log.emit('Failed to load Item ID DB: ' + str(e), 'red')
      traceback.print_exc()

  @pyqtSlot()
  def saveDB(self):
    path = self.lbl_path_db.text()
    if path == 'DB not loaded':
      path = QDir.currentPath() + '/codes/item_id.txt'
    path = QFileDialog.getSaveFileName(self, 'Save Custom DB', path, '*.txt')
    if len(path) > 0:
      try:
        with open(str(path), 'w') as f:
          f.write('\n'.join(self.custom_db_lines))
        self.log.emit('Saved custom Item ID DB', 'black')
      except IOError, e:
        self.log.emit('Failed to save Item ID DB: ' + str(e), 'red')
      except BaseException, e:
        self.log.emit('Failed to save Item ID DB: ' + str(e), 'red')
        traceback.print_exc()

  @pyqtSlot()
  def fetchName(self):
    val_word = None
    try:
      type_txt = self.txt_type.text()
      id_txt = self.txt_id.text()
      if len(type_txt) <= 0 or len(id_txt) <= 0:
        return
      type_val = int(str(type_txt), 16)
      id_val = int(str(id_txt), 16)
      val_word = form_item_word(type_val, id_val, 0)
    except ValueError, e:
      traceback.print_exc()

    if val_word is not None:
      if val_word in self.custom_db:
        self.lbl_name.setText('Name: ' + self.custom_db[val_word].name)
        self.txt_new_name.setText(self.custom_db[val_word].name)
      else:
        self.lbl_name.setText('Name: [NOT IN DB]')

  @pyqtSlot()
  def updateName(self):
    # Parse fields
    name = self.txt_new_name.text()
    type_val = None
    id_val = None
    val_word = None
    try:
      type_val = int(str(self.txt_type.text()), 16)
      id_val = int(str(self.txt_id.text()), 16)
      val_word = form_item_word(type_val, id_val, 0)
    except ValueError, e:
      self.log.emit('Failed to fetch ID/Type/Name', 'red')
    except BaseException, e:
      self.log.emit('Failed to fetch ID/Type/Name: ' + str(e), 'red')
      traceback.print_exc()

    # Update name
    if len(name) > 0 and val_word is not None:
      if val_word in self.custom_db:
        item = self.custom_db[val_word]
        item.name = name
        self.custom_db_lines[item.line] = '%02X %03X %s' % (type_val, id_val, name)
      else:
        self.custom_db[val_word] = Item(type_val, id_val, name, len(self.custom_db_lines))
        self.custom_db_lines.append('%02X %03X %s' % (type_val, id_val, name))

    # Update display
    self.txt_db.setPlainText('\n'.join(self.custom_db_lines))
    scrollbar = self.txt_db.verticalScrollBar()
    scrollbar.setValue(scrollbar.maximum())

    # Automatically increment ID and poke
    if self.btn_auto_incr.isChecked():
      id_val += 1
      if id_val <= Item.MAX_ID_VAL:
        self.txt_id.setText('%03X' % id_val)
        self.txt_new_name.setText('')
        self.onPokeWord()

  @pyqtSlot(bool)
  def onAutoIncrChanged(self, checked):
    if checked:
      self.btn_auto_incr.setText(' Auto Increment: ON')
      self.btn_auto_incr.setIcon(self.ico_auto_incr_on)
    else:
      self.btn_auto_incr.setText(' Auto Increment: OFF')
      self.btn_auto_incr.setIcon(self.ico_auto_incr_off)

  @pyqtSlot()
  def onReadWord(self):
    addr_word = self.getAddrWord()
    if addr_word is None:
      self.log.emit('Failed to parse address: invalid address, expecting XXXXXXXX', 'red')
      return
    self.read_block.emit(addr_word, 4)

  @pyqtSlot(int, int, QByteArray)
  def onBlockRead(self, addr_start, num_bytes, raw_qbytes):
    addr_word = self.getAddrWord()
    if addr_word is None or addr_word != addr_start or num_bytes != 4:
      return
    word_val = struct.unpack('>I', str(raw_qbytes))[0]
    (type_val, id_val, amount) = parse_item_word(word_val)
    self.txt_type.setText('%02X' % type_val)
    self.txt_id.setText('%03X' % id_val)
    self.txt_amount.setText('%d' % amount)
    self.fetchName()

  @pyqtSlot()
  def onPokeWord(self):
    addr_word = self.getAddrWord()
    if addr_word is None:
      self.log.emit('Failed to parse address: invalid address, expecting XXXXXXXX', 'red')
      return

    try:
      type_val = int(str(self.txt_type.text()), 16)
      id_val = int(str(self.txt_id.text()), 16)
      amount = int(str(self.txt_amount.text()))
      if amount < 0 or amount > 99:
        self.log.emit('Amount not in [0, 99] range', 'red')
        return
      val_word = form_item_word(type_val, id_val, amount)
    except ValueError, e:
      self.log.emit('Failed to parse ID/Type/Name', 'red')
      return

    raw_bytes = struct.pack('>I', val_word)
    self.poke_block.emit(addr_word, QByteArray(raw_bytes), False)
    self.read_block.emit(addr_word, 4)
