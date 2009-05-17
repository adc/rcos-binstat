"""
This is an attempt to do ltrace....without the trace. :-)

Take a flow graph

  -> extract all of the function calls
    :: resolve the arguments as best as possible
      (hard part (the work): propagating values across branches)

    not done yet  
      
"""


import symbolic
import math

class StackFrame:
  def __init__(self, wordsize):
    self.offset = 0
    self.words = {}
      
  def write(self, offset, symbol):
    self.words[offset] = symbol
  
  def read(self, offset):
    if offset not in self.words:
      return None
    return self.words[offset]


    
def funk(binary, translator, blocks):
  
  for r in translator.registers:
    if "stack" in r.aliases:
      stack_reg = r
    
  
  print "[+] Function has %d blocks"%len(blocks)
  
  
  for b in blocks:
    stack_frame = StackFrame(r.size)
    
    print hex(b.start)+'-'+hex(b.end)
    print "     branch: %.8x     next: %.8x"%(b.branch,b.next)
    prev = None

    #SSA per-block for now
    last_reg_write = {}
    for r in translator.registers:
      last_reg_write[r.register_name] = None
    #zomg single static assigment
    track_ssa = {}

    for instr in b.code:
      #instr.annotation=""
      
      if instr.type == "operation":
                
        if len(instr.ops) > 2:
          #check for stack assignment operation
          if instr.ops[1] == '=':
            #save each last assignment
            reg_name = instr.ops[0].register.register_name
            ssa_name = reg_name + '_'+str(instr.address) + "_"+ str(b.code.index(instr))

            track_ssa[ssa_name] = symbolic.make_ssa_like(last_reg_write, track_ssa, instr.ops[2:])
            last_reg_write[reg_name] = ssa_name
      
      elif instr.type == 'call':
        #dump stack
        #4 args for now
        if last_reg_write[stack_reg.register_name]:
          ssa_stack_expr = track_ssa[last_reg_write[stack_reg.register_name]]
        
        addr = symbolic.eval_with_reg_sub(stack_reg, ssa_stack_expr)
        print ""
        #dump 4 arguments for now
        for i in range(0, 4):
          offset = addr+4 + i*4
          val = stack_frame.read(offset)
          if val:
            print "   arg %d offset=%5d----->    %20s"%(i+1, offset, val)

      elif instr.type == 'store':

        destination = symbolic.make_ssa_like(last_reg_write, track_ssa, [prev.ops[0]])
        if stack_reg.register_name in destination:
          #check if it is related to esp
          stack_offset = eval_with_reg_sub(stack_reg, destination)
          if stack_offset:
            stack_frame.write(stack_offset, symbolic.get_ssa(last_reg_write, track_ssa, instr.dest))
            #print "storing %s @ %d"%(stack_frame.read(stack_offset), stack_offset)
      
      print "       %.8x: "%instr.address, instr
      prev = instr
      
      
      
      
      