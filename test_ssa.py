"""
Tests for ssa symbol abstractions. This should also shed
some insight for newcomers to this spaghetti.
"""
import ssa
import ir

EAX = ir.register("eax:32-0")
EBX = ir.register("ebx:32-0")
ECX = ir.register("ecx:32-0")

SYMa = ssa.ssa_symbol(str(EAX.register_name), EAX.bitmin, EAX.bitmax)
SYMb = ssa.ssa_symbol(str(EBX.register_name), EBX.bitmin, EBX.bitmax)
SYMc = ssa.ssa_symbol(str(ECX.register_name), ECX.bitmin, ECX.bitmax)

TRACK = {'eax': SYMa, 'ebx': SYMb, 'ecx': SYMc}
def dump():
  global TRACK
  for name in TRACK:
    print name,'=',TRACK[name].get_values(), TRACK[name].get_states()
  print '---'

#dump()

#10:     eax = 0
SYMa.update([0], 10, 0)
#dump()

#20:     ebx = ecx + 5
new_state = ssa.translate_ops(TRACK, [ir.register_operand('ecx', ECX),'+', ir.constant_operand(5)], 20)
SYMb.update([new_state], 20, 0)

#dump()
### retroactive update is a funny way of putting it
### but thats what this assignment does since code
###   addr 15 < 20.
#15:    ebx = 4 
SYMc.update([4], 15, 0)

#dump()
#verify everything worked
works = True
if SYMc.get_values()[0] != 4:
  works = False
  print "FAILED, ecx should be 4"
  dump()
if SYMb.get_values()[0] != 9:
  works = False
  print "FAILED, ebx should be 9"
  dump()
if SYMa.get_values()[0] != 0:
  works = False
  print "FAILED, eax should be 0"
  dump()

if works:
  print "[+] Retroactive updates seem to work!"
else:
  import sys
  sys.exit(0)

#########################
#next, test expansion
#
# 1) updates to the same address should produce multiple possibilities
# 2)  multiple values in resolve_ssa should result in multiple new values



EAX = ir.register("eax:32-0")
EBX = ir.register("ebx:32-0")
ECX = ir.register("ecx:32-0")

SYMa = ssa.ssa_symbol(str(EAX.register_name), EAX.bitmin, EAX.bitmax)
SYMb = ssa.ssa_symbol(str(EBX.register_name), EBX.bitmin, EBX.bitmax)
SYMc = ssa.ssa_symbol(str(ECX.register_name), ECX.bitmin, ECX.bitmax)

TRACK = {'eax': SYMa, 'ebx': SYMb, 'ecx': SYMc}

works = True
#check 1, updates to the same address should produce multiple possibilities
#10: eax = [0, 1]
SYMa.update([0], 10, 0)
SYMa.update([1], 10, 0)

vals = SYMa.get_values()
if len(vals) != 2 or vals[0] != 0 or vals[1] != 1:
  works = False
  print "- Multiple updates to the same addr+aux failed"
  dump()


SYMa.update([1], 10, 0)
if len(SYMa.get_values()) != 2:
  works = False
  print "- Duplicate values added at same address"
  dump()

#20:  ebx = [3, 4]
SYMb.update([3,4], 20, 0)

new_state = ssa.translate_ops(TRACK, [ir.register_operand('eax',EAX),'+',ir.register_operand('ebx',EBX)], 30)
#30: ecx = eax + ebx ----->   [0+3], [0+4], [1+3], [1+4]
SYMc.update([new_state], 30, 0)
vals = SYMc.get_values()
#check 3 - done

if vals[0] != 3 or vals[1] != 4 or vals[2] != 4 or vals[3] != 5:
  print "resolve_ssa failed to expand symbols "
  dump()

if works:
  print "[+] Basic symbol expansion seems to work"  
#SYMb.update(30, 0, 5)
#dump()

################################
#next, test working with the IR
# making sure everything is pretty and so on
EAX = ir.register("eax:32-0")
EBX = ir.register("ebx:32-0")
ECX = ir.register("ecx:32-0")
EDX = ir.register("edx:32-0")
ESP = ir.register("esp:32-0")
EBP = ir.register("ebp:32-0")

SYMa = ssa.ssa_symbol(str(EAX.register_name), EAX.bitmin, EAX.bitmax)
SYMb = ssa.ssa_symbol(str(EBX.register_name), EBX.bitmin, EBX.bitmax)
SYMc = ssa.ssa_symbol(str(ECX.register_name), ECX.bitmin, ECX.bitmax)
SYMd = ssa.ssa_symbol(str(EDX.register_name), EDX.bitmin, EDX.bitmax)
SYMs = ssa.ssa_symbol(str(ESP.register_name), ESP.bitmin, ESP.bitmax)
SYMp = ssa.ssa_symbol(str(EBP.register_name), EBP.bitmin, EBP.bitmax)

symdict = {"eax":SYMa, "ebx": SYMb, "ecx": SYMc, "edx": SYMd, "esp": SYMs, "ebp" : SYMp }
expression = [ir.register_operand("esp", ESP), '=', ir.register_operand("esp",ESP), '+', 4]

works = True

#10: esp = esp + 4
state = ssa.translate_ops(symdict, expression[2:], 5)
if str(state) != "(((undefined_esp)+4))":
  works = False
  print "translate_ops produced incorrect state :("
  print str(state)
#10: esp = esp + 4
#20: esp = esp + 4
#30: esp = esp + 4
SYMs.update([state], 10)
state = ssa.translate_ops(symdict, expression[2:], 20)
SYMs.update([state], 20)
state = ssa.translate_ops(symdict, expression[2:], 30)
SYMs.update([state], 30)
string_ = "".join([str(x) for x in SYMs.get_states()])


if string_ != "(((((undefined_esp)+4)+4)+4))":
  works = False
  print "consecutive translate_ops produced incorrect state :("
  print string_

SYMs.update([10,11], 1)
SYMs.update([5], 1)
vals = SYMs.get_values()
if len(vals) != 3 or vals[0] != 22 and vals[1] != 23 and vals[2] != 17:
  works = False
  print "Resolved multiple states incorrectly!!"

#test out clearing, e.g. after a function call
SYMs.clear(1)
SYMs.update([100], 1)
vals = SYMs.get_values()

if len(vals) != 1 or vals[0] != 112:
  works = False
  print "GOT wrong value or length, expected 112, got",vals, SYMs.get_states()
if works:
  print "[+] Everything seems to work"


