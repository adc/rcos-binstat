import string

def pull_ascii(data, offset):
  o = ""
  
  while offset in data and data.get(offset) != "\x00":
    val = data.get(offset)
      
    if val not in string.printable: break
    o += val
    offset += 1
  return o
