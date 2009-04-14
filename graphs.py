import ir

class CodeBlock:
  def __init__(self, code):
    self.code = code
    self.start = code[0].address & 0xffffffff
    self.end = code[-1].address & 0xffffffff

    self.next = 0
    self.branch = 0
    self.parents = []
  
  def split(self, address):
    if address <= self.start or address > self.end:
      return None
    
    if len(self.code) == 1:
      raise Exception("trying to split sz =1")

    i = 1
    while i < len(self.code):
      if self.code[i].address >= address:
        break
      i += 1
        
    #print "Splitting %x-%x:%d  @%x"%(self.start,self.end, len(self.code), address),
    top = self.code[:i]
    bottom = self.code[i:]
      
    #print "Old block becomes %x-%x"%(top[0].address, top[-1].address)
    #print "New block becomes %x-%x"%(bottom[0].address, bottom[-1].address)
    self.code = top
    self.end = top[-1].address
    #print "old=%x-%x:%d     new=%x-%x:%"%(self.start,self.end, len(self.code), bottom[0].address, bottom[-1].address, len(bottom))
    
    return CodeBlock(bottom)

def CBcmp(a,b):
  return int(a.start - b.start) 

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
        value = -operand.value
      else:
        return
      
      if value < 0:
        return 1
  return 0


def linear_sweep_split_functions(code):
  if len(code) == 0: return

  functions = {}
  func_start_addr = 0

  current_function = []
  current_start = code[0].address
  for x in code:
    prev = func_start_addr

    if x.type == "operation":
      if is_stack_sub(x):
        func_start_addr = x.address
    
    if prev != func_start_addr:
      functions[current_start] = current_function
      current_function = [x]
      current_start = func_start_addr
    else:
      current_function.append(x)

  if current_function:
    functions[current_start] = current_function
  return functions

def dump_code(func):
  print "@@@@@\t\t"+hex(func[0].address),"  @@@"
  for instr in func:
    print "0x%x >>>   "%instr.address,instr

  print "\n"

def make_blocks(code):
  #split up code into blocks based on branches
  
  blocks = [CodeBlock(code)]
  
  #sweep 1, find local branch dests and split the blocks
  SPLITNEXT = 0
  for instr in code:
    
    if SPLITNEXT:
      SPLITNEXT = 0

      dest = instr.address
      for i in range(0, len(blocks)):
        #split the destination 
        if blocks[i].start < dest and blocks[i].end >= dest:
          newblock = blocks[i].split(dest)
          if newblock:
            blocks.insert(i, newblock)
            break
          else:
            #there is a case with delay slots where an address
            # can go missing and enter another slot
            #should not trigger if blocks are inserted in order
            print blocks[i].code
            raise Exception("FAILED TO SPLIT @ %x"%dest)
            
    
    if instr.type == "branch_true":
      dest = instr.dest.value + instr.address
      dest = dest & 0xffffffff
      for i in range(0, len(blocks)):
        #split the destination 
        if blocks[i].start < dest and blocks[i].end >= dest:
          #print "SPLITTING %x-%x @ %x"%(blocks[i].start, blocks[i].end, dest)
          newblock = blocks[i].split(dest)
          if newblock:
            blocks.insert(i, newblock)
            break            
          else:
            print "2",blocks[i].code, hex(blocks[i].start), hex(blocks[i].end)
            raise Exception("FAILED TO SPLIT @ %x"%dest)
      #split after the current block      
      SPLITNEXT = 1
  
  #remove empty blocks
  for x in blocks:
    if len(x.code) == 0:
      blocks.remove(x)
  #sweep 2, connect all the dots
  blocks.sort(cmp=CBcmp)
  for i in range(0, len(blocks)-1):
    blocks[i].next = blocks[i+1].start
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
  
  return blocks

def graph_function(code):
  blocks = make_blocks(code)

  o = "digraph function_0x%x {\n"%(code[0].address)  
  for b in blocks:
    c = "\n".join(["0x%x: %s"%(instr.address,repr(instr)) for instr in b.code])
    s = "%r"%c
    if s[0] == '\'':
      s = '"' + s[1:-1] + '"'
    o += "    block_%s [shape=box align=left label=%s];\n"%(hex(b.start), s)
    if b.next:
      o += "    block_%s -> block_0x%x;\n"%(hex(b.start), b.next)
    if b.branch:
      o += "    block_%s -> block_0x%x;\n"%(hex(b.start), b.branch)
  o += "}\n"
  open("graphs/%x.dot"%code[0].address,'w').write(o)
  #return 
  
  for b in blocks:
    print "********", hex(b.start), '-', hex(b.end), "********"
    print "parents: ",[hex(x) for x in b.parents]
    print "next: %x   branch: %x"%(b.next, b.branch)
    for instr in b.code:
      print hex(instr.address), instr
    print ""
  #sweep 2, draw connections
  
def make_flow_graph(code):
  if not code:
    return
  f = linear_sweep_split_functions(code)
  k = f.keys()
  k.sort()
  for func in k:
    #print "#######func 0x%x"%func
    graph_function(f[func])
    #print "#######\n\n\n"

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