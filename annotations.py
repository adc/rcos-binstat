import struct
import elf
import graphs
import ssa
import util


def libcall_transform(arch, ssa_vals, instr):
  if instr.dest.type == 'register':
    src_addr = ssa_vals[str(instr.dest.register_name)].get(instr.address)
  else:
    src_addr = str(instr.dest.value)
  
  if src_addr.isdigit():
    addr = int(src_addr)
    if addr in arch.external_functions:
      instr.annotation= '### ' + arch.external_functions[addr] + "   %x"%addr
    else:
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

                value = ssa.resolve_ssa(block.ssa_vals, instr.ops[2:])
                instr.annotation = '            '+value
                if value.isdigit():
                  value = int(value)
                  if value in bin.memory:
                    data = util.pull_ascii(bin.memory, value)
                    if len(data) > 1:
                      instr.annotation = ' @@@@@  ' + `data`
                      
        elif instr.type == 'load':
          src_addr = block.ssa_vals[str(instr.src.register_name)].get(instr.address)
          if src_addr.isdigit():
            addr = int(src_addr)
            #update on load
            if addr in bin.memory and addr+instr.size in bin.memory:
              sizemap = {1: 'B', 2: 'H', 4: 'L', 8: 'Q'}
              value = struct.unpack(arch.endianness + "%s"%sizemap[instr.size], bin.memory.getrange(addr, instr.size+addr))[0]
              value = "%d"%value
              if value in bin.memory:
                data = util.pull_ascii(bin.memory, value)
                if len(data) > 1:
                  value = data
              instr.annotation = "%%%% addr_%x -> (%s)"%(addr, value)

        elif instr.type == 'call':
          libcall_transform(arch, block.ssa_vals, instr)
