# TODO: 64-bit mips instructions
#TODO -> speed hit with the current decoding, dont build up massive dictionaries...
import ir
import struct
import graphs
import elf

class MIPS_Translator:
  def __init__(self):
    self.registers = [
        ir.register("$0", "$zero"),
        ir.register("$1", "$at"),
        ir.register("$2", "$v0"),
        ir.register("$3", "$v1"),
        ir.register("$4", "$a0"),
        ir.register("$5", "$a1"),
        ir.register("$6", "$a2"),
        ir.register("$7", "$a3"),
        ir.register("$8", "$t0"),
        ir.register("$9", "$t1"),
        ir.register("$10", "$t2"),
        ir.register("$11", "$t3"),
        ir.register("$12", "$t4"),
        ir.register("$13", "$t5"),
        ir.register("$14", "$t6"),
        ir.register("$15", "$t7"),
        ir.register("$16", "$s0"),
        ir.register("$17", "$s1"),
        ir.register("$18", "$s2"),
        ir.register("$19", "$s3"),
        ir.register("$20", "$s4"),
        ir.register("$21", "$s5"),
        ir.register("$22", "$s6"),
        ir.register("$23", "$s7"),
        ir.register("$24", "$t8"),
        ir.register("$25", "$t9"),
        ir.register("$26", "$k0"),
        ir.register("$27", "$k1"),
        ir.register("$28", "$gp", size=8),
        ir.register("$29", "$sp", "stack"),
        ir.register("$30", "$fp"),
        ir.register("$31", "$ra"), 
        ir.register("$32", "$pc"),
        ir.register("TMEM:32-0"),
        ir.register("TVAL:32-0")
    ]

    for i in range(32):
      self.registers.append(ir.register("$f%d"%i))
    self.registers.append(ir.register("FP_COND"))
    self.registers.append(ir.register("HILO",size=8))
    self.registers.append(ir.register("FIR"))
    self.registers.append(ir.register("FSR"))
    
    self.external_functions = {}
    
  def decode_register(self, reg):
    R = None
    name = reg
    if type(reg) == str:
      for r in self.registers:
        if reg in r.aliases:
          R = r
          break
      if R is None:
        raise KeyError("DR: Unknown register: %s"%reg)
    else:
      name = "$%d"%name
      for r in self.registers:
        if "$%d"%reg in r.aliases:
          R = r
          break
      if not R:
        raise KeyError("DR: Unknown register: $%d"%reg)

        
    return ir.register_operand(name, R)

  def get_r_type(self, opcode):
    function = opcode & 0x3f
    rs = (opcode>>21) & 0x1f
    rt = (opcode>>16) & 0x1f
    rd = (opcode>>11) & 0x1f
    sa = (opcode>>6) & 0x1f
    
    DR = self.decode_register
    instructions = {
      0   : ("sll rd = rt << sa", 
          [ir.operation(DR(rd),"=",DR(rs),"<<",DR(sa), signed=0)]),
      2   : ("srl  rd = rt >> sa", 
          [ir.operation(DR(rd),"=",DR(rs),">>",DR(sa), signed=0)]),
      3   : ("sra rd = rt >> sa",
          [ir.operation(DR(rd),"=",DR(rs),">>",DR(sa))]),
      4   : "sllv",
      6   : "srlv",
      7   : "srav",
      8   : ("jr PC = rs", 
          [ir.jump(DR(rs))]),
      9   : ("jalr rd = return_addr, PC = rs ",
          [ir.operation(DR(rd),'=',DR("$pc"),"+",ir.constant_operand(4)),
           ir.call(DR(rs))]),
      12  : "syscall",
      13  : "break",
      16  : ("mfhi", 
          [ir.operation(DR(rd),'=',DR("HILO"))]),
      17  : ("mthi",     
          [ir.operation(DR("HILO"),'=',DR(rs),'<<',ir.constant_operand(32))]), 
      18  : ("mflo",
          [ir.operation(DR(rd),'=',DR("HILO"))]),   
      19  : ("mtlo",
          [ir.operation(DR("HILO"),'=',DR(rs))]),
      24  : ("mult LO,HI = rs*rt",
          [ir.operation(DR("HILO"),"=",DR(rs),"*",DR(rt))]),
      25  : ("multu",
          [ir.operation(DR("HILO"),"=",DR(rs),"*",DR(rt), signed=0)]),
      26  : ("div",
            [ir.operation(DR("HILO"),"=",DR(rs),"/",DR(rt))]),
      27  : ("divu",
            [ir.operation(DR("HILO"),"=",DR(rs),"/",DR(rt), signed=0)]),
      28  : "dmult",
      29  : "dmultu",
      30  : "ddiv",
      31  : "ddivu",
      32  : ("add  rd = rs + rt",
          [ir.operation(DR(rd),"=",DR(rs),"+",DR(rt))]),
      33  : ("addu",
          [ir.operation(DR(rd),"=",DR(rs),"+",DR(rt), signed=0)]),
      34  : ("sub",
            [ir.operation(DR(rd),'=',DR(rs),"-",DR(rt))]),
      35  : ("subu",
          [ir.operation(DR(rd),'=',DR(rs),"-",DR(rt), signed=0)]),
      36  : ("and",
          [ir.operation(DR(rd),"=",DR(rs),"&",DR(rt))]),
      37  : ("or",
          [ir.operation(DR(rd),"=",DR(rs),"|",DR(rt))]),
      38  : ("xor", 
          [ir.operation(DR(rd),"=",DR(rs),"^",DR(rt))]),
      39  : ("nor",
          [ir.operation(DR(rd),'=',DR(rs),"~",DR(rt))]),
      42  : ("slt",
          [ir.operation(DR(rd),'=',DR(rs), "<", DR(rt))]),
      43  : ("sltu",
          [ir.operation(DR(rd),'=',DR(rs), "<", DR(rt), signed=0)]),
      45  : ("daddu",
          [ir.operation(DR(rd),'=',DR(rs), "+", DR(rt), signed=0)]),
      47  : ("dsubu",
          [ir.operation(DR(rd),'=',DR(rs), "-", DR(rt), signed=0)]),      
      52  : "teq",
      56  : "dssl",
      58  : "todo",
      59  : "dsra",
      60  : "dsll32",
      62  : "dsrl32",
      63  : "dsra32"
    }
    if function in instructions:
      instr = instructions[function]
      if "jr" in instr[0]:
        if instr[1][0].dest == DR("$ra"):
          #this instruction is considered a 'ret'
          instr[1][0] = ir.ret(DR("$ra"))
      return instr
    else:
      raise Exception("unknown function code for R types: %d"%function)
  """
  Instruction	 Opcode	 Notes
  swc1	 rt, immediate(rs)	 111001	
  xori	 rt, rs, immediate	 001110"""      
  def get_i_type(self, opcode):
    OP = opcode >> 26
    offset = opcode & 0xffff
    rs = (opcode>>21) & 0x1f
    rt = (opcode>>16) & 0x1f
    rd = (opcode>>11) & 0x1f

    DR = self.decode_register
    
    instructions = {
      4   :   ("beq",
              [ir.operation(DR(rs),'==',DR(rt)), ir.branch_true(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4))]),
      5   :   ("bne",
              [ir.operation(DR(rs),'!=',DR(rt)), ir.branch_true(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4))]),
      6   :   ("blez",
              [ir.operation(DR(rs),'<=',ir.constant_operand(0)), ir.branch_true(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4))]),
      7   :   ("bgtz",
              [ir.operation(DR(rs),'>',ir.constant_operand(0)), ir.branch_true(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4))]),
      8   :   ("addi", #rt = rs + immediate
              [ir.operation(DR(rt),'=',DR(rs),'+',ir.constant_operand(offset,size=2))]),
      9   :   ("addiu",
              [ir.operation(DR(rt),'=',DR(rs),'+',ir.constant_operand(offset,size=2))]),
      10  :   ("slti",
              [ir.operation(DR(rt),'=',DR(rs),'<',ir.constant_operand(offset,size=2))]),
      11  :   ("sltiu",
              [ir.operation(DR(rt),'=',DR(rs),'<',ir.constant_operand(offset,size=2))]),
      12  :   ("andi",
              [ir.operation(DR(rt),'=',DR(rs),'&',ir.constant_operand(offset,size=2))]),
      13  :   ("ori",
              [ir.operation(DR(rt),'=',DR(rs),'|',ir.constant_operand(offset,size=2))]),
      14  :   ("xori",
              [ir.operation(DR(rd),"=",DR(rs),"^",ir.constant_operand(offset,size=2))]),
      15  :   ("lui",
              [ir.operation(DR(rt),'=',ir.constant_operand(offset,size=2),'<<',ir.constant_operand(16))]),
      20  :   ("beqzl",
              [ir.operation(DR(rs),'==',DR(rt)), ir.branch_true(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4))]),
      21  :   ("bnezl",
              [ir.operation(DR(rs),'!=',DR(rt)), ir.branch_true(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4))]),
      22  :   ("blezl",
              [ir.operation(DR(rs),'<=',ir.constant_operand(0)), ir.branch_true(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4))]),
      23  :   ("bgtzl",
              [ir.operation(DR(rs),'>',ir.constant_operand(0)), ir.branch_true(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4))]),
      24  :   ("daddi", 
              [ir.operation(DR(rt),'=',DR(rs),'+',ir.constant_operand(offset,size=2,signed=1))]),
      25  :   ("daddiu", #unsigned is a misnomer
              [ir.operation(DR(rt),'=',DR(rs),'+',ir.constant_operand(offset,size=2,signed=1))]),
      26  :   "ldl",
      27  :   "ldr",
      29  :   "JALX",
      32  :   ("lb",
              [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR('TMEM'), DR(rt),size=1)]),
      33  :   ("ll", #atmoic load words
              [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR('TMEM'), DR(rt))]),      
      34  :   "lwl",
      35  :   ("lw",
              [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR('TMEM'),DR(rt))]),
      36  :   ("lbu",
              [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR('TMEM'),DR(rt),size=1,signed=0)]),
      37  :   ("lhu",
              [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR('TMEM'),DR(rt),size=2,signed=0)]),
      38  :   "lwr", #todo
      39  :   ("lw",
              [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR('TMEM'),DR(rt))]),      
      40  :   ("sb",
              [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.store(DR(rt),DR('TMEM'),size=1)]),
      41  :   ("sh",
              [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.store(DR(rt),DR('TMEM'),size=2)]),
      42  :   "swl",
      43  :   ("sw",
              [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.store(DR(rt),DR('TMEM'))]),
      44  :   "sdl",
      45  :   "sdr",
      46  :   "swr",
      49  :   "lwc1",
      53  :   "ldc1",
      55  :   ("ld",
            [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR('TMEM'),DR(rt),size=8)]),
      57  :   "swc1",
      61  :   "sdc1",
      63  :   ("sd",
            [ir.operation(DR('TMEM'),'=',DR(rs),'+',ir.constant_operand(offset,size=2)), ir.store(DR(rt), DR('TMEM'),size=8)])    
    }
    
    try:
      
      if OP == 1:
        code = rt
        
        if code in [0,2]: #BLTZ, BLTZL
          instr = ("bltz",[ir.operation(DR(rs),'<',ir.constant_operand(0)), 
                  ir.branch_true(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4))])
        elif code in [1,3]: #BGEZ, BGEZL
          instr = ("bltz",[ir.operation(DR(rs),'>=',ir.constant_operand(0)), 
                  ir.branch_true(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4))])
        elif code in [16,18]: #BLTZAL, BLTZALL
          instr = ("bltzal",[ir.operation(DR(rs),'<',ir.constant_operand(0)),
                  ir.operation(DR("$ra"),'=',DR("$pc"),'+',ir.constant_operand(4)),
                  ir.call(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4),relative=0)])
        elif code in [17,19]: #BGEZAL,BGEZALL
          instr = ("bgezal",[ir.operation(DR(rs),'>=',ir.constant_operand(0)),
                  ir.operation(DR("$ra"),'=',DR("$pc"),'+',ir.constant_operand(4)),
                  ir.call(ir.constant_operand(((ir.sext16(offset)<<2)&0xfffffffff) + 4), relative=0)])
      else:
        instr = instructions[OP]
          
      return instr
    except KeyError:
      raise KeyError("unknown op code for I types: %d"%OP)

  def get_j_type(self, opcode, address):
    OP = opcode >> 26
    target = opcode & 0x3ffffff
    DR = self.decode_register
    
    if OP == 2:
      return ("j", [ir.jump(ir.constant_operand(((target<<2)&0xfffffff) + (address&0xf0000000)))])
    elif OP == 3:
      return ("jal", [ir.operation(DR("$ra"),'=',DR('$pc'),'+',ir.constant_operand(4)),
                    ir.call(ir.constant_operand(((target<<2)&0xfffffff) + (address&0xf0000000)), relative=0)])
  def get_coproc_type(self, opcode):
    return "unsupported"
  
  def disassemble(self, bytecodes, base_addr):
    opcode = struct.unpack(">L", bytecodes)[0]
    
    OP = opcode >> 26

    ret = None
    if OP == 0:
      ret = self.get_r_type(opcode)
    elif OP in [2,3]:
      ret = self.get_j_type(opcode, base_addr)
    elif OP in [16,17,18,19]:
      ret = self.get_coproc_type(opcode)
    else:
      try:
        ret = self.get_i_type(opcode)
      except KeyError, e:
        raise KeyError("%s addr=%x"%(e,base_addr))
    
    if type(ret) != str:
      for n in ret[1]:
        n.address = base_addr
        n.wordsize = 32 #TODO
    return ret

  def translate(self, target):
    output = []
    
    for seg in target.memory.segments:
      if seg.code:
        addr = target.entry_points[0]
        
        FIXDELAY = 0
        branchQ  = []
        
        while addr < seg.end:
          try:
            IR = self.disassemble(target.memory[addr:addr+4], addr)
          except KeyError, e:
            print "finishing early due to invalid disassembly", e
            break
          if type(IR) == str:
            instrs = [ir.unhandled_instruction(IR)]
            instrs[0].address = addr
          else:
            instrs  = IR[1]
                    
          added = 0
          #reordering the delay slot is kind of like the chicken and egg problem
          if FIXDELAY:
            FIXDELAY = 0
            added = 1
            #XXX even worse than normal code alert, flip the addresses also
            a = instrs[0].address
            b = branchQ[0].address
            for n in instrs:
              n.address = b
            for n in branchQ:
              n.address = a
            output += instrs
            output += branchQ

          #MIPS requires delay slot re-ordering for branches
          for n in instrs:
            if n.type in ["jump","call","ret","branch_true"]:
              #wait until next time around to add the branch
              FIXDELAY = 1
              branchQ = instrs
              break
          
          if not FIXDELAY and not added:
            output += instrs
          
          addr += 4

    return output

  def libcall_transform(self, IR, bin):
    """
    gcc calling convention is something like this
      lw t9, -offset(gp)
      jalr t9
    
    in the IR it becomes
      ($25 = $25 + offset)
      LOAD $25
      CALL $25
    """
    
    #pull out GP from REGINFO XXX this is not correct
    GP = 0
    for phdr in bin.binformat.Phdrs:
      if phdr.type == 0x70000000:
        GP = struct.unpack(">L", bin.memory[phdr.vaddr+20: phdr.vaddr+24])[0]
    
    if not GP:
      print "[x] FAILED TO FIND GP"
      return
    
    print "GP = ", hex(GP)
    
    callgraph = {}
    f = graphs.linear_sweep_split_functions(IR)
    for func in f:
      callgraph[func] = graphs.make_blocks(f[func])
    
    sg = callgraph.keys()
    sg.sort()
    for func in sg:
      #print "====== func %x ====="%func
      for block in callgraph[func]:
        #print "--- block %x -> %x:%d--"%(block.start, block.end, len(block.code))
        #print "parents: ",[hex(x) for x in block.parents]
        #print "branches: ",hex(block.next), hex(block.branch)
        
        #do value propagation within a block
        prev = None
        propreg = {}
        for r in self.registers:
          if r.register_name == "$32":
            propreg['$pc'] = 0
          else:
            propreg[r.register_name] = 0
        
        for z in block.code:
          if z.type == "operation":
            if len(z.ops) > 1:
              if z.ops[1] != "=":
                prev = z
              else:
                if len(z.ops) == 5:
                  if z.ops[0].type == "register":
                    if z.ops[3] == '+':
                      if z.ops[2].type == "register" and z.ops[4].type == "constant":
                        if propreg[str(z.ops[2].register_name)] != 0:
                          value = propreg[str(z.ops[2].register_name)] + z.ops[4].value
                          if value in bin.memory:
                            data = elf.pull_ascii(bin.memory, value)
                            if len(data) > 1:
                              z.annotation = '%%%% "'+ data.replace('"', '\"').replace("'", "\'")+ '"'
                            else:
                              z.annotation = "%%%% (%x)"%value
                          propreg[str(z.ops[0].register_name)] = value
                
              #check if an offset from gp is being used
              #and see if a string can be pulled out
              for i in range(1, len(z.ops)):
                if z.ops[i] == '+':
                  if z.ops[i-1].type == "register":
                    if z.ops[i-1].register_name == "$gp":
                      if z.ops[i+1].type == "constant":
                        data = elf.pull_ascii(bin.memory,GP+z.ops[i+1].value)
                        if data:
                          z.annotation = "GP"+str(z.ops[i+1].value)+"  @@@ " + `data`
              #print hex(z.address),z
          elif z.type == "load":
            if prev:
              if prev.ops[1] == '+':
                if prev.ops[0].type == "register" and prev.ops[2].type == "constant":
                  if prev.ops[0].register_name == "$gp":
                    addr = GP + prev.ops[2].value
                    if addr in bin.memory and (addr+z.size) in bin.memory:
                      sizemap = {1: 'B', 2: 'H', 4: 'L', 8: 'Q'}
                      value = struct.unpack(">%s"%sizemap[z.size], bin.memory[addr:z.size+addr])[0]
                      z.annotation = "%%%% (%x)"%value
                      propreg[str(z.dest.register_name)] = value
                    
              #propreg[z.dest.register_name] = 
            if z.dest.register_name == "$t9":
              if prev and prev.address == z.address:
                addr = (GP+prev.ops[2].value)&0xffffffff
                if addr in self.external_functions:
                  z.annotation= '### ' + self.external_functions[addr]

          #print hex(z.address),z
        #print "---end of block---\n"
      #print "====\n\n\n"
