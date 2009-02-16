# TODO: 64-bit mips instructions

import ir
import struct

class Translator:
  """ Base class for IR translators
    To implement a translator for your architecture
    you must implement the following:

    register_info() -> returns information about available flags, registers, and their sizes

    disassemble(bytecodes, base_addr)
    translate(target) -> returns IR representation of binary
    
    mem_info() -> describes memory regions 
    """
  def __init__(self):
    pass

class MIPS_Translator(Translator):
  def __init__(self):
    Translator.__init__(self)
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
        ir.register("$29", "$sp"),
        ir.register("$30", "$fp"),
        ir.register("$31", "$ra"), 
        ir.register("$32", "$pc")
    ]

    for i in range(32):
      self.registers.append(ir.register("$f%d"%i))
    self.registers.append(ir.register("FP_COND"))
    self.registers.append(ir.register("HILO",size=8))
    self.registers.append(ir.register("FIR"))
    self.registers.append(ir.register("FSR"))
      
  def mem_info():
    pass
    
  def decode_register(self, reg):
    R = None
    if type(reg) == str:
      for r in self.registers:
        if r.name == reg or reg in r.aliases:
          R = r
          break
      if not R:
        raise Exception("DR: Unknown register: %s"%reg)
    else:
      for r in self.registers:
        if r.name == "$%d"%reg:
          R = r
          break
      if not R:
        raise Exception("DR: Unknown register: $%d"%reg)

        
    return ir.register_operand(R)

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
          [ir.operation(DR(rd),'=',DR("$pc"),"+",4),
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
      59  : "dsra",
      60  : "dsll32",
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
  bgez	 rs, label        	 000001	 rt = 00001
  bgtz	 rs, label        	 000111	 rt = 00000
  blez	 rs, label        	 000110	 rt = 00000
  bltz	 rs, label        	 000001	 rt = 00000

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
              [ir.operation(DR(rs),'==',DR(rt)), ir.branch_true(ir.constant_operand((offset<<2) + 4))]),
      5   :   ("bne",
              [ir.operation(DR(rs),'!=',DR(rt)), ir.branch_true(ir.constant_operand((offset<<2) + 4))]),
      6   :   ("blez",
              [ir.operation(DR(rs),'<=',ir.constant_operand(0)), ir.branch_true(ir.constant_operand((offset<<2) + 4))]),
      7   :   ("bgtz",
              [ir.operation(DR(rs),'>',ir.constant_operand(0)), ir.branch_true(ir.constant_operand((offset<<2) + 4))]),
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
              [ir.operation(DR(rt),'=',ir.constant_operand(offset,size=2),'<<',16)]),
      20  :   ("beqzl",
              [ir.operation(DR(rs),'==',DR(rt)), ir.branch_true(ir.constant_operand((offset<<2) + 4))]),
      21  :   ("bnezl",
              [ir.operation(DR(rs),'!=',DR(rt)), ir.branch_true(ir.constant_operand((offset<<2) + 4))]),
      22  :   ("blezl",
              [ir.operation(DR(rs),'<=',ir.constant_operand(0)), ir.branch_true(ir.constant_operand((offset<<2) + 4))]),
      23  :   ("bgtzl",
              [ir.operation(DR(rs),'>',ir.constant_operand(0)), ir.branch_true(ir.constant_operand((offset<<2) + 4))]),
      25  :   ("daddiu", #unsigned is a misnomer
              [ir.operation(DR(rt),'=',DR(rs),'+',ir.constant_operand(offset,size=2,signed=1))]),
      26  :   "ldl",
      27  :   "ldr",
      32  :   ("lb",
              [ir.operation(DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR(rt),size=1)]),
      33  :   ("ll", #atmoic load words
              [ir.operation(DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR(rt))]),      
      34  :   "lwl",
      35  :   ("lw",
              [ir.operation(DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR(rt))]),
      36  :   ("lbu",
              [ir.operation(DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR(rt),size=1,signed=0)]),
      37  :   ("lhu",
              [ir.operation(DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR(rt),size=2,signed=0)]),
      38  :   "lwr", #todo
      39  :   ("lw",
              [ir.operation(DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR(rt))]),      
      40  :   ("sb",
              [ir.operation(DR(rs),'+',ir.constant_operand(offset,size=2)), ir.store(DR(rt),size=1)]),
      41  :   ("sh",
              [ir.operation(DR(rs),'+',ir.constant_operand(offset,size=2)), ir.store(DR(rt),size=2)]),
      43  :   ("sw",
              [ir.operation(DR(rs),'+',ir.constant_operand(offset,size=2)), ir.load(DR(rt))]),
      44  :   "sdl",
      45  :   "sdr",
      49  :   "lwc1",
      53  :   "ldc1",
      55  :   "ld",
      57  :   "swc1",
      61  :   "sdc1",
      63  :   "sd",
      
    }
    
    try:
      
      if OP == 1:
        code = rt
        
        if code in [0,2]: #BLTZ, BLTZL
          instr = ("bltz",[ir.operation(DR(rs),'<',ir.constant_operand(0)), 
                  ir.branch_true(ir.constant_operand((offset<<2) + 4))])
        elif code in [1,3]: #BGEZ, BGEZL
          instr = ("bltz",[ir.operation(DR(rs),'>=',ir.constant_operand(0)), 
                  ir.branch_true(ir.constant_operand((offset<<2) + 4))])
        elif code in [16,18]: #BLTZAL, BLTZALL
          instr = ("bltzal",[ir.operation(DR(rs),'<',ir.constant_operand(0)),
                  ir.operation(DR("$ra"),'=',DR("$pc"),'+',4),
                  ir.call(ir.constant_operand((offset<<2) + 4))])
        elif code in [17,19]: #BGEZAL,BGEZALL
          instr = ("bgezal",[ir.operation(DR(rs),'>=',ir.constant_operand(0)),
                  ir.operation(DR("$ra"),'=',DR("$pc"),'+',4),
                  ir.call(ir.constant_operand((offset<<2) + 4))])
      else:
        instr = instructions[OP]
          
      return instr
    except KeyError:
      raise Exception("unknown op code for I types: %d"%OP)

  def get_j_type(self, opcode):
    OP = opcode >> 26
    target = opcode & 0x3ffffff
    DR = self.decode_register
    
    if OP == 2:
      return ("j", [ir.jump(ir.constant_operand(target))])
    elif OP == 3:
      return ("jal", [ir.operation(DR("$ra"),'=',DR('$pc'),'+',4),
                    ir.jump(ir.constant_operand(target))])

  def get_coproc_type(self, opcode):
    return "unsupported"
  
  def disassemble(self, bytecodes, base_addr):
    opcode = struct.unpack(">L", bytecodes)[0]
    
    OP = opcode >> 26

    ret = None
    
    if OP == 0:
      ret = self.get_r_type(opcode)
    elif OP in [2,3]:
      ret = self.get_j_type(opcode)
    elif OP in [16,17,18,19]:
      ret = self.get_coproc_type(opcode)
    else:
      ret = self.get_i_type(opcode)
    
    if type(ret) != str:
      for n in ret[1]:
        n.address = base_addr
    return ret

  def translate(self, target):
    output = []
    for seg in target.memory.segments:
      if seg.code:
        x = target.entry_points[0]

        while x < seg.end:
          r = self.disassemble(target.memory[x:x+4], x)
          if type(r) == str:
            z = [ir.unhandled_instruction(r)]
            z[0].address = x
          else:
            z  = r[1]
          output += z
          x += 4
    return output        