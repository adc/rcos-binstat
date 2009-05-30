# TODO: 64-bit mips instructions
#TODO -> speed hit with the current decoding, dont build up massive dictionaries...
import ir
import struct
import elf

class MIPS_Translator:
  def __init__(self):
    self.endianness = '>'
    self.registers = [
        ir.register("$0:32-0", "$zero"),
        ir.register("$1:32-0", "$at"),
        ir.register("$2:32-0", "$v0"),
        ir.register("$3:32-0", "$v1"),
        ir.register("$4:32-0", "$a0"),
        ir.register("$5:32-0", "$a1"),
        ir.register("$6:32-0", "$a2"),
        ir.register("$7:32-0", "$a3"),
        ir.register("$8:32-0", "$t0"),
        ir.register("$9:32-0", "$t1"),
        ir.register("$10:32-0", "$t2"),
        ir.register("$11:32-0", "$t3"),
        ir.register("$12:32-0", "$t4"),
        ir.register("$13:32-0", "$t5"),
        ir.register("$14:32-0", "$t6"),
        ir.register("$15:32-0", "$t7"),
        ir.register("$16:32-0", "$s0"),
        ir.register("$17:32-0", "$s1"),
        ir.register("$18:32-0", "$s2"),
        ir.register("$19:32-0", "$s3"),
        ir.register("$20:32-0", "$s4"),
        ir.register("$21:32-0", "$s5"),
        ir.register("$22:32-0", "$s6"),
        ir.register("$23:32-0", "$s7"),
        ir.register("$24:32-0", "$t8"),
        ir.register("$25:32-0", "$t9"),
        ir.register("$26:32-0", "$k0"),
        ir.register("$27:32-0", "$k1"),
        ir.register("$gp:32-0", "$28"),
        ir.register("stack", "$29:32-0", "$sp"),
        ir.register("$fp:32-0", "$30"),
        ir.register("$ra:32-0", "$31"), 
        ir.register("$pc:32-0", "$32", "pc"),
        ir.register("TMEM:32-0"),
        ir.register("TVAL:32-0")
    ]

    for i in range(32):
      self.registers.append(ir.register("$f%d:32-0"%i))
    self.registers.append(ir.register("FP_COND:32-0"))
    self.registers.append(ir.register("HILO:64-0"))
    self.registers.append(ir.register("FIR:32-0"))
    self.registers.append(ir.register("FSR:32-0"))
    
    self.call_clobber = []
    for i in [2,3,4,5,6,7]:
      self.call_clobber.append(self.decode_register(i))
    
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
      15  : "sync",
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
        for addr in target.entry_points:
      
          FIXDELAY = 0
          branchQ  = []
        
          while addr+4 < seg.end:
            try:
              IR = self.disassemble(target.memory.getrange(addr,addr+4), addr)
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

  def get_analysis_constant_regs(self, bin):
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
          GP = struct.unpack(">L", bin.memory.getrange(phdr.vaddr+20 , phdr.vaddr+24))[0]
  
      if not GP:
        print "[x] FAILED TO FIND GP"
        return
  
      ret = {}
      
      for r in self.registers:
        if "$0" in r.aliases:
          zero_reg = r
        if "$gp" in r.aliases:
          gp_reg = r

      ret[zero_reg] = "0"
      ret[gp_reg] = "%d"%GP
      
      return ret
  
              
