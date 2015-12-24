import string
import traceback

from PyQt4.QtCore import QDir
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QFileDialog
from PyQt4.QtGui import QGridLayout
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPlainTextEdit
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QWidget

'''
Item Value Word Structure:
0    0    1    3     8    3    1    8
uuuu uiii iiii ittt  tyyy yaaa aaaa afff

u: unknown
i: ID
t: type
y: type2/unknown
a: amount
f: flags/unknown
'''


def form_item_word(type_byte, id_byte, amount_byte):
  val_word = (id_byte << 19) | (type_byte << 11) | (amount_byte << 3)
  return val_word


def parse_item_word(val_word):
  type_byte = (val_word >> 11) & 0xFF
  id_byte = (val_word >> 19) & 0xFF
  amount_byte = (val_word >> 3) & 0xFF
  return type_byte, id_byte, amount_byte


class Item:
  def __init__(self, type_byte, id_byte, name, line=-1):
    self.type_byte = type_byte
    self.id_byte = id_byte
    self.name = name
    self.val_word = form_item_word(type_byte, id_byte, 0)
    self.line = line


class ItemIDWidget(QWidget):
  read = pyqtSignal(str)  # code_label
  poke = pyqtSignal(str, int)  # code_label, new_val
  word_read = pyqtSignal(str, int)  # txt_addr, word_val
  log = pyqtSignal(str, str)  # msg, color

  def __init__(self, parent=None):
    super(ItemIDWidget, self).__init__(parent)
    self.db = dict()
    self.db_lines = []

    self.layout = QGridLayout(self)

    self.lbl_path_db = QLabel('Load Item ID DB first', self)
    self.layout.addWidget(self.lbl_path_db, 0, 0, 1, 2)
    self.btn_load_db = QPushButton('Load DB', self)
    self.btn_load_db.clicked.connect(self.loadDB)
    self.layout.addWidget(self.btn_load_db, 0, 2)
    self.btn_save_db = QPushButton('Save DB', self)
    self.btn_save_db.clicked.connect(self.saveDB)
    self.layout.addWidget(self.btn_save_db, 0, 3)

    self.txt_addr = QLineEdit(self)
    self.txt_addr.setPlaceholderText('Memory Address')
    self.layout.addWidget(self.txt_addr, 1, 0)
    self.btn_curval = QPushButton('Fetch Value', self)
    self.btn_curval.clicked.connect(self.onReadVal)
    self.layout.addWidget(self.btn_curval, 1, 1)
    self.btn_auto_incr = QPushButton('Auto Increment: OFF', self)
    self.btn_auto_incr.setCheckable(True)
    self.btn_auto_incr.setChecked(False)
    self.btn_auto_incr.clicked.connect(self.onAutoIncrChanged)
    self.layout.addWidget(self.btn_auto_incr, 1, 2)
    self.txt_type = QLineEdit(self)
    self.txt_type.setPlaceholderText('Type')
    self.txt_type.editingFinished.connect(self.fetchName)
    self.layout.addWidget(self.txt_type, 2, 0)
    self.txt_id = QLineEdit(self)
    self.txt_id.setPlaceholderText('ID')
    self.txt_id.editingFinished.connect(self.fetchName)
    self.layout.addWidget(self.txt_id, 2, 1)
    self.txt_amount = QLineEdit(self)
    self.txt_amount.setPlaceholderText('Amount')
    self.layout.addWidget(self.txt_amount, 2, 2)
    self.btn_poke = QPushButton('Poke', self)
    self.btn_poke.clicked.connect(self.onPokeVal)
    self.layout.addWidget(self.btn_poke, 2, 3)
    self.lbl_name = QLabel('Name: [NOT IN DB]', self)
    self.layout.addWidget(self.lbl_name, 3, 0, 1, 2)
    self.txt_new_name = QLineEdit(self)
    self.txt_new_name.setPlaceholderText('Add/Modify Item Name')
    self.txt_new_name.returnPressed.connect(self.updateName)
    self.layout.addWidget(self.txt_new_name, 3, 2, 1, 2)

    self.txt_db = QPlainTextEdit(self)
    self.txt_db.setReadOnly(True)
    self.layout.addWidget(self.txt_db, 4, 0, 1, 4)

    self.layout.setColumnStretch(0, 1)
    self.layout.setColumnStretch(1, 1)
    self.layout.setColumnStretch(2, 1)
    self.layout.setColumnStretch(3, 1)

    self.setStyleSheet('ItemIDWidget { background-color: white; }')
    self.show()

  def parseDBTxt(self, db_txt):
    line_count = 0
    try:
      self.db = dict()
      self.db_lines = db_txt.split('\n')
      for line in self.db_lines:
        line_count += 1
        if len(line) <= 0 or line[0] == '#':
          continue
        tokens = string.split(line, maxsplit=2)
        if len(tokens) != 3:
          raise BaseException('invalid line format, expecting TYPE_BYTE ID_BYTE NAME')
        elif len(tokens[0]) != 2:
          raise BaseException('invalid TYPE_BYTE, expecting XX')
        elif len(tokens[1]) != 2:
          raise BaseException('invalid ID_BYTE, expecting XX')
        type_byte = int(tokens[0], 16)
        id_byte = int(tokens[1], 16)
        name = tokens[2]
        item = Item(type_byte, id_byte, name, line_count-1)
        if item.val_word in self.db:
          raise BaseException('duplicate entry for TYPE=%s ID=%s' % (tokens[0], tokens[1]))
        self.db[item.val_word] = item
        # print 'Parsed %08X (type=%02X id=%02X): %s' % (item.val_word, item.type_byte, item.id_byte, item.name)

    except BaseException, e:
      self.log.emit('Failed to parse Item ID DB on line %d: %s' % (line_count, str(e)), 'red')
      traceback.print_exc()

  @pyqtSlot()
  def loadDB(self):
    # Get DB path
    path = QFileDialog.getOpenFileName(self, 'Load DB', QDir.currentPath() + '/codes', '*.txt')
    if len(path) <= 0:
      return
    pwd = QDir(QDir.currentPath())
    rel_path = pwd.relativeFilePath(path)
    if len(rel_path) > 2 and rel_path[:2] != '..':
      path = rel_path

    try:
      with open(str(path), 'r') as f:
        self.parseDBTxt(f.read())
      self.txt_db.setPlainText('\n'.join(self.db_lines))
      self.lbl_path_db.setText(path)
      self.log.emit('Loaded Item ID DB', 'black')
    except BaseException, e:
      self.log.emit('Failed to load Item ID DB: ' + str(e), 'red')
      traceback.print_exc()

  @pyqtSlot()
  def saveDB(self):
    path = QFileDialog.getSaveFileName(self, 'Save DB', self.lbl_path_db.text(), '*.txt')
    if len(path) > 0:
      try:
        with open(str(path), 'w') as f:
          f.write('\n'.join(self.db_lines))
        self.log.emit('Saved Item ID DB', 'black')
      except BaseException, e:
        self.log.emit('Failed to save Item ID DB: ' + str(e), 'red')
        traceback.print_exc()

  def fetchName(self):
    val_word = None
    try:
      type_txt = self.txt_type.text()
      id_txt = self.txt_id.text()
      type_byte = int(str(type_txt), 16)
      id_byte = int(str(id_txt), 16)
      if 0 <= type_byte <= 0xFF and 0 <= id_byte <= 0xFF:
        val_word = form_item_word(type_byte, id_byte, 0)
    except BaseException, e:
      traceback.print_exc()

    if val_word is not None:
      if val_word in self.db:
        self.lbl_name.setText('Name: ' + self.db[val_word].name)
        self.txt_new_name.setText(self.db[val_word].name)
      else:
        self.lbl_name.setText('Name: [NOT IN DB]')

  @pyqtSlot()
  def updateName(self):
    # Parse fields
    name = self.txt_new_name.text()
    type_byte = None
    id_byte = None
    val_word = None
    try:
      type_byte = int(str(self.txt_type.text()), 16)
      id_byte = int(str(self.txt_id.text()), 16)
      val_word = form_item_word(type_byte, id_byte, 0)
    except BaseException, e:
      self.log.emit('Failed to fetch ID/Type/Name', 'red')
      traceback.print_exc()

    # Update name
    if len(name) > 0 and val_word is not None:
      if val_word in self.db:
        item = self.db[val_word]
        item.name = name
        self.db_lines[item.line] = '%02X %02X %s' % (type_byte, id_byte, name)
      else:
        self.db[val_word] = Item(type_byte, id_byte, name, len(self.db_lines))
        self.db_lines.append('%02X %02X %s' % (type_byte, id_byte, name))

    # Update display
    self.txt_db.setPlainText('\n'.join(self.db_lines))

    # Automatically increment ID and poke
    if self.btn_auto_incr.isChecked():
      id_byte += 1
      if id_byte <= 255:
        self.txt_id.setText('%02X' % id_byte)
        self.txt_new_name.setText('')
        self.onPokeVal()

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
    except BaseException, e:
      addr_word = None
    return addr_word

  @pyqtSlot(bool)
  def onAutoIncrChanged(self, checked):
    if checked:
      self.btn_auto_incr.setText('Auto Increment: ON')
    else:
      self.btn_auto_incr.setText('Auto Increment: OFF')

  @pyqtSlot(str, int)
  def onWordRead(self, txt_addr, word_val):
    addr_word = self.getAddrWord()
    if addr_word is None:
      return

    cur_addr = '%08X' % addr_word
    if txt_addr != cur_addr:
      # print 'ItemIDWidget.onWordRead(%s != %s)' % (txt_addr, cur_addr)
      return

    (type_byte, id_byte, amount_byte) = parse_item_word(word_val)
    self.txt_type.setText('%02X' % type_byte)
    self.txt_id.setText('%02X' % id_byte)
    self.txt_amount.setText('%d' % amount_byte)
    self.fetchName()

  @pyqtSlot()
  def onReadVal(self):
    addr_word = self.getAddrWord()
    if addr_word is None:
      self.log.emit('Failed to parse address: invalid address, expecting XXXXXXXX', 'red')
      return

    self.read.emit('%08X' % addr_word)

  @pyqtSlot()
  def onPokeVal(self):
    addr_word = self.getAddrWord()
    if addr_word is None:
      self.log.emit('Failed to parse address: invalid address, expecting XXXXXXXX', 'red')
      return

    val_word = None
    try:
      type_byte = int(str(self.txt_type.text()), 16)
      id_byte = int(str(self.txt_id.text()), 16)
      amount_byte = int(str(self.txt_amount.text()))
      if amount_byte < 0 or amount_byte > 0xFF:
        self.log.emit('Amount out of [0, 255] range', 'red')
        return
      val_word = form_item_word(type_byte, id_byte, amount_byte)
    except BaseException, e:
      self.log.emit('Failed to fetch ID/Type/Name', 'red')
      traceback.print_exc()
      return

    if addr_word is not None and val_word is not None:
      addr = '%08X' % addr_word
      self.poke.emit(addr, val_word)
      self.read.emit(addr)
