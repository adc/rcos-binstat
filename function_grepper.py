"""
This is an attempt to do ltrace....without the trace. :-)

Take a flow graph

  -> extract all of the function calls
    :: resolve the arguments as best as possible
      (hard part (the work): propagating values across branches)
"""


import symbolic
import math

class StackFrame:
  def __init__(self, wordsize):
    self.offset = 0
    self.min = 0
    self.max = 0
    self.wordsize = wordsize

    self.words = [""]
    

  def grow(self, value):
    #TODO:: depending on the architecture too far in one direction
    #means the stack collapsed too far, should warn about this
    #or something.

    if value % self.wordsize:
      print "[X] Unaligned stack operations not supported yet! (still too funky)"
      return
      
    count = int(math.ceil(abs((value + self.offset) - self.offset)/(self.wordsize*1.0)))
    new_words = [symbolic.Void(self.wordsize)] * count
      
    if value + self.offset > self.max:
      self.words = self.words + new_words
    elif value + self.offset < self.min:
      self.words = new_words + self.words 
    
    self.offset += value
  
  def write(self, offset, symbol):
    idx = (offset + abs(self.min))/self.wordsize
    self.words[idx] = symbol
  
  def read(self, offset):
    idx = (offset + abs(self.min))/self.wordsize
    return self.words[idx]
    

class StackStateMachine:
  def __init__(self, binary, translator, blocks):
    self.target = binary
    self.translator = translator
    self.blockdict = {}
    self.stack_reg = None
    for b in blocks:
      self.blockdict[b.start] = b
    self.blocks = blocks
      
    for r in translator.registers:
      if "stack" in r.aliases:
        self.stack_reg = r
        break

    if not self.stack_reg:
      print "[X] error: Translator missing stack register"
      return

  def explore(self, block):
    print "visiting %x"% block.start
    print "branch: %x   next: %x"%(block.branch, block.next)
    if block.branch:
      if self.visited[block.branch] is False:
        self.visited[block.branch] = True
        self.explore(self.blockdict[block.branch])
    if block.next:
      if self.visited[block.next] is False:
        self.visited[block.next] = True
        self.explore(self.blockdict[block.next])

  
  def analyze(self):
    
    self.visited = {}
    for b in self.blockdict:
      self.visited[b] = False
    
    self.explore(self.blocks[0])

def eval_stack_rel_addr(instr, stack_reg, *tracked_registers):
  eval_str = ""

  for op in instr.ops[2:]:
    if type(op) is str:
      if op in '+-':
        eval_str += op
      elif op in '&':
        #ignore aligment for now
        print "[-] Ignoring stack alignment @ %x"%instr.address
        eval_str = ""
        break
      else:
        print "Unknown stack operation",op
        return
    elif op.type == 'constant':
      eval_str += str(op.value)
    elif op.type == 'register':
      if op.register == stack_reg:
        pass #grow knows this already
      else:
        pass
        #print "[X] unresolved stack operation",instr
        #return
    else:
      print 'unknown op', op
    
  try:
    return eval(eval_str)
  except:
    return None


def getbest(last_reg_write, ssa_history, dest):
  if dest.type == 'register':
    reg_name = dest.register.register_name
    if last_reg_write[reg_name]:
      return ssa_history[last_reg_write[reg_name]]
    else:
      return reg_name

  else:
    return ""

def make_ssa_like(last_reg_write, ssa_history, ops):
  outstring = ""
  
  for op in ops:
    if type(op) is str:
      outstring += ' %s '%op
    elif op.type == 'constant':
      outstring += " %d "%op.value
    elif op.type == 'register':
      reg_name = op.register.register_name
      if last_reg_write[reg_name]:
        outstring += '('+ssa_history[last_reg_write[reg_name]]+')'
      else:
        outstring += reg_name
    else:
      print "UNKNOWN OP TYPE",op, op.type, ops
  
  return outstring
  
def eval_with_reg_sub(register, string):
  eval_str = string.replace("%s &  -16 "%register.register_name, "0")
  eval_str = eval_str.replace(register.register_name, "")

  try:
    return eval(eval_str)
  except:
    return None
    
def funk(binary, translator, blocks):
  #s = StackStateMachine(binary, translator, blocks)
  #s.analyze()
  
  
  
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


            track_ssa[ssa_name] = make_ssa_like(last_reg_write, track_ssa, instr.ops[2:])
            last_reg_write[reg_name] = ssa_name

            if instr.ops[0].register == stack_reg:              
              
              value = eval_stack_rel_addr(instr, stack_reg)
              if value is not None:
                stack_frame.grow(value)
                instr.annotation = str(stack_frame.offset)
            #elif len(instr.ops) == 3:
            #  #TODOTODO make me symbolic
        #print "       %.8x: "%instr.address, instr
      
      elif instr.type == 'call':
        #assume function returns; popping off return address?
        # note this doesnt really play well for PIC where_am_i code
        #stack_frame.grow(4) #collapse stack by 4 || todo look up arch direction

        print "       %.8x: "%instr.address, instr, stack_frame.offset
        #dump stack there
        
        #4 args for now
        for i in range(stack_frame.offset+4, stack_frame.offset+20, 4):
          if i <= stack_frame.max and i <= stack_frame.min:          
            print "%5d----->    %20s"%(i, stack_frame.read(i))
      elif instr.type == 'store':

        destination = make_ssa_like(last_reg_write, track_ssa, [prev.ops[0]])
        #print "store %s @ ---> %s"%(instr.dest, destination)
        if stack_reg.register_name in destination:
          #check if it is related to esp
          stack_offset = eval_with_reg_sub(stack_reg, destination)
          if stack_offset:
            stack_frame.write(stack_offset, getbest(last_reg_write, track_ssa, instr.dest))
            #print "store %s @ stack offset %d ----> %s"%(instr.dest, stack_offset, stack_frame.read(stack_frame.offset))

        #print "       %.8x: "%instr.address, instr
        
      #else:
        #print "       %.8x: "%instr.address, instr
      
      prev = instr
      
      
      
      
      