def read_pdb(pdb_path):
    lines = storage.read_plain(pdb_path)
    hetatm = filter(lambda x: x.startswith('HETATM'), lines)
    atom_num_name = map(lambda x: x.split()[1:3], hetatm)
    return dict(atom_num_name)

def read_mol2(mol2_path, name_map):
    lines = storage.read_plain(mol2_path)
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

def make_ligand_mol2_renamed(ligand_pdb_path, ligand_mol2_path, output_path):
    name_map = read_pdb(ligand_pdb_path)
    storage.write_plain(output_path, read_mol2(ligand_mol2_path, name_map))

