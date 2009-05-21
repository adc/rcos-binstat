import graphs
import struct
import util

def resolve_ssa(ssa_track, ops, location = None):
  outstring = ""

  for op in ops:
    if type(op) is str:
      outstring += ' %s '%op
    elif op.type == 'constant':
      outstring += " %d "%op.value
    elif op.type == 'register':
      reg_name = op.register.register_name
      
      value = ssa_track[reg_name].get(location)
      if value:
        outstring += '('+value+')'
      else:
        outstring += reg_name
    else:
      print "UNKNOWN OP TYPE",op, op.type, ops
    
  try:
    outstring = "%d"%eval(outstring)
  except:
    pass
      
  return outstring


class ssa_value:
  def __init__(self, target):
    self.target = target
    self.names = []
    self.values = {}

  def update(self, addr, aux, value):
    #assumes updates happen sequentially
    # by address
    ssa_name = self.target + '_'+str(addr) + "_"+ str(aux)    
    self.names = [(addr, ssa_name)] + self.names
    self.values[ssa_name] = value
  
  def get(self, location=None):
    #find first valid address
    #names are in order of most recent assignment
    if location:
      for address, name in self.names:
        if location > address:
          return self.values[name]

      return ""
    
    #otherwise return the most recent name
    if len(self.names) == 0:
      return ""
    else:
      return self.values[ self.names[0][1] ]

def propagate_intra_block_values(arch, callgraph, bin):
  
  sg = callgraph.keys()
  sg.sort()
  
  constant_regs = arch.get_analysis_constant_regs(bin)
  
  for r in arch.registers:
    if "stack" in r.aliases:
      stack_reg = r
    elif "pc" in r.aliases:
      pc_reg = r
  
  
  for func in sg:
    #print "====== func %x ====="%func
    for block in callgraph[func]:
      #print "--- block %x -> %x:%d--"%(block.start, block.end, len(block.code))
      #print "parents: ",[hex(x) for x in block.parents]
      #print "branches: ",hex(block.next), hex(block.branch)
      
      ssa_track = {}
      for r in arch.registers:
        ssa_track[str(r.register_name)] = ssa_value(r.register_name)
      
      for reg in constant_regs:
        ssa_track[str(reg.register_name)].update(0,0,constant_regs[reg])
      
      ####do value propagation within a block
      for instr in block.code:
        ssa_track[pc_reg.register_name].update(instr.address,0,"%d"%instr.address)
        
        if instr.type == 'operation':
          if len(instr.ops) > 2:
            if instr.ops[1] == '=':
              #update on assignment

              if instr.ops[0].register in constant_regs:
                pass
              elif instr.ops[0].register == pc_reg:
                print "HUH? write to pc reg???"
              else:
                reg_name = instr.ops[0].register.register_name

                value = resolve_ssa(ssa_track, instr.ops[2:])
                ssa_track[reg_name].update(instr.address,block.code.index(instr), value)

        elif instr.type == 'load':

          src_addr = ssa_track[str(instr.src.register_name)].get()
          
          if src_addr.isdigit():
            addr = int(src_addr)
            #update on load
            if addr in bin.memory and addr+instr.size in bin.memory:
              sizemap = {1: 'B', 2: 'H', 4: 'L', 8: 'Q'}
              value = struct.unpack(arch.endianness+"%s"%sizemap[instr.size], bin.memory.getrange(addr, instr.size+addr))[0]
              value = "%d"%value
            else:
              value = "addr__["+str(addr)+']'
            
            reg_name = str(instr.dest.register_name)
            ssa_track[reg_name].update(instr.address,block.code.index(instr), value)
              
        elif instr.type == "store":
          #memory destination...
          pass
      
      block.ssa_vals = ssa_track



      