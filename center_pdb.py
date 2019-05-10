from operator import itemgetter
from prody import parsePDB, calcCenter, parseDCD, moveAtoms, writePDB
import itertools
from apbs import APBS
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from collections import defaultdict
import h5py
from scipy.interpolate import Rbf
from scipy.spatial.distance import cdist

def build_images(pdb_path, size, interpolation_mode):
  complex = parsePDB(str(pdb_path))
  protein = complex.select("protein or water")
  ligand = complex.select("resname WER")
  center = calcCenter(ligand.getCoords())
  moveAtoms(complex, by=-center)
  center = calcCenter(complex.select("resname WER").getCoords())
  writePDB(str(pdb_path.parent / (pdb_path.stem + "_centered.pdb")), complex)

def process_file(file):
  try:
    image = build_images(file, size, interpolation_mode)
  except Exception as e:
    print(file)
    print(e)
    return False
  return True

def exp_12(r,rvdw):
  rvdw = rvdw.reshape((-1,))
  rr = rvdw[:,None]/r
  ret = np.where(r==0, 1, 1 - np.exp(-(rr)**12))
  return ret


if __name__ == "__main__":
  size = 25
  interpolation_mode = exp_12
  filter_mode = exp_12
  process_file(Path('/cluster/scratch/hhussein/pdbbind2018/10gs/10gs_complex_0004.pdb'))
