import h5py
import numpy as np
import os
from pathlib import Path
from multiprocessing import Pool

suffix = ""

def get_files():
  rosetta = [x for x in os.listdir('/cluster/scratch/hhussein/results_min2018_rosetta'+suffix) if '.hdf5' in x]
  htmd = [x for x in os.listdir('/cluster/scratch/hhussein/results_min2018_htmd') if '.hdf5' in x]
  #apbs = [x for x in os.listdir('/cluster/scratch/hhussein/results_min2018_apbs') if '.hdf5' in x]
  elec = [x for x in os.listdir('/cluster/scratch/hhussein/results_min2018_electroneg'+suffix) if '.hdf5' in x]
  files = set.intersection(set(rosetta),set(htmd),set(elec))
  return files

def combine_maps(file):
  rosetta = os.path.join('/cluster/scratch/hhussein/results_min2018_rosetta'+suffix, file)
  htmd = os.path.join('/cluster/scratch/hhussein/results_min2018_htmd', file)
  #apbs = os.path.join('/cluster/scratch/hhussein/results_min2018_apbs', file)
  elec = os.path.join('/cluster/scratch/hhussein/results_min2018_electroneg'+suffix, file)
  output = os.path.join('/cluster/scratch/hhussein/results_min2018'+suffix, file)
  if Path(output).exists():
    return
  try:
    with h5py.File(rosetta,'r') as f:
      rosetta_grid = np.array(f['grid'])
  except:
    print("Error rosetta ", file)
    return
  try:
    with h5py.File(htmd,'r') as f:
      htmd_grid = np.array(f['grid'])
  except:
    print("Error htmd ", file)
    return
  try:
    with h5py.File(elec,'r') as f:
      elec_grid = np.array(f['grid'])
  except:
    print("Error elec ", file)
    return
  #try:
  #  with h5py.File(apbs,'r') as f:
  #    apbs_grid = np.array(f['grid'])
  #except:
  #  print("Error apbs ", file)
  #  return
  grid = np.concatenate((htmd_grid,elec_grid,rosetta_grid),axis=-1)
  print(grid.shape)
  with h5py.File(output, 'w', libver='latest') as f:
    f.create_dataset("grid", dtype='f4', data=grid)

if __name__ == "__main__":
  #combine_maps('10gs_complex_0002.hdf5')
  Path('/cluster/scratch/hhussein/results_min2018'+suffix).mkdir(parents=True, exist_ok=True)
  p = Pool(48)
  p.map(combine_maps, get_files())
