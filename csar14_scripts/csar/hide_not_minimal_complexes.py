#!/cluster/apps/python/3.6.0/x86_64/bin/python3
from prody import parsePDB, writePDB 
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

def get_files(folder):
  return folder.glob('*/*/score.sc')

def hide_non_minimal_complexes(score_sc):
  folder = score_sc.parent
  print(score_sc)
  csv = pd.read_csv(str(score_sc), header=1, sep=r"\s*", usecols=['total_score', 'description'])
  minimal_complex = csv.total_score.idxmin()
  minimal_name = csv.description[minimal_complex]
  hidden_folder = folder / 'other_complexes'
  hidden_folder.mkdir(exist_ok=True, parents=True)
  hide_complexes = [x for x in folder.glob('*_complex_*.pdb') if x.stem != minimal_name]
  hide_mol2 = [x for x in folder.glob('*_ligand_*.mol2') if x.stem[-4:] != minimal_name[-4:]]
  for x in hide_complexes:
    x.rename(hidden_folder / x.name)
  for x in hide_mol2:
    x.rename(hidden_folder / x.name)

def process(args):
  try:
    hide_non_minimal_complexes(args)
  except Exception as e:
    print(e)
    return False
  return True

if __name__ == "__main__":
  parent_folder = Path('/cluster/scratch/hhussein/Structures')
  #hide_non_minimal_complexes(parent_folder / '10gs' / 'score.sc')
  p = Pool(48)
  p.map(process, get_files(parent_folder))
