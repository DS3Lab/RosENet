import os

source_path = os.path.dirname(os.path.abspath(__file__))
flags_relax_path = os.path.join(source_path, "static", "flags_relax.txt")
metal_selector = "chain Z"
ligand_resname = "WER"
close_ligand_selector = "resname {ligand_resname} and (not (element H or element C)) and within 2.5 of t"
protein_selector = "not resname {ligand_resname}"
mgl_python_path = "/cluster/scratch/hhussein/MGLTools-1.5.6/bin/pythonsh"
preprocess_vina_path = os.path.join(source_path, "preprocess_vina.py")
nonstd2stdresidues = {'HOH':'WAT',
                      'CYX':'CYS',
                      'CYM':'CYS',
                      'HIE':'HIS',
                      'HID':'HIS',
                      'HSD':'HIS',
                      'HIP':'HIS',
                      'TRQ':'TRP',
                      'KCX':'LYS',
                      'LLP':'LYS',
                      'ARN':'ARG',
                      'ASH':'ASP',
                      'GLH':'GLU',
                      'LYN':'LYS',
                      'AR0':'ARG',
                      'HSE':'SER'}
ligand_chid = "X"
water_residue = "WAT"
water_chain = "W"
accepted_metals = ["MN", "MG", "ZN", "CA", "NA"]
metal_chain = "Z"
ligand_selector = f"not protein and same residue as ((resname {water_residue} and within 3 of resname {ligand_resname} and within 3 of protein) or (resname {" ".join(accepted_metals)} and within 5 of resname {ligand_resname}) or resname {ligand_resname})"
