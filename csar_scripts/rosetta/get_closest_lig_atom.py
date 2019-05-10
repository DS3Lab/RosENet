from prody import *
import numpy as np
import sys

def process(file, output):
  complex = parsePDB(file)
  metals = complex.select("chain Z")
  #import pdb; pdb.set_trace()
  result = []
  if metals:
    for atom in metals:
      pos = atom.getCoords()
      close_ligand = complex.select("resname WER and (not (element H or element C)) and within 2.5 of t", t=pos)
      if close_ligand:
        #close = close_ligand[np.argmin(np.linalg.norm(close_ligand.getCoords() - pos, axis=1))]
        for close in close_ligand:
          result.append((atom.getName(), str(atom.getResnum())+atom.getChid(), close.getName(), str(close.getResnum())+close.getChid()))
  with open(output, "w") as f:
    for r in result:
      f.write(f"AtomPair {r[0]} {r[1]} {r[2]} {r[3]} SQUARE_WELL 2.5 -2000\n")
  

if __name__ == "__main__":
  process(sys.argv[1], sys.argv[2])
