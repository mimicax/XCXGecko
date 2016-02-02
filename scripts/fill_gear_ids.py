from collections import OrderedDict


def write_roman(num):
    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(n):
        for r in roman.keys():
            x, y = divmod(n, r)
            yield roman[r] * x
            n -= (r * x)
            if n > 0:
                roman_num(n)
            else:
                break

    return "".join([a for a in roman_num(num)])


data = '''
001 Max HP Up I
015 Max TP Up I
029 Melee Accuracy Up I
03D Ranged Accuracy Up I
051 Evasion Up I
065 Melee Attack Up I
079 Ranged Attack Up I
08D Potential Up I
0A1 Max HP Boost I
0B5 Max TP Boost I
0C9 Melee Accuracy Boost I
0DD Ranged Accuracy Boost I
0F1 Evasion Boost I
105 Melee Attack Boost I
119 Ranged Attack Boost I
12D Potential Boost I
141 Max HP Drive I
155 Max GP Drive I
169 Melee Accuracy Drive I
17D Ranged Accuracy Drive I
191 Evasion Drive I
1A5 Melee Attack Drive I
1B9 Ranged Attack Drive I
1CD Potential Drive I
1E1 Bind: Refuel I
1F5 Fuel Efficiency Up I
209 Physical Resistance Up I
21D Beam Resistance Up I
231 Electric Resistance Up I
245 Thermal Resistance Up I
259 Ether Resistance Up I
26D Gravity Resistance Up I
281 Weapon Attack Power Up I
295 Stabilizer I
2A9 Destabilizer I
2BD Magazine Capacity Up I
2D1 Melee: TP Gain Up
2D2 Ranged: TP Gain Up
2D3 Cooldown Reducer I
2E7 Firing Range Up I
2FB Resist Stagger I
30F Resist Flinch I
323 Resist Topple I
337 Resist Knockback I
34B Resist Launch I
35F Resist Stun I
373 Resist Sleep I
387 Resist Taunt I
39B Resist Control I
3AF Resist Virus I
3C3 Resist Blackout I
3D7 Resist Fatigue I
3EB Resist Slow Arts I
3FF Resist Physical Res Down I
413 Resist Beam Res Down I
427 Resist Thermal Res Down I
43B Resist Electric Res Down I
44F Resist Ether Res Down I
463 Resist Gravity Res Down I
477 Resist Time Bomb I
48B Resist Debuff Res Down I
49F Resist HP Recovery Down I
4B3 Resist Blaze I
4C7 Resist Shock I
4DB Debuff Suppressor I
4EF Critical Chance Up I
503 Theroid Criticals Up I
517 Insectoid Criticals Up I
52B Piscinoid Criticals Up I
53F Humanoid Criticals Up I
553 Mechanoid Criticals Up I
567 Chimeroid Criticals Up I
57B Ultrafauna Criticals Up I
58F Extend Critical Power I
5A3 Zero Critical
5A4 Theroid Slayer I
5B8 Insectoid Slayer I
5CC Piscinoid Slayer I
5E0 Humanoid Slayer I
5F4 Mechanoid Slayer I
608 Chimeroid Slayer I
61C Ultrafauna Slayer I
630 Physical Attack Plus I
644 Beam Attack Plus I
658 Ether Attack Plus I
66C Thermal Attack Plus I
680 Electric Attack Plus I
694 Gravity Attack Plus I
6A8 Front Attack Plus I
6BC Side Attack Plus I
6D0 Back Attack Plus I
6E4 Vantage Attack Plus I
6F8 Melee: Blackout I
70C Melee: Fatigue I
720 Melee: Physical Res Down I
734 Melee: Beam Res Down I
748 Melee: Ether Res Down I
75C Melee: Thermal Res Down I
770 Melee: Electric Res Down I
784 Melee: Gravity Res Down I
798 Melee: Blaze I
7AC Melee: Shock I
7C0 Melee: Recover HP I
7D4 Soft Touch I
7E8 HP Rebound I
7FC TP Rebound I
810 Taunt: Barrier I
824 Taunt: Decoy I
838 Taunt: Supercharge I
84C Topple: Barrier I
860 Topple: Decoy I
874 Stun: Barrier I
888 Stun: Decoy I
89C Reflect Physical
89D Reflect Beam
89E Reflect Ether
89F Reflect Thermal
8A0 Reflect Electric
8A1 Reflect Gravity
8A2 Reflect Damage Up I
8B6 Nullify Physical Reflect I
8CA Nullify Beam Reflect I
8DE Nullify Ether Reflect I
8F2 Nullify Thermal Reflect I
906 Nullify Electric Reflect I
91A Nullify Gravity Reflect I
92E Overdrive: Recover HP I
942 Overdrive: Gain TP I
956 Overdrive: Count Up I
96A Extend OverDrive I
97E Overdrive Blue Bonus
97F Overdrive Green Bonus
980 Extend Aura I
994 Aura Rapid Cooldown I
9A8 Aura: Refuel I
9BC Arts: Gain TP I
9D0 Arts: Recover HP I
9E4 Secondary CD Reducer I
9F8 Extend Taunt I
A0C Extend Control I
A20 Extend Virus I
A34 Extend Blackout I
A48 Extend Fatigue I
A5C Extend Slow Arts I
A70 Extend Debuff Res Down I
# A84 DEBUG
A98 Extend Blaze I
AAC Extend Shock I
AC0 Extended Phys Res Down I
AD4 Extended Beam Res Down I
AE8 Extend Ether Res Down I
AFC Extend Thermal Res Down I
B10 Extend Electric Res Down I
B24 Extend Gravity Res Down I
# B38 DEBUG
B4C Opening Act: Damage Up I
# B60-C14 DEBUG
C28 Melee Draw Surge I
C3C Ranged Draw Surge I
C50 Art Draw Surge I
C64 Danger Surge I
C78 High Danger Surge I
C8C Incapacitation Surge I
CA0 Critical Surge I
CB4 Crush Surge I
CC8 Underdog Surge I
CDC Artful Execution Surge I
CF0 Aura Surge I
D04 Overdrive Surge I
D18 Reinvigorate I
D2C EXP Boost I
D40 Visual Cloaking I
D54 Aural Cloaking I
D68 Appendage Crusher
D69 Crush: Gain TP I
D7D Ranged Appendage Damage I
D91 Terrain Damage Reducer I
DA5 Antispike I
DB9 Resistance Reducer I
DCD Treasure Sensor I
DE1 Untouchable Dash I
# DF5 DEBUG
E09 Night Vision I
E1D Focused Evasion I
E31 Fog Screen
E32 Rain Screen
E33 Lightning Screen
E34 Heavy Rain Screen
E35 Heat Wave Screen
E36 Sandstorm Screen
E37 Thunderstorm Screen
E38 EM Storm Screen
E39 Energy Mist Screen
E3A Rising Energy Mist Screen
E3B Brimstone Rain Screen
E3C Aurora Screen
E3D Crimson Aurora Screen
E3E Spore Screen
E3F Meteor Shower Screen
E40 Weather Master I
# E55-E5E EMPTY
'''

data = '''
001 SpecUp.HP-MAX I
015 SpecUp.GP-MAX I
029 SpecUp.M-ACC I
03D SpecUp.R-ACC I
051 SpecUp.EVA I
065 SpecUp.M-ATK I
079 SpecUp.R-ATK I
08D SpecUp.FTL I
0A1 SpecUp.APP-HP I
0B5 Boost.HP-MAX I
0C9 Boost.GP-MAX I
0DD Boost.M-ACC I
0F1 Boost.R-ACC I
105 Boost.EVA I
119 Boost.M-ATK I
12D Boost.R-ATK I
141 Boost.PTL I
155 Generator Boost I
158 SpecUp.PHYS-RES I
16C SpecUp.BEAM-RES I
180 SpecUp.ELEC-RES I
194 SpecUp.THERM-RES I
1A8 SpecUp.ETHER-RES I
1BC SpecUp.GRAV-RES I
1D0 SpecUp.FUEL-MAX I
1E4 SpecUp.FUEL-COST I
1F8 SpecUp.FUEL-PARK I
20C SpecUp.FUEL-BIND I
220 SpecUp.FUEL-OD I
234 Custom.WP-ATK I
248 Custom.WP-STABLE I
25C Custom.WP-DESTABLE I
270 Custom.WP-RFL-MAG I
284 Custom.WP-MSL-MAG I
298 Custom WP.M-GP
# 299-29D DUPLICATES
29E Custom.WP-R-GP
# 29F-2A3 DUPLICATES
2A4 Custom.WP-SPEED I
2B8 Custom.WP-R-RANGE I
2CC Custom.WP-FUEL I
2E0 Resist.STAGGER I
2F4 Resist.FLINCH I
308 Resist.TOPPLE I
31C Resist.KNOCKBACK I
330 Resist.LAUNCH I
344 Resist.STUN I
358 Resist.SLEEP I
36C Resist.TAUNT I
380 Resist.CONTROL I
394 Resist.VIRUS I
3A8 Resist.BLACKOUT I
3BC Resist.FATIGUE I
3D0 Resist.SLOW-ARTS I
3E4 Resist.PHYS-DOWN I
3F8 Resist.BEAM-DOWN I
40C Resist.THERM-DOWN I
420 Resist.ELEC-DOWN I
434 Resist.ETHER-DOWN I
448 Resist.GRAV-DOWN I
45C Resist.TIME-BOMB I
470 Resist.DEBUFF-DOWN I
484 Resist.RECOV-DOWN I
498 Resist.BLAZE I
4AC Resist.SHOCK I
4C0 CutTime.DEBUFF I
4D4 CriticalUp I
4E8 CritUp.THEROID I
4FC CritUp.INSECTOID I
510 CritUp.PISCINOID I
524 CritUp.HUMANOID I
538 CritUp.MECHANOID I
54C CritUp.CHIMEROID I
560 CritUp.ULTRAFAUNA I
574 ExTime.CRIT-FLOW I
588 Slayer.THEROID I
59C Slayer.INSECTOID I
5B0 Slayer.PISCINOID I
5C4 Slayer.HUMANOID I
5D8 Slayer.MECHANOID I
5EC Slayer.CHIMEROID I
600 Slayer.ULTRAFAUNA I
614 AttributeDmg.PHYS I
628 AttributeDmg.BEAM I
63C AttributeDmg.ETHER I
650 AttributeDmg.THERM I
664 AttributeDmg.ELEC I
678 AttributeDmg.GRAV I
68C PositionDmg.FRONT I
6A0 PositionDmg.SIDE I
6B4 PositionDmg.BACK I
6C8 PositionDmg.ABOVE I
6DC M-Auto.BLACKOUT I
6F0 M-Auto.FATIGUE I
704 M-Auto.PHYS-DOWN I
718 M-Auto.BEAM-DOWN I
72C M-Auto.ETHER-DOWN I
740 M-Auto.THERM-DOWN I
754 M-Auto.ELEC-DOWN I
768 M-Auto.GRAV-DOWN I
77C M-Auto.BLAZE I
790 M-Auto.SHOCK I
7A4 M-Auto.HP-RECOV I
7B8 Damage.GP-GAIN I
7CC Damage.APPEND I
7E0 Jamming I
7F4 AppendLost.ATK-UP I
808 AppendLost.EVA-UP I
81C AppendLost.GP I
830 Reflect ADD-PHYS
831 Reflect ADD-BEAM
832 Reflect ADD-ETHER
833 Reflect ADD-THERM
834 Reflect ADD-ELEC
835 Reflect ADD-GRAV
836 Reflect DAMAGE-UP I
84A Reflect.NEG-PHYS I
85E Reflect.NEG-BEAM I
872 Reflect.NEG-ETHER I
886 Reflect.NEG-THERM I
89A Reflect.NEG-ELEC I
8AE Reflect.NEG-GRAV I
8C2 Overdrive.FRAME-HP I
8D6 Overdrive.APPEND-HP I
8EA Overdrive.EXTEND I
8FE Arts.GP I
912 TimeEx.TAUNT I
926 TimeEx.CONTROL I
93A TimeEx.SLEEP I
94E TimeEx.VIRUS I
962 TimeEx.BLACKOUT I
976 TimeEx.FATIGUE I
98A TimeEx.SLOW-ARTS I
99E TimeEx.DEBUFF-DOWN I
9B2 TimeEx.RECOV-DOWN I
9C6 TimeEx.BLAZE I
9DA TimeEx.SHOCK I
9EE TimeEx.PHYS-DOWN I
A02 TimeEx.BEAM-DOWN I
A16 TimeEx.ETHER-DOWN I
A2A TimeEx.THERM-DOWN I
A3E TimeEx.ELEC-DOWN I
A52 TimeEx.GRAV-DOWN I
# A66-A79 ITM_SKL_DL_FST_TP01_ - 20
A7A Draw.OPENING-DMG I
# A8E-A96 ITM_SKLO_DL_FST_CRTC0
# A97-AA0 ITM_SKLO_DL_FST_CRTC1
# AA1 ITM_SKLO_DL_FST_CRTC2
# AA2-AB5 ITM_SKL_DL_FST_FDEX01_name - 20
# AB6-AC9 ITM_SKL_DL_FST_SDEX01_name - 20
# ACA-ADD ITM_SKL_DL_FST_EVA01_name - 20
# ADE-AF1 ITM_SKL_DL_FST_FPOW01_name - 20
# AF2-B06 ITM_SKL_DL_FST_SPOW01_name - 20
# B07-B19 ITM_SKL_DL_FST_MIND01_name - 20
# ...
'''

prev_addr = 0
incr_name = None
incr_level = None
for line in data.split('\n'):
  if len(line.strip()) <= 0 or line[0] == '#':
    print line
    continue

  tokens = line.split(' ', 1)
  if len(tokens) < 2:
    raise ValueError('Invalid number of tokens: ' + line)
  cur_addr = int(tokens[0], 16)
  cur_name = tokens[1]
  if cur_addr <= prev_addr:
    raise ValueError('Overlapping addresses: %03X, %03X' % (cur_addr, prev_addr))
  if len(cur_name.strip()) <= 2:
    raise ValueError('Invalid name: ' + cur_name)

  if incr_name is not None:
    incr_addr = prev_addr + incr_level - 1
    while incr_level <= 20 and incr_addr < cur_addr:
      print '%03X %s %s' % (incr_addr, incr_name, write_roman(incr_level))
      incr_level += 1
      incr_addr = prev_addr + incr_level - 1
    # if incr_level != 21:
    #   raise BaseException('Non-20-incr level: ' + line)

  if cur_name[-2:] == ' I':
    print line
    incr_name = cur_name[:-2]
    incr_level = 2
  else:
    print line
    incr_name = None
    incr_level = None
  prev_addr = cur_addr
