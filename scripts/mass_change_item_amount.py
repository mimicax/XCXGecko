import sys, os
import struct
sys.path.append(os.path.abspath('../pygecko'))
from tcpgecko import TCPGecko
sys.path.append(os.path.abspath('../xcxgui'))
from item_utils import *

# MODIFY BELOW
wiiu_addr = '192.168.0.133'
addr_first_slot = 0x1C3BB0DC # see codes/xcx_v1.0.1e.txt for Slot 001 of Material, Rare Resources, ...
addr_last_slot = 0x1C3BD650 # ... same as above
new_amount = 99
item_type_val = 0x68 # see codes/item_id_v1.0.1e.txt for the appropriate 1-byte Type ID
slot_num_bytes = 12 # do not change

if new_amount <= 0 or new_amount > 99:
  raise ValueError('new_amount must be in [1, 99] range')

with open('../codes/item_id_v1.0.1e.txt', 'r') as f:
  (item_db, item_db_lines, item_types) = parse_item_db(f.read())

print '> Connecting to Wii U...'
g = TCPGecko(wiiu_addr)
print '> Connected to Wii U'

num_items_max = (addr_last_slot - addr_first_slot) / slot_num_bytes
num_items_found = 0
for slot_i in xrange(num_items_max):
  # Read and parse item from memory
  offset = slot_i * slot_num_bytes
  addr_curr = addr_first_slot + offset
  print '0x%08X (Slot %03d):' % (addr_curr, slot_i + 1),
  word_curr = struct.unpack('>I', g.readmem(addr_curr, 4))[0]
  type_val, id_val, amount = parse_item_word(word_curr)
  if type_val == 0:
    print 'EMPTY'
    continue
  elif type_val != item_type_val:
    print 'UNEXPECTED ITEM TYPE (%02X)' % type_val
    continue
  num_items_found += 1

  # Look up item in DB
  item_word_val = form_item_word(type_val, id_val, 0)
  item = None
  if item_word_val in item_db:
    item = item_db[item_word_val]

  # Print item
  if item is None:
    print '[NOT_IN_DB] TYPE=%02X ID=%03X x %d' % (type_val, id_val, amount)
  else:
    print '%s x %d' % (item.name, amount)

  # Update amount
  mod_word_val = form_item_word(type_val, id_val, new_amount)
  g.pokemem(addr_curr, mod_word_val)
  print '  -> x %d' % new_amount

g.s.close()
print '> Disconnected from Wii U'
