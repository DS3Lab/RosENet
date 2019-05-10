#!/cluster/apps/python/3.6.0/x86_64/bin/python3
from prody import parsePDB, writePDB 
from multiprocessing import Pool
from pathlib import Path
import numpy as np

def get_files(folder):
  return folder.glob('*/*/*_complex_*.pdb')

def make_complex_pdb(complex_pdb):
  complex = parsePDB(str(complex_pdb))
  protein_pdb = complex_pdb.parent / complex_pdb.name.replace('complex','protein')
  protein = complex.select('protein')
  writePDB(str(protein_pdb), protein)

def process(args):
  try:
    make_complex_pdb(args)
  except Exception as e:
    print(e)
    return False
  return True

if __name__ == "__main__":
  parent_folder = Path('/cluster/scratch/hhussein/Structures')
  p = Pool(48)
  p.map(process, get_files(parent_folder))
