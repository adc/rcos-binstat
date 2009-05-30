import struct
import elf
import graphs
import ssa
import util


def libcall_transform(arch, ssa_vals, instr):
  if instr.dest.type == 'register':
    src_addrs = ssa_vals[str(instr.dest.register_name)].get(instr.address)
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
        if instr.type == 'operation':
          #check for stack assignment operation
          if len(instr.ops) > 2:
            if instr.ops[1] == '=':
              if str(instr.ops[0].register_name) in block.ssa_vals:

                value = ssa.resolve_ssa(block.ssa_vals, instr.ops[2:], instr.address-1)
                instr.annotation = '            '+str(value)
                if isinstance(value, int):
                  if value in bin.memory:
                    data = util.pull_ascii(bin.memory, value)
                    if len(data) > 1:
                      instr.annotation = ' @@@@@  ' + `data`
                      
        elif instr.type == 'load':
          for src_addr in block.ssa_vals[str(instr.src.register_name)].get(instr.address):
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
        elif instr.type == 'store':
          if instr.src.type == 'register':
            src_addrs = block.ssa_vals[str(instr.src.register.register_name)].get(instr.address)
          else:
            src_addrs = [instr.src.value]

          if instr.dest.type == 'register':
            dest_addrs = block.ssa_vals[str(instr.dest.register.register_name)].get(instr.address)
          else:
            dest_addrs = [instr.dest.value]
          
          o = ""
          for src_addr in src_addrs:
            for dest_addr in dest_addrs:
              o += " %s -> %s OR\n"%(src_addr, dest_addr)
          o = o[:-3]
          instr.annotation = o

        elif instr.type == 'call' or instr.type == 'jump':
          libcall_transform(arch, block.ssa_vals, instr)
