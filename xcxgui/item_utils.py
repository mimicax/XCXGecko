import traceback


class Item:
  MAX_ID_VAL = 0x3FF # NOTE: also used as bit mask!

  '''
  WARNING: poking an illegal/large ID will cause XCX to crash back to title screen

  Item Value Word Structure:
  0    0    1    3     8    3    1    8
  uuui iiii iiii ittt  tyyy yaaa aaaa afff

  u: unknown
  i: ID
  t: type
  y: type2/unknown
  a: amount
  f: flags/unknown
  '''

  def __init__(self, type_val, id_val, name, line=-1):
    self.type_val = type_val
    self.id_val = id_val
    self.name = name
    self.val_word = form_item_word(type_val, id_val, 0)
    self.line = line

  def __str__(self):
    msg = 'l%d t%02X i%03X v%08X %s' % (self.line, self.type_val, self.id_val, self.val_word, self.name)
    return msg


def form_item_word(type_val, id_val, amount):
  type_val &= 0xFF
  id_val &= Item.MAX_ID_VAL
  amount &= 0xFF
  val_word = (id_val << 19) | (type_val << 11) | (amount << 3)
  return val_word


def parse_item_word(val_word):
  type_val = (val_word >> 11) & 0xFF
  id_val = (val_word >> 19) & Item.MAX_ID_VAL
  amount = (val_word >> 3) & 0xFF
  return type_val, id_val, amount


def parse_item_db(db_txt):
  db_lines = db_txt.split('\n')
  item_types = []
  db = dict()

  line_count = 0
  try:
    for line in db_lines:
      line_count += 1

      if len(line) <= 0: # Skip empty lines
        continue

      elif len(line) > 4 and line[:4] == '### ': # Parse TYPE_VAL TYPE_NAME
        type_tokens = line.split(None, 2)
        if len(type_tokens) != 3:
          continue
        try:
          type_val = int(type_tokens[1], 16)
          if type_val < 0 or type_val > 0xFF:
            continue
          type_name = type_tokens[2]
          item_types.append((type_val, type_name))
        except ValueError, e:
          continue

      elif line[0] == '#': # Skip commented lines
        continue

      else: # Parse TYPE_VAL ID_VAL NAME
        tokens = line.split(None, 2)
        if len(tokens) != 3:
          raise SyntaxError('invalid line format, expecting TYPE_VAL ID_VAL NAME')
        type_val = int(tokens[0], 16)
        id_val = int(tokens[1], 16)
        if type_val < 0 or type_val > 0xFF:
          raise ValueError('TYPE_VAL out of [%d, %d] range' % (0, 0xFF))
        if id_val < 0 or id_val > Item.MAX_ID_VAL:
          raise ValueError('ID_VAL out of [%d, %d] range' % (0, Item.MAX_ID_VAL))
        name = tokens[2]
        item = Item(type_val, id_val, name, line_count-1)
        if item.val_word in db:
          raise ValueError('duplicate entry for TYPE=%02X ID=%03X' % (type_val, id_val))
        db[item.val_word] = item

  except (ValueError, SyntaxError), e:
    raise SyntaxError('Failed to parse Item ID DB on line %d: %s' % (line_count, str(e)))
  except BaseException, e:
    traceback.print_exc()
    raise SyntaxError('Failed to parse Item ID DB on line %d: %s' % (line_count, str(e)))

  return db, db_lines, item_types
