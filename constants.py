"""Constants file. Here one only needs to change the location of the different 
tools used by the project.
"""

import os
from types import SimpleNamespace
from pathlib import Path

source_path = os.path.dirname(os.path.abspath(__file__))
flags_filename = "flags_relax.txt"
flags_relax_path = os.path.join(source_path, "static", flags_filename)
relax_filename = "dock_relax.xml"
relax_path = os.path.join(source_path, "static", relax_filename)
metal_selector = "chain Z"
ligand_resname = "WER"
close_ligand_selector = f"resname {ligand_resname} and (not (element H or element C)) and within 2.5 of t"
protein_selector = f"not resname {ligand_resname}"
mgl_python_path = "/cluster/scratch/hhussein/MGLTools-1.5.6/bin/pythonsh"
preprocess_vina_path = os.path.join(source_path, "preprocessing", "preprocess_vina.py")
nonstd2stdresidues = {'HOH':'WAT',
                      'CYX':'CYS',
                      'CYM':'CYS',
                      'HIE':'HIS',
                      'HID':'HIS',
                      'HSD':'HIS',
                      'HIP':'HIS',
                      'HIY':'HIS',
                      'ALB':'ALA',
                      'ASM':'ASN',
                      'DIC':'ASP',
                      'GLV':'GLU',
					  'GLO':'GLN',
                      'HIZ':'HIS',
                      'LEV':'LEU',
                      'SEM':'SER',
                      'TYM':'TYR',
                      'TRQ':'TRP',
                      'KCX':'LYS',
                      'LLP':'LYS',
                      'ARN':'ARG',
                      'ASH':'ASP',
                      'DID':'ASP',
					  'ASZ':'ASP',
					  'CYT':'CYS',
                      'GLH':'GLU',
                      'LYN':'LYS',
                      'AR0':'ARG',
                      'PCA':'GLU',
                      'HSE':'SER'}
ligand_chid = "X"
water_residue = "WAT"
water_chain = "W"
accepted_metals = ["MN", "MG", "ZN", "CA", "NA"]
metal_chain = "Z"
ligand_selector = f"not protein and same residue as ((resname {water_residue} and within 3 of resname {ligand_resname} and within 3 of protein) or (resname {' '.join(accepted_metals)} and within 5 of resname {ligand_resname}) or resname {ligand_resname})"

class classproperty(object):
    def __init__(self, getter):
        self.getter = getter
    def __get__(self, instance, owner):
        return self.getter(owner)


class rosetta:
    root = Path("/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle")

    @classproperty
    def molfile_to_params(cls):
        return cls.root / "main/source/scripts/python/public/molfile_to_params.py"

    @classproperty
    def minimize(cls):
        return cls.root / "main/source/bin/rosetta_scripts.static.linuxgccrelease"

    @classproperty
    def pdb_to_molfile(cls):
        return cls.root / "main/source/src/apps/public/ligand_docking/pdb_to_molfile.py"

    @classproperty
    def database(cls):
        return cls.root / "main/database/"
    
    @classproperty
    def py_wd(cls):
        return cls.root / "main/source/scripts/python/public/"
