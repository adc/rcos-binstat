import struct
import elf
import graphs
import ssa
import util


def libcall_transform(arch, ssa_vals, instr, aux_loc):
  if instr.dest.type == 'register':
    src_addrs = ssa_vals[str(instr.dest.register_name)].get_values(instr.address, aux_loc)
  else:
    src_addrs = [instr.get_dest()]

  for src_addr in src_addrs:
    if isinstance(src_addr,int):
      addr = src_addr
      if addr in arch.external_functions:
        instr.annotation= '### ' + arch.external_functions[addr] + "   %x"%addr
      else:
        try:
          instr.annotation = ">>> %x"%addr+'    '+str(instr.dest.value)
        except:
          instr.annotation = ">>> %x"%addr
          
def transform(arch, callgraph, bin):
  sg = callgraph.keys()
  sg.sort()
  
  constant_regs = arch.get_analysis_constant_regs(bin)
  
  for r in arch.registers:
    if "stack" in r.aliases:
      stack_reg = r
    elif "pc" in r.aliases:
      pc_reg = r
  
  for func in sg:
    for block in callgraph[func]:
      for instr in block.code:
        aux_loc = block.code.index(instr)
        
        if instr.type == 'operation':
          #check for stack assignment operation
          if len(instr.ops) > 2:
            if instr.ops[1] == '=':
              reg_name = str(instr.ops[0].register_name)
              if reg_name in block.ssa_vals:

                #here we look at addr+1 because we're interested in the result after
                # this instruction
                values = block.ssa_vals[reg_name].get_states(instr.address, aux_loc+1)
                out = ""
                for value in values:
                  if isinstance(value, int):
                    if value in bin.memory:
                      data = util.pull_ascii(bin.memory, value)
                      if len(data) > 1:
                        out +=  ' @@@@@  ' + `data` + '\n'
                  else:
                    n = []
                    for v in values:
                      #dont print out if unresolved remain
                      if isinstance(v, ssa.ssa_state):
                        if None not in v.eval():
                          n += ['{'+",".join(str(x) for x in v.eval())+'}']
                        else:
                          n += [str(v)]
                      else:
                        n += [str(v)]
                    out += str(n)
                instr.annotation += " "*20 + out
                      
        elif instr.type == 'load':
          src_addrs = block.ssa_vals[str(instr.src.register_name)].get_values(instr.address, aux_loc)
          if None in src_addrs:
            src_addrs = block.ssa_vals[str(instr.src.register_name)].get_states(instr.address, aux_loc)
          
          for src_addr in src_addrs:
            if isinstance(src_addr,int):
              addr = src_addr
              #update on load
              if addr in bin.memory and addr+instr.size in bin.memory:
                sizemap = {1: 'B', 2: 'H', 4: 'L', 8: 'Q'}
                value = struct.unpack(arch.endianness + "%s"%sizemap[instr.size], bin.memory.getrange(addr, instr.size+addr))[0]
                value = "%d"%value
                if value in bin.memory:
                  data = util.pull_ascii(bin.memory, value)
                  if len(data) > 1:
                    value = data
                instr.annotation = "%%%% (%s) <- addr_%x"%(value,addr)
            else:
              instr.annotation = " "*10+"%s <- addr_[%s]"%(instr.dest, src_addr)
                
            
        elif instr.type == 'store':

          if instr.src.type == 'register':
            src_name = str(instr.src.register.register_name)
            src_addrs = block.ssa_vals[src_name].get_values(instr.address, aux_loc)
            if None in src_addrs:
              src_addrs = block.ssa_vals[src_name].get_states(instr.address, aux_loc) 
          else:
            src_addrs = [instr.src.value]

          if instr.dest.type == 'register':
            dest_addrs = block.ssa_vals[str(instr.dest.register.register_name)].get_values(instr.address, aux_loc)
            if None in dest_addrs:
              dest_addrs = block.ssa_vals[str(instr.dest.register.register_name)].get_states(instr.address, aux_loc) 
          else:
            dest_addrs = [instr.dest.value]
          
          o = ""
          for src_addr in src_addrs:
            for dest_addr in dest_addrs:
              o += " "*20 + " %s -> %s OR\n"%(src_addr, dest_addr)
          o = o[:-3]
          instr.annotation = o

        elif instr.type == 'call' or instr.type == 'jump':
          libcall_transform(arch, block.ssa_vals, instr, aux_loc)
