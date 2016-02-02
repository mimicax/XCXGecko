import struct
import traceback


def parse_gear_db(db_txt):
  db_lines = db_txt.split('\n')
  db = dict()
  db[0] = '[NO SKILL]'

  line_count = 0
  try:
    for line in db_lines:
      line_count += 1

      line = line.strip()
      if len(line) <= 0:  # Skip empty lines
        continue

      elif line[0] == '#':  # Skip commented lines
        continue

      else:  # Parse ID_VAL NAME
        tokens = line.split(None, 1)
        if len(tokens) != 2:
          raise SyntaxError('invalid line format, expecting ID_VAL NAME')
        id_val = int(tokens[0], 16)
        if id_val < 0:
          raise ValueError('ID_VAL out of range')
        name = tokens[1]

        # Interpolate for incrementable skill IDs
        if len(name) > 2 and name[-2:] == ' I':
          base_name = name[:-2]
          base_id = id_val
          for incr in xrange(20):
            id_val = base_id + incr
            name = base_name + ' %02d' % (incr + 1)
            if id_val in db:
              raise ValueError('duplicate entry for ID=%03X' % (id_val))
            db[id_val] = name
        else:
          if id_val in db:
            raise ValueError('duplicate entry for ID=%03X' % (id_val))
          db[id_val] = name

  except (ValueError, SyntaxError), e:
    raise SyntaxError('Failed to parse Gear ID DB on line %d: %s' % (line_count, str(e)))
  except BaseException, e:
    traceback.print_exc()
    raise SyntaxError('Failed to parse Gear ID DB on line %d: %s' % (line_count, str(e)))

  return db


# ===== Gear codes: partially decoded =====
# Ground/Skill Gear Format: wwwwxxxx yyyyyyyy zzzzpppq aaaabbbb cccc1111 22223333
#  w: 2-byte unknown; includes gear ID (with embedded maker + specs)
#  x: 2-byte unknown; ranged wep=0xC008/0xC009, melee wep=0xE008/0xE009
#  y: 4-byte unknown; possibly indicates item purchase / found locations; only seen \0 in last 6 bits
#  z: 2-byte unknown; only seen 0x0000
#  p: 10-bit placement index (incl upper 2 bits of 3rd byte)
#  q: 6-bit unknown; only seen 0b000000
#  a-c: gear/skell skill ID 1-3: yyyi
#     y: 12-bit (packed); skill type + base lvl (if applicable); see codes/gear_id_v1.0.1e.txt
#     i: 4-bit skill level incr (+0 to +15)
#  1-3: slot 1-3: 0xFFFF = no slot, 0x0000 = empty slot, other values = possibly augment slot ID
#
# Potential Up XX, Potential Boost XX, Treasure Sensor XX
# 0A001400 DE000000 00000000
#
# Melee Attack Up XX, Melee Accuracy Up XX, Melee Attack Boost XX
# 07801180 03C00000 00000000
def parse_gear_bytes(raw_bytes):
  gear_id_bytes = None
  index = None
  post_index = None
  skill_a_id = None
  skill_a_incr = None
  skill_b_id = None
  skill_b_incr = None
  skill_c_id = None
  skill_c_incr = None
  augment_a_id = None
  augment_b_id = None
  augment_c_id = None

  if raw_bytes is None:
    raise ValueError('Unexpected num gear bytes (expecting 24, got None')
  if len(raw_bytes) != 4 * 6:
    raise ValueError('Unexpected num gear bytes (expecting 24, got %d)' % len(raw_bytes))

  gear_id_bytes = raw_bytes[:10]

  placement_short = struct.unpack('>H', raw_bytes[10:12])[0]
  index = placement_short >> 6
  post_index = placement_short & 0b00111111

  skill_short = struct.unpack('>H', raw_bytes[12:14])[0]
  skill_a_id = skill_short >> 4
  skill_a_incr = skill_short & 0x0F

  skill_short = struct.unpack('>H', raw_bytes[14:16])[0]
  skill_b_id = skill_short >> 4
  skill_b_incr = skill_short & 0x0F

  skill_short = struct.unpack('>H', raw_bytes[16:18])[0]
  skill_c_id = skill_short >> 4
  skill_c_incr = skill_short & 0x0F

  augment_a_id = struct.unpack('>H', raw_bytes[18:20])[0]
  augment_b_id = struct.unpack('>H', raw_bytes[20:22])[0]
  augment_c_id = struct.unpack('>H', raw_bytes[22:24])[0]

  return (gear_id_bytes, index, post_index, skill_a_id, skill_a_incr, skill_b_id, skill_b_incr,
          skill_c_id, skill_c_incr, augment_a_id, augment_b_id, augment_c_id)


def form_gear_bytes(gear_id_bytes, index, post_index, skill_a_id, skill_a_incr, skill_b_id, skill_b_incr,
                    skill_c_id, skill_c_incr, augment_a_id, augment_b_id, augment_c_id):
  if len(gear_id_bytes) != 10:
    raise ValueError('Unexpected num gear_id bytes (expecting 10, got %d)' % len(gear_id_bytes))
  placement_short = (index << 6) + post_index
  skill_a_short = (skill_a_id << 4) + skill_a_incr
  skill_b_short = (skill_b_id << 4) + skill_b_incr
  skill_c_short = (skill_c_id << 4) + skill_c_incr
  try:
    gear_bytes = gear_id_bytes + struct.pack('>H', placement_short) + \
           struct.pack('>HHH', skill_a_short, skill_b_short, skill_c_short) + \
           struct.pack('>HHH', augment_a_id, augment_b_id, augment_c_id)
  except struct.error, e:
    traceback.print_exc()
    raise ValueError('Coding error')
  return gear_bytes


def is_gear_empty(raw_bytes):
  empty = True
  if len(raw_bytes) == 6*4:
    for idx in xrange(10):
      if raw_bytes[idx] != '\0':
        empty = False
        break
  return empty
