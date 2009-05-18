import graphs
import symbolic
import elf
import struct

def libcall_transform(arch, IR, bin):
  
  callgraph = {}
  f = graphs.linear_sweep_split_functions(IR)
  for func in f:
    callgraph[func] = graphs.make_blocks(f[func])
  
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
      
      last_reg_write = {}
      for r in arch.registers:
        last_reg_write[r.register_name] = None
      #zomg single static assigment
      track_ssa = {}
      
      for reg in constant_regs:
        last_reg_write[reg.register_name] = reg.register_name
        track_ssa[reg.register_name] = constant_regs[reg]

      last_reg_write[pc_reg.register_name] = pc_reg.register_name
      
      #do value propagation within a block
      for instr in block.code:
        track_ssa[pc_reg.register_name] = "%d"%instr.address
        if instr.type == 'operation':
          #check for stack assignment operation
          if len(instr.ops) > 2:
            if instr.ops[1] == '=':
              #save each last assignment
              reg_name = instr.ops[0].register.register_name
              ssa_name = reg_name + '_'+str(instr.address) + "_"+ str(block.code.index(instr))

              if instr.ops[0].register in constant_regs:
                pass
              elif instr.ops[0].register == pc_reg:
                print "HUH? write to pc reg???"
              else:
                track_ssa[ssa_name] = symbolic.make_ssa_like(last_reg_write, track_ssa, instr.ops[2:])
                last_reg_write[reg_name] = ssa_name            
              #instr.annotation = symbolic.get_ssa(last_reg_write, track_ssa, instr.ops[0])

              value = symbolic.get_ssa(last_reg_write, track_ssa, instr.ops[0])                

              if value.isdigit():
                value = int(value)
                if value in bin.memory:
                  data = elf.pull_ascii(bin.memory, value)
                  if len(data) > 1:
                    instr.annotation = ' @@@@@  ' + `data`
                  
              
        elif instr.type == 'load':

          src_addr = symbolic.get_ssa(last_reg_write, track_ssa, instr.src)

          if src_addr.isdigit():
            addr = int(src_addr)
            
            if addr in bin.memory and addr+instr.size in bin.memory:
              sizemap = {1: 'B', 2: 'H', 4: 'L', 8: 'Q'}
              value = struct.unpack(">%s"%sizemap[instr.size], bin.memory.getrange(addr, instr.size+addr))[0]
              out = "%x"%value
              if value in bin.memory:
                data = elf.pull_ascii(bin.memory, value)
                if len(data) > 1:
                  out = ' @@@@@' + data
                  
              instr.annotation = "%%%% addr_%x -> (%s)"%(addr, out)
              

              reg_name = instr.dest.register.register_name
              ssa_name = reg_name + '_'+str(instr.address) + "_"+ str(block.code.index(instr))
              track_ssa[ssa_name] = "%d"%value
              last_reg_write[reg_name] = ssa_name

            else:
              instr.annotation = "addr out of range:: "+hex(addr)

        elif instr.type == "store":
          dst_addr = symbolic.get_ssa(last_reg_write, track_ssa, instr.dest)
          value = symbolic.get_ssa(last_reg_write, track_ssa, instr.src)
          instr.annotation = "    %s -> addr_(%s)"%(value, dst_addr)

        elif instr.type == 'call':
          src_addr = symbolic.get_ssa(last_reg_write, track_ssa, instr.dest)
          if src_addr.isdigit():
            addr = int(src_addr)
            if addr in arch.external_functions:
              instr.annotation= '### ' + arch.external_functions[addr] + "   %x"%addr
            else:
              instr.annotation = ">>> %x"%addr

              