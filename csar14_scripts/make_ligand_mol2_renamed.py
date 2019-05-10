import pdb
from pathlib import Path
from multiprocessing import Pool


def read_pdb(pdb_path):
  with pdb_path.open('r') as f:
    lines = f.readlines()
  hetatm = filter(lambda x: x.startswith('HETATM'), lines)
  atom_num_name = map(lambda x: x.split()[1:3], hetatm)
  return dict(atom_num_name)

def read_mol2(mol2_path, name_map):
  with mol2_path.open('r') as f:
    lines = f.readlines()
  mode = "search"
  for i, line in enumerate(lines):
    if mode == "search":
      if line.startswith('@<TRIPOS>ATOM'):
        mode = "rename"
    elif mode == "rename":
      if line.startswith('@<TRIPOS>BOND'):
        mode = "end"
      else:
        atom_num, atom_name = line.split()[0:2]
        new_name = name_map[atom_num].ljust(len(atom_name))
        position = line.find(atom_name)
        end = position + len(new_name)
        new_line = line[0:position] + new_name + line[end:]
        lines[i] = new_line
    elif mode == "end":
      return lines

def process_file(path):
  print(path)
  pdb_code = path.stem
  new_mol2_path = path / f"{pdb_code}_ligand_renamed.mol2"
  try:
    name_map = read_pdb(path / f"{pdb_code}_ligand.pdb")
    with new_mol2_path.open('w') as f:
      f.write("".join(read_mol2(path / f"{pdb_code}_ligand.mol2", name_map)))
  except:
    print(e)

def get_files(path):
  return path.glob('*/')

if __name__ == "__main__":
  p = Pool(48)
  p.map(process_file, get_files(Path('/cluster/scratch/hhussein/CSAR14')))
