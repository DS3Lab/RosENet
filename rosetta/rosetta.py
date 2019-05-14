import subprocess
from collections import OrderedDict
import Repo.constants as constants
from io import StringIO
import pandas as pd


def molfile_to_params(input_path, output_path, working_directory):
	print(input_path, output_path, working_directory)
	subprocess.run(["python2",
					constants.rosetta.molfile_to_params,
			        "-n", constants.ligand_resname,
					"-p", output_path,
					"--conformers-in-one-file",
					"--keep-names",
					"--clobber",
					input_path],
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
	scores = StringIO(scores_text)
	csv = pd.read_csv(scores, header=1, sep=r"\s*", usecols=['total_score', 'description'])
	csv.sort_values("total_score",  inplace=True)
	return OrderedDict(zip([name.split("_")[-1] for name in csv.description], csv.total_score))

