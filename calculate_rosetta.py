from operator import itemgetter
from prody import parsePDB, calcCenter, parseDCD, moveAtoms
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

def save_grid(saving_path, image):
  with h5py.File(str(saving_path), "w", libver='latest') as f:
    f.create_dataset("grid", dtype='f4', data=image)

def get_files(folder):
  return folder.glob('*/*_complex_*.pdb')

def import_data(pdb_path):
  data_path = str(pdb_path).replace('.pdb', '.attr.npz')
  data = np.load(data_path)
  radii = dict(zip(data['rc_keys'], data['radius_values']))
  charges = dict(zip(data['rc_keys'],data['charge_values']))
  energies = data['energy_values'].squeeze()
  energy_keys = data['energy_keys']
  return radii, charges, energy_keys, energies

from scipy.spatial import KDTree
def apply_filter(filter_type, points, values, targets, radii):
  c = 0
  mask = np.linalg.norm(points,axis=-1) <= 12.5*np.sqrt(3)
  points = points[mask]
  values = values[mask,:]
  radii = radii[mask]
  dists = cdist(points,targets)
  aux = np.where(dists < 5, filter_type(dists,radii), 0)
  del dists
  #import pdb; pdb.set_trace()
  result = np.array([values[np.argmax(aux,axis=0),i] * np.max(aux,axis=0) for i in range(values.shape[-1])])
  result = np.swapaxes(result,0,1)
  return result

def interpolate(int_type, points, values, targets):
  points_x, points_y, points_z = [c.flatten() for c in np.split(points,3,axis=1)]
  targets_x, targets_y, targets_z = [c.flatten() for c in np.split(targets,3,axis=1)]
  rbf = Rbf(points_x, points_y, points_z, values, function=int_type)
  return rbf(targets_x, targets_y, targets_z)

GRIDS = ['fa_atr', 'fa_rep', 'fa_sol', 'fa_elec']

def grid_around(center, size, spacing=1.0):
  size_ang = ((size - 1) / 2.) * spacing
  ex_min = center - size_ang
  ex_max = center + size_ang

  x = np.linspace(ex_min[0], ex_max[0], size)
  y = np.linspace(ex_min[1], ex_max[1], size)
  z = np.linspace(ex_min[2], ex_max[2], size)
  return np.stack(np.meshgrid(x,y,z,indexing='ij'),axis=-1)

def get_keys(pdb):
  resnums = pdb.getResnums()
  chids = pdb.getChids()
  names = pdb.getNames()
  keys = np.char.add(np.char.mod('%s-',np.char.replace(np.char.add(np.char.mod('%s ', resnums),chids),' ', '-')),names)
  return keys

def build_images(pdb_path, size, interpolation_mode):
  complex = parsePDB(str(pdb_path))
  protein = complex.select("protein or water")
  ligand = complex.select("resname WER")
  center = calcCenter(ligand.getCoords())
  moveAtoms(complex, by=-center)
  center = calcCenter(complex.select("resname WER").getCoords())

  size_ang = ((size - 1) / 2.) * (24/(size-1))
  ex_min = center - size_ang
  ex_max = center + size_ang

  position_matrix = grid_around(center, size, spacing=24/(size-1))
  radii, charges, energy_keys, energies = import_data(pdb_path)
  coordinates = complex.getCoords()
  keys = get_keys(complex)
  keys_p = get_keys(protein)
  keys_l = get_keys(ligand)
  
  key_map = dict(zip(keys, range(len(keys))))

  energy_ids = [i for i, x in enumerate(energy_keys) if x in key_map]
  energy_ids_p = [i for i, x in enumerate(energy_keys) if x in key_map and x in keys_p]
  energy_ids_l = [i for i, x in enumerate(energy_keys) if x in key_map and x in keys_l]
  e_p, e_l = energies[energy_ids_p,:], energies[energy_ids_l,:]
  return e_p, e_l
#  energy_coordinates = np.array([coordinates[key_map[x]] for x in energy_keys if x in key_map])
#  energy_coordinates_p = np.array([coordinates[key_map[x]] for x in energy_keys if x in key_map and x in keys_p])
#  energy_coordinates_l = np.array([coordinates[key_map[x]] for x in energy_keys if x in key_map and x in keys_l])
  
#  radii_c = np.array([radii[x] for x in energy_keys if x in key_map])
#  radii_p = np.array([radii[x] for x in energy_keys if x in key_map and x in keys_p])
#  radii_l = np.array([radii[x] for x in energy_keys if x in key_map and x in keys_l])

#  image = {}
#  image_p = {}
#  image_l = {}
#  for field in GRIDS:
#      image[field] = np.zeros(3 * (size, ))
#      image_p[field] = np.zeros(3 * (size, ))
#      image_l[field] = np.zeros(3 * (size, ))
  #image[k] = apply_filter(filter_mode, energy_coordinates, energies[energy_ids,i], position_matrix.reshape((-1,3)),radii_c).reshape(3*(size,) + (-1, ))
#  rosetta_p = apply_filter(filter_mode, energy_coordinates_p, energies[energy_ids_p,:], position_matrix.reshape((-1,3)),radii_p).reshape(3*(size,) + (-1,))
#  rosetta_l = apply_filter(filter_mode, energy_coordinates_l, energies[energy_ids_l,:], position_matrix.reshape((-1,3)),radii_l).reshape(3*(size,) + (-1,))
  #return np.concatenate((rosetta_p, rosetta_l), axis=-1)

def process_file(file):
  try:
    image = build_images(file, size, interpolation_mode)
  except Exception as e:
    print(file)
    print(e)
    return None
  return image

def exp_12(r,rvdw):
  rvdw = rvdw.reshape((-1,))
  rr = rvdw[:,None]/r
  ret = np.where(r==0, 1, 1 - np.exp(-(rr)**12))
  return ret


import pdb;
if __name__ == "__main__":
  size = 25
  interpolation_mode = exp_12
  filter_mode = exp_12
  #process_file(Path('/cluster/scratch/hhussein/pdbbind2018/10gs/10gs_complex_0002.pdb'))
  p = Pool(48)
  a = p.map(process_file, get_files(Path('/cluster/scratch/hhussein/pdbbind2018')))
  pdb.set_trace()
  pass
  #list(map(process_file, get_files(Path('/cluster/scratch/hhussein/pdbbind2018'))))
