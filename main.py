from config import Config
import argparse
from pathlib import Path
from protein import Protein

REQUIRED_OPTIONS = [('--pdb_name', 'pdb_name'),
                    ('--config', 'cfg')]

parser = argparse.ArgumentParser(usage='%(prog)s [A | [[B | C] ? D] ? E]')
parser.add_argument('--build-config', dest='build_cfg')
parser.add_argument('-p', '--pdb_name', dest='pdb_name')
parser.add_argument('-a', '--all', dest='all', action='store_true')
parser.add_argument('-c', '--config', dest='cfg')
parser.add_argument('-i', '--interpolation', dest='interpolation')
parser.add_argument('-P', '--parallel', dest='parallel', action='store_true')


def process_protein(pdb_folder, interpolation, parallel):
    (pdb_folder / 'images').mkdir(exist_ok=True)
    protein = Protein(pdb_folder)
    protein.compute_grids(interpolation, parallel)

if __name__ == "__main__":
    args = parser.parse_args()
    if args.build_cfg:
        Config.save_default_config(args.build_cfg)
        exit(0)
    cfg_path = args.cfg
    interpolation = args.interpolation
    parallel = args.parallel
    Config.load_config(cfg_path)
    root_folder = Path(Config.config['Path']['ProteinFolder'])
    if args.all:
        proteins = [x for x in root_folder.iterdir() if x.is_dir()]
    else:
        protein_folder = root_folder / args.pdb_name
        if not protein_folder.exists():
            raise FileNotFoundError()
        proteins = [protein_folder]

    for protein in proteins:
        process_protein(protein, interpolation, parallel)
