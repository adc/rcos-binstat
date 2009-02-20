import ir

class CodeBlock:
  def __init__(self, code):
    self.code = code
    self.start = code[0].address
    self.end = code[-1].address

    self.next = 0
    self.branch = 0
    self.parents = []
    
  def split(self, address):
    if address <= self.start or address > self.end:
      return None
    
    top = []
    bottom = []
    switch = 0
    for x in self.code:
      if switch:
        bottom.append(x)
      else:
        if x.address >= address:
          switch = 1
          bottom.append(x)
        else:
          top.append(x)
    
    self.code = top
    self.end = self.code[-1].address
    
    return CodeBlock(bottom)

def CBcmp(a,b):
      return a.start - b.start

def is_stack_sub(x):
  #look for stack pointer
  if len(x.ops) == 5:
    dest_op = x.ops[0]
    operand = x.ops[4]
    if dest_op.register_name == "stack":        
      if operand.type != "constant":
        return
      
      value = 0
            
      if x.ops[3] == '+':
        value = operand.value
      elif x.ops[3] == '-':
        value = -opernad.value
      else:
        return
      
      if value < 0:
        return 1
  return 0


def linear_sweep_split_functions(code):
  functions = {}
  func_start_addr = 0

  current_function = []
  current_start = code[0].address
  for x in code:
    prev = func_start_addr
    if x.type == "call":
      if x.dest.type == "constant":
        pass#print "CALL %d %x"%(x.dest.value, x.dest.value+x.address)
    elif x.type == "operation":
      if is_stack_sub(x):
        func_start_addr = x.address
    
    if prev != func_start_addr:
      functions[current_start] = current_function
      current_function = [x]
      current_start = func_start_addr
    else:
      current_function.append(x)

  return functions

def dump_code(func):
  print "@@@@@\t\t"+hex(func),"  @@@"
  for instr in f[func]:
    print "0x%x >>>   "%instr.address,instr

  print "\n"

def make_blocks(code):
  #split up code into blocks based on branches
  
  blocks = [CodeBlock(code)]
  
  #sweep 1, find local branch dests and split the blocks
  for instr in code:
    if instr.type == "branch_true":
      dest = instr.dest.value + instr.address
      for i in range(0, len(blocks)):
        #split the destination 
        if blocks[i].start < dest and blocks[i].end >= dest:
          newblock = blocks[i].split(dest)
          if newblock:
            blocks.insert(i, newblock)
          else:
            raise Exception("FAILED TO SPLIT @ %x"%instr.address)
      #split the current block
      for i in range(0, len(blocks)):
        #split the destination 
        if blocks[i].start < instr.address and blocks[i].end >= instr.address:
          newblock = blocks[i].split(instr.address)
          if newblock:
            blocks.insert(i, newblock)
          else:
            raise Exception("FAILED TO SPLIT @ %x"%instr.address)

  #sweep 2, connect all the dots
  
  for i in range(0, len(blocks)-1):
    blocks[i].next = blocks[i].start
    instr = blocks[i].code[-1]
    dest = 0
    if instr.type == "branch_true":
      dest = instr.dest.value + instr.address
      blocks[i].branch = dest
    
    if dest:
      for j in range(0, len(blocks)) :
        if blocks[j].start == dest:
          blocks[j].parents.append(blocks[i].start)
          break
    
  blocks.sort(CBcmp)
  
  return blocks

def graph_function(code):
  blocks = make_blocks(code)

  for b in blocks:
    print "********", hex(b.start), '-', hex(b.end), "********"
    print "parents: ",`[hex(x) for x in b.parents]`
    print "next: %x   branch: %x"%(b.next, b.branch)
    for instr in b.code:
      print hex(instr.address), instr
    print ""
  #sweep 2, draw connections

def make_flow_graph(code):
  f = linear_sweep_split_functions(code)
  for func in f:
    graph_function(f[0x10001944])
    break

"""
  for n in code:
    if isinstance(n, ir.jump):
      print "0x%x:    "%n.address,n
    elif isinstance(n, ir.call):
      if isinstance(ir.dest, ir.constant_operand):
        call_dests.append( ir.constant_operand.value )
      print "0x%x:    "%n.address,n
    elif isinstance(n, ir.branch_true):
      print "0x%x:    "%n.address,n
    elif isinstance(n, ir.ret):
      print "0x%x:    "%n.address,n    
"""