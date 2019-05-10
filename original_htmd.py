from pathlib import Path
import numpy as np
from collections import defaultdict
import h5py
from htmd.molecule.molecule import Molecule
from htmd.molecule.voxeldescriptors import getVoxelDescriptors
from multiprocessing import Pool

def save_grid(saving_path, pdb, image):
  with h5py.File(str(saving_path), "w", libver='latest') as f:
    f.create_dataset("grid", dtype='f4', data=image)

def build_images(protein_file, ligand_file,size):
  protein = Molecule(str(protein_file))
  ligand = Molecule(str(ligand_file))
  #protein.filter('not name HG and not name CD and not name K and not name CU and not name SE and not name LI and not name NI and not name CO and not name CS and not name SR and not name MN and not name NA')
  center = np.mean(ligand.get('coords'), axis=0)
  ligand.moveBy(-center)
  protein.moveBy(-center)
  size_ang = (size - 1) / 2.
  center = np.mean(ligand.get('coords'), axis=0)
  ex_min = center - size_ang
  ex_max = center + size_ang
  x = np.linspace(ex_min[0], ex_max[0], size)
  y = np.linspace(ex_min[1], ex_max[1], size)
  z = np.linspace(ex_min[2], ex_max[2], size)
  position_matrix = np.stack(np.meshgrid(x, y, z, indexing='ij'),axis=-1).reshape((-1,3))
  prot_features = getVoxelDescriptors(protein, usercenters=position_matrix)[0].reshape(3*(size,) + (-1,))
  inh_features = getVoxelDescriptors(ligand, usercenters=position_matrix)[0].reshape(3*(size,) + (-1,))
  final_grid = np.concatenate((prot_features,inh_features), axis=-1)
  return final_grid

def get_files(folder):
  for protein_file in folder.glob('*/*_protein.pdbqt'):
    pdb = protein_file.parent
    try:
      ligand_file = next(pdb.glob('*_ligand.pdbqt'))
    except:
      continue
    yield (pdb.stem, protein_file, ligand_file)

def process_file(params):
  pdb, prot, lig = params
  saving_folder = Path('/cluster/scratch/hhussein/results_pdb2018_htmd')
  saving_path = saving_folder / (prot.name.replace('.pdbqt','.hdf5').replace('protein','complex'))
  #if saving_path.exists():
  #  return True
  try:
    image = build_images(prot, lig, size)
  except Exception as e:
    print(e)
    raise e
    return False
  save_grid(saving_path, pdb, image)
  return True

if __name__ == "__main__":
  size = 25
  saving_folder = Path('/cluster/scratch/hhussein/results_pdb2018_htmd')
  saving_folder.mkdir(parents=True, exist_ok=True)
  #pa = Path('/cluster/scratch/hhussein/pdbbind2018')
  #print(len(list(get_files(pa))))
  #process_file(next(get_files(Path('/cluster/scratch/hhussein/pdbbind2018'))))
  p = Pool(48)
  p.map(process_file, get_files(Path('/cluster/scratch/hhussein/pdbbind2018')))
