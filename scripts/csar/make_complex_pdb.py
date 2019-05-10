#!/cluster/apps/python/3.6.0/x86_64/bin/python3
from prody import parsePDB, writePDB 
from multiprocessing import Pool
from pathlib import Path
import numpy as np

def get_files(folder):
  for pdb in folder.glob('*/*/'):
    protein_pdb = pdb / f'{pdb.stem}_protein.pdb'
    ligand_pdb = pdb / f'{pdb.stem}_ligand.pdb'
    complex_pdb = pdb / f'{pdb.stem}_complex.pdb'
    yield (protein_pdb, ligand_pdb, complex_pdb)

def make_complex_pdb(protein_pdb, ligand_pdb, complex_pdb):
  print(protein_pdb)
  protein = parsePDB(str(protein_pdb))
  ligand = parsePDB(str(ligand_pdb))
  prot_res = protein.getResnames()
  prot_res[prot_res=='CYX'] = 'CYS'
  prot_res[prot_res=='CYM'] = 'CYS'
  prot_res[prot_res=='HIE'] = 'HIS'
  prot_res[prot_res=='HID'] = 'HIS'
  prot_res[prot_res=='HIP'] = 'HIS'
  prot_res[prot_res=='TRQ'] = 'TRP'
  prot_res[prot_res=='KCX'] = 'LYS'
  prot_res[prot_res=='LLP'] = 'LYS'
  protein.setResnames(prot_res)
  ligand.setResnames(np.array(['WER']*ligand.numAtoms()))
  complex = protein + ligand
  writePDB(str(complex_pdb), complex)

def process(args):
  try:
    make_complex_pdb(*args)
  except Exception as e:
    print(e)
    return False
  return True

if __name__ == "__main__":
  parent_folder = Path('/cluster/scratch/hhussein/Structures')
 #protein_pdb = parent_folder/ '10gs' / '10gs_protein.pdb'
 #ligand_pdb = parent_folder/ '10gs' / '10gs_ligand.pdb'
 #complex_pdb = parent_folder/ '10gs' / '10gs_complex.pdb'
 #make_complex_pdb(protein_pdb,ligand_pdb,complex_pdb)
  p = Pool(48)
  p.map(process, get_files(parent_folder))
