class Faddr:
  def __init__(self, a):
    self.addr = a
  def __iadd__(self, i):
    self.addr += i


class Mnemcode:
  def __init__(self, addr_start):
    self.addr_start = addr_start 
    self.instructions = []

  def concat(self, other):
    offset = len(self.instructions)
    for instruct in other.instructions:
      if isinstance(instruct, list) and isinstance(instruct[1], Faddr):
        instruct[1] += offset
    self.instructions += other.instructions
  
  def get_end(self):
    return len(self.instructions)*32
  
  def append(self, instr, addr = None):
    if addr is not None:
      self.instructions.append([instr, addr])
    else:
      self.instructions.append(instr)
  
