import ir

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
#    elif x.type == "ret":
#      print "func end?\n"+"-"*10
      
    
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

def graph_function(code):
  #split up code into blocks based on branches
  
  #sweep 1, find local branch dests
  print hex(code[0].address), '-', hex(code[-1].address)
  for instr in code:
    print hex(instr.address),
    if instr.type == "branch_true":
      print instr, hex(instr.dest.value + instr.address)
    else:
      print "...",instr
  

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
    