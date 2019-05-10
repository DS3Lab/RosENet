#!/cluster/apps/python/3.6.0/x86_64/bin/python3
from prody import parsePDB, writePDB 
from multiprocessing import Pool, cpu_count
from pathlib import Path
import numpy as np
import sys
import string
from htmd.molecule.molecule import Molecule
from htmd.molecule.voxeldescriptors import getVoxelDescriptors
from htmd.builder.preparation import proteinPrepare


def get_files(folder):
  for pdb in folder.glob('*/'):
    protein_pdb = pdb / f'{pdb.stem}_protein.pdb'
    ligand_pdb = pdb / f'{pdb.stem}_ligand.pdb'
    complex_pdb = pdb / f'{pdb.stem}_complex.pdb'
    yield (protein_pdb, ligand_pdb, complex_pdb)

def make_complex_pdb(protein_pdb, ligand_pdb, complex_pdb):
  if complex_pdb.exists():
    print(complex_pdb, " exists")
    return
  protein = parsePDB(str(protein_pdb))
  ligand = parsePDB(str(ligand_pdb))
  p_chains = protein.getChids()
  individual_chains = set(p_chains)
  possible_chains = string.ascii_uppercase.translate(str.maketrans("WXZ","wxz")) + string.digits + string.ascii_lowercase.translate(str.maketrans({"w":"","x":"","z":""}))
  chain_dict = dict(zip(individual_chains, possible_chains[:len(individual_chains)]))
  protein.setChids(np.vectorize(chain_dict.get)(p_chains))
  ligand.setResnames(np.array(['WER']*ligand.numAtoms()))
  ligand.setChids(np.array(['X']*ligand.numAtoms()))
  complex = protein + ligand
  res = complex.getResnames()
  elem = complex.getElements()
  res[res=='HOH'] = 'WAT'
  res[res=='CYX'] = 'CYS'
  res[res=='CYM'] = 'CYS'
  res[res=='HIE'] = 'HIS'
  res[res=='HID'] = 'HIS'
  res[res=='HSD'] = 'HIS'
  res[res=='HIP'] = 'HIS'
  res[res=='TRQ'] = 'TRP'
  res[res=='KCX'] = 'LYS'
  res[res=='LLP'] = 'LYS'
  res[res=='ARN'] = 'ARG'
  res[res=='ASH'] = 'ASP'
  res[res=='GLH'] = 'GLU'
  res[res=='LYN'] = 'LYS'
  res[res=='AR0'] = 'ARG'
  res[res=='HSE'] = 'SER'
  chain = complex.getChids()
  chain[res=="WAT"] = "W"
  for metal in ["MN", "MG", "ZN", "CA", "NA", "V"]:
    res[elem==metal] = metal
    chain[res==metal] = "Z"
  complex.setResnames(res)
  complex.setChids(chain)
  writePDB(str(complex_pdb), complex)
  complex = Molecule(str(complex_pdb))
  prot = complex.copy()
  prot.filter("protein")
  lig = complex.copy()
  lig.filter("not protein and same residue as ((resname WAT and within 3 of resname WER and within 3 of protein) or (resname MN MG ZN CA NA V and within 5 of resname WER) or resname WER)")
  prot = proteinPrepare(prot, pH=7.0)
  mol = Molecule(name="complex")
  mol.append(prot)
  mol.append(lig)
  mol.write(str(complex_pdb))
  complex = parsePDB(str(complex_pdb))
  res = complex.getResnames()
  res[res=='HOH'] = 'WAT'
  res[res=='CYX'] = 'CYS'
  res[res=='CYM'] = 'CYS'
  res[res=='HIE'] = 'HIS'
  res[res=='HID'] = 'HIS'
  res[res=='HSD'] = 'HIS'
  res[res=='HIP'] = 'HIS'
  res[res=='TRQ'] = 'TRP'
  res[res=='KCX'] = 'LYS'
  res[res=='LLP'] = 'LYS'
  res[res=='ARN'] = 'ARG'
  res[res=='ASH'] = 'ASP'
  res[res=='GLH'] = 'GLU'
  res[res=='LYN'] = 'LYS'
  res[res=='AR0'] = 'ARG'
  res[res=='HSE'] = 'SER'
  complex.setResnames(res)
  writePDB(str(complex_pdb), complex)

def process(args):
  try:
    make_complex_pdb(*args)
  except Exception as e:
    print(e)
    return False
  return True

def params(root,pdb):
  protein_pdb = root/ pdb / (pdb+'_protein.pdb')
  ligand_pdb = root/ pdb / (pdb+'_ligand.pdb')
  complex_pdb = root/ pdb / (pdb+'_complex.pdb')
  return protein_pdb, ligand_pdb, complex_pdb

if __name__ == "__main__":
  parent_folder = Path('/cluster/scratch/hhussein/NMR')
  #make_complex_pdb(*params(parent_folder, str(sys.argv[1])))
  if len(sys.argv) > 1:
    process(params(parent_folder,sys.argv[1]))
  else:
    p = Pool(cpu_count())
    p.map(process, get_files(parent_folder))
