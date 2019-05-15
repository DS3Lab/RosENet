import DrugDiscovery.storage.storage as storage
from DrugDiscovery.preprocessing.step import Step
from DrugDiscovery.preprocessing.make_ligand_params_pdb import MakeLigandParamsPDB

def read_pdb(pdb_path):
    lines = storage.read_plain(pdb_path).splitlines()
    hetatm = filter(lambda x: x.startswith('HETATM'), lines)
    atom_num_name = map(lambda x: x.split()[1:3], hetatm)
    return dict(atom_num_name)

def read_mol2(mol2_path, name_map):
    lines = storage.read_plain(mol2_path).splitlines()
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

class MakeLigandMOL2Renamed(metaclass=Step,requirements=[MakeLigandParamsPDB]):
    @classmethod
    def files(cls, pdb_object):
        return [pdb_object.ligand.renamed_mol2]

    @classmethod
    def _run(cls, pdb_object):
        ligand_pdb_path = pdb_object.ligand.pdb.path
        ligand_mol2_path = pdb_object.ligand.mol2.path
        output_path = pdb_object.ligand.renamed_mol2.path
        name_map = read_pdb(ligand_pdb_path)
        storage.write_plain(output_path, read_mol2(ligand_mol2_path, name_map))
