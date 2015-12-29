import sys, os
sys.path.append(os.path.abspath('../pygecko'))
from tcpgecko import *

wiiu_addr = '192.168.0.133'
print '> Connecting to Wii U...'
g = TCPGecko(wiiu_addr)
print '> Connected to Wii U'

base_addr = 0x1C3AC718
skill_12_addr = base_addr+12
skill_3_addr = base_addr+16

skill_names = []
incr_by_one = True
base_id = 0xD69+20
base_id = 0xE4F+1
for i in range(5):
  if incr_by_one:
    skill_1_id = base_id
    skill_2_id = base_id+1
    skill_3_id = base_id+2
    base_id += 3
  else:
    skill_1_id = base_id
    skill_2_id = base_id+20
    skill_3_id = base_id+40
    base_id += 60

  if skill_1_id > 0xFFF or skill_2_id > 0xFFF or skill_3_id > 0xFFF:
    break
  skill_12_word = (skill_1_id << 20) + (skill_2_id << 4)
  skill_3_word = (skill_3_id << 20) + 0x0000
  # print '> POKE %08X %08X' % (skill_12_addr, skill_12_word)
  g.pokemem(skill_12_addr, skill_12_word)
  # print '> POKE %08X %08X' % (skill_3_addr, skill_3_word)
  g.pokemem(skill_3_addr, skill_3_word)
  skill_1_name = raw_input('%03X ' % skill_1_id)
  skill_2_name = raw_input('%03X ' % skill_2_id)
  skill_3_name = raw_input('%03X ' % skill_3_id)
  skill_1_str = '%03X %s' % (skill_1_id, skill_1_name)
  skill_2_str = '%03X %s' % (skill_2_id, skill_2_name)
  skill_3_str = '%03X %s' % (skill_3_id, skill_3_name)
  skill_names.append(skill_1_str)
  skill_names.append(skill_2_str)
  skill_names.append(skill_3_str)

g.s.close()
print '> Disconnected from Wii U'
