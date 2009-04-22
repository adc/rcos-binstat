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
        return 0
      
      if value < 0:
        return value
  return 0

def match_template(template, code):
  a = template
  b = code
  if a.type == b.type:
    if a.type == 'operation':
      if len(a.ops) == len(b.ops):
        for op_a,op_b in zip(a.ops,b.ops):
          match = False
          if op_a == 'stack':
            if op_a == op_b.register_name:
              match = True
          elif op_a == op_b:
            match = True
          elif op_a == 'reg':
            if op_b.type == 'register':
              match = True
          elif op_a.type == op_b.type and op_a.type == 'constant':
            if op_a.value == op_b.value:
              match = True
          if not match:
            return 0
      else:
        return 0  
    elif a.type == 'store':
      if a.dest == 'stack':
        if b.dest.register_name != 'stack':
          return 0
    else:
      return 0
  else:
    return 0
      
  return 1
  
def find_prologue(code, index):
  
  #print code[:index+1]
  prologues = [
    [ir.operation('stack', '=', 'stack', '-', ir.constant_operand(4)), ir.store('reg'),
     ir.operation('reg', '=', 'stack')]
  ]

  #move backwards until a prologue or
  # a nop or 
  # an epilogue is found
  
  for p in prologues:
    go = 0
    sz = len(p)
    j = index-sz
    while j >= 0:
      #print j, code[j:j+sz]
      good = True
      for k in range(sz):
        if code[j+k].type == 'operation':
          if 'NOP' in code[j+k].ops:
            return j+1
        
        if not match_template(p[k], code[j+k]):
          good = False
          break
        
      if good:
        return j+1
        
      j -= 1

  return index    
    
  
def linear_sweep_split_functions(code):
  if len(code) == 0: return

  functions = {}
  func_start_addr = 0

  current_function = []
  current_start = code[0].address
  
  index = 0
  for x in code:
    prev = func_start_addr
    if x.type == "operation":
      if is_stack_sub(x) < -4:
        #try to find a prologue above
        new_index = find_prologue(code, index)
        xaddr = code[new_index].address
        #print hex(xaddr), code[new_index-1:index]
        #put prologue in Queue
        Q = code[new_index-1:index]
        
        func_start_addr = xaddr
    
    if prev != func_start_addr:
      #Q holds prologue, subtract it from the current function
      #and add it to the new one
      functions[current_start] = current_function[:-len(Q)]
      current_function = Q+[x]
      current_start = func_start_addr
      Q = []
    else:
      #print "append", hex(x.address)
      current_function.append(x)

    index += 1

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
      mask = 0xffffffff
      if instr.dest.signed:
        mask = 0x7fffffff
      dest = instr.dest.value + instr.address
      dest = dest & mask
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
      mask = 0xffffffff
      if instr.dest.signed:
        mask = 0x7fffffff
      dest = instr.dest.value + instr.address
      dest = int(dest & mask)
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
    s.replace('"', "\"")
    if s[0] == '\'':
      s = '"' + s[1:-1] + '"'
    o += "    block_0x%x [shape=box align=left label=%s];\n"%(b.start, s)
    if b.next:
      o += "    block_0x%x -> block_0x%x;\n"%(b.start, b.next)
    if b.branch:
      o += "    block_0x%x -> block_0x%x;\n"%(b.start, b.branch)
  o += "}\n"
  open("graphs/%x.dot"%code[0].address,'w').write(o)
  return
  
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