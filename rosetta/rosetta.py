""" Module wrapping the function calls to the Rosetta Commons software
"""

import subprocess
from collections import OrderedDict
import DrugDiscovery.constants as constants
from io import StringIO
import pandas as pd


def molfile_to_params(input_path, output_path, working_directory):
    new_env = os.environ.copy()
    # This should solve the relative import problem in Rosetta's script
    new_env["PYTHONPATH"] = f"{constants.rosetta.root}/main/source/scripts/python/public:{new_env.get('PYTHONPATH','')}"
    subprocess.run(["python2",
        constants.rosetta.molfile_to_params,
        "-n", constants.ligand_resname,
        "-p", output_path,
        "--conformers-in-one-file",
        "--keep-names",
        "--clobber",
        input_path],
        env=new_env,
        cwd=str(working_directory))

def minimize(working_directory):
    subprocess.run([constants.rosetta.minimize,
        f"@{constants.flags_filename}",
        f"-parser:protocol",
        f'"{constants.relax_path}"',
        "-database", constants.rosetta.database],
        cwd=str(working_directory))

def pdb_to_molfile(mol, complex_path, output_path):
    subprocess.run(" ".join(["python2",
        str(constants.rosetta.pdb_to_molfile),
        str(mol),
        str(complex_path),
        ">",
        str(output_path)]),
        cwd=str(constants.rosetta.py_wd),
        shell=True)

def parse_scores(scores_text):
    """Parse a score.sc file to a dictionary of id to score value ordered in increasing order.

    scores_text : string
        Content of the score.sc file
    """
    scores = StringIO(scores_text)
    csv = pd.read_csv(scores, header=1, sep=r"\s*", usecols=['total_score', 'description'])
    csv.sort_values("total_score",  inplace=True)
    return OrderedDict(zip([name.split("_")[-1] for name in csv.description], csv.total_score))

