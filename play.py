import ssa
import util


def get_block(callgraph, address):
  for block in callgraph:
    if block.start == address:
      return block
  return None


def propagate_ssa_values(source, dest):
  print "-- propagate %x to %x --"%(source.start, dest.start)

  for symbol in ['ebx']:#ource.ssa_vals:
    #propagate each possible value to the dest node
    reference = source.ssa_vals[symbol].get_states(source.end+1) #returns last 
    
    #oops, circular references appear if new states arent created
    #note that the states still refernce the original symbols
    #TODO: depth...
    states = []
    for r in reference:
      if isinstance(r, ssa.ssa_state):
        n = ssa.ssa_state(dest.start, -1)
        n.expression = r.expression
        states.append(n)
      else:
        states.append(r)
    
    addr = dest.start
    aux = -1
    
    dest.ssa_vals[symbol].update(states, addr, aux)
      

    
def prop_blocks(arch, bin, callgraph):
  sg = callgraph.keys()
  sg.sort()

  for r in arch.registers:
    if "stack" in r.aliases:
      stack_reg = r
    elif "pc" in r.aliases:
      pc_reg = r

  stack_reg_name = str(stack_reg.register_name)

  visited = {}
  
  for func in sg:
    print "\n>>>>>>> func 0x%x <<<<<<<<"%func

    #top down value propagation, does not do loops for now (LOL  = loops orgasm lol)
    for block in callgraph[func]:
      if block.start in visited:
        continue

      visited[block.start] = 1
      
      if block.next:
        next = get_block(callgraph[func], block.next)
        if next and next.start not in visited:
          propagate_ssa_values(block, next)

      if block.branch:
        branch = get_block(callgraph[func], block.branch)
        if branch and branch.start not in visited:
          propagate_ssa_values(block, branch)

