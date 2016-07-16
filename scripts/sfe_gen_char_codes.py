chars = '''Itsuki
Tsubasa
Touma
Kiria
Eleonora
Mamori
Yashiro'''
itsuki_exp_addr = 0x49AE6120

traits_raw = '''HP: -58 0000270F
Max HP: -54 0000270F
EP: -50 0000270F
Max EP: -4C 0000270F
Str: -3A 03E7
Mag: -38 03E7
Skl: -36 03E7
Spd: -34 03E7
Def: -32 03E7
Res: -30 03E7
Lck: -2E 0005
Resistance Sword: -2C 0009
Resistance Lance: -2A 0009
Resistance Axe: -28 0009
Resistance Bow: -26 0009
Resistance Fire: -24 0009
Resistance Ice: -22 0009
Resistance Elec: -20 0009
Resistance Force: -1E 0009
Resistance Mind: -1C 0009
Resistance Body: -1A 0009
Stage Rank Exp: -4 00000500
Exp: 0 0013BD20
'''
# TODO: scan for more char codes


traits = []
for line in traits_raw.splitlines():
  colon_idx = line.find(':')
  space_idx = line.find(' ', colon_idx+2)
  label = line[:colon_idx]
  incr = int(line[colon_idx+2:space_idx], 16)
  value = line[space_idx+1:]
  traits.append((label, incr, value))
  # print '> %s: +0x%08X %s' % (label, incr, value)


names = chars.splitlines()
for i in xrange(len(names)):
  name = names[i]
  addr = itsuki_exp_addr + i*0x360

  for (trait, incr, value) in traits:
    print '%s %s\n%08X %s\n' % (name, trait, addr+incr, value)

  print '\n'
