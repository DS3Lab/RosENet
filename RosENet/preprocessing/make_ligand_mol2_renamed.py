import RosENet.storage.storage as storage
from RosENet.preprocessing.step import Step
from RosENet.preprocessing.make_ligand_params_pdb import MakeLigandParamsPDB

def read_pdb(pdb_path):
    """Read .pdb file and relate atom numbers to their names

    pdb_path : pathlib.Path
        Path of the pdb file
    """
    lines = storage.read_plain(pdb_path).splitlines()
    hetatm = filter(lambda x: x.startswith('HETATM'), lines)
    atom_num_name = map(lambda x: x.split()[1:3], hetatm)
    return dict(atom_num_name)

def read_mol2(mol2_path, name_map):
    """Read .mol2 file and change names to the original .pdb names

    mol2_path : pathlib.Path
        Path to the mol2 file
    name_map : dict
        Atom number to name dictionary
    """
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
        """List of files being created

        pdb_object : PDBObject
            PDB structure being handled
        """
        return [pdb_object.ligand.renamed_mol2]

    @classmethod
    def _run(cls, pdb_object):
        """Inner function for the preprocessing step.

        pdb_object : PDBObject
            PDB structure being handled
        """
        ligand_pdb_path = pdb_object.ligand.pdb.path
        ligand_mol2_path = pdb_object.ligand.mol2.path
        output_path = pdb_object.ligand.renamed_mol2.path
        name_map = read_pdb(ligand_pdb_path)
        storage.write_plain(output_path, read_mol2(ligand_mol2_path, name_map))
