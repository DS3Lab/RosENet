from types import SimpleNamespace
from DrugDiscovery.storage.storage import *
import DrugDiscovery.storage.storage as storage
import DrugDiscovery.rosetta.rosetta as rosetta
from DrugDiscovery import settings

class _PDB:
    """Inner PDB class. Represents a PDB structure (a folder with a protein.pdb and ligand.mol2 files)."""
    
    _instance_dict = {}
    _property_tree = { "flags_relax" : "flags_relax.txt",
        "constraints" : "constraints",
        "ligand" : {
            "pdb" : "{code}_ligand.pdb",
            "mol2" : "{code}_ligand.mol2",
            "renamed_mol2" : "{code}_ligand_renamed.mol2",
            "pdbqt" : "{code}_ligand.pdbqt",
            "params" : "{code}_ligand.params"
            },
        "protein" : {
            "pdb" : "{code}_protein.pdb",
            "pdbqt" : "{code}_protein.pdbqt"
            },
        "complex" : {
            "pdb" : "{code}_complex.pdb"
            },
        "minimized" : {
            "scores" : "score.sc",
            "hidden_complexes" : "other_complexes",
            "ligand" : {
                "mol2" : "{code}_ligand_{number}.mol2",
                "pdbqt": "{code}_ligand_{number}.pdbqt"
                },
            "protein" : {
                "pdb" : "{code}_protein_{number}.pdb",
                "mol2" : "{code}_protein_{number}.mol2",
                "pdbqt": "{code}_protein_{number}.pdbqt"
                },
            "complex" : {
                "pdb": "{code}_complex_{number}.pdb",
                "pdbqt": "{code}_complex_{number}.pdbqt",
                "attr": "{code}_complex_{number}.attr"
                }
            },
        "image" : {
                "rosetta" : "{code}_rosetta.img",
                "htmd" : "{code}_htmd.img",
                "electronegativity" : "{code}_electroneg.img"
            }
        }

    def __init__(self, path):
        self.path = path
        self.id = path.name
        self.metadata_path = path / "metadata.json"
        if not self.metadata_path.exists():
            storage.write_json(self.metadata_path, { "completed_steps" : []})
        self.metadata = storage.read_json(self.metadata_path)
        _create(_PDB._property_tree, path, self.__dict__)
        self.image.combined = File.create(f"{self.id}.img", path.parent / settings.options)

    @property
    def completed_steps(self):
        return self.metadata["completed_steps"]

    def complete(self, step):
        self.metadata["completed_steps"].append(step)
        self.metadata["completed_steps"] = list(set(self.metadata["completed_steps"]))
        storage.write_json(self.metadata_path, self.metadata)
    
    def uncomplete(self, step):
        try:
            self.metadata["completed_steps"].remove(step)
            storage.write_json(self.metadata_path, self.metadata)
        except ValueError:
            pass

def PDBObject(path):
    if str(path.absolute()) not in _PDB._instance_dict:
        _PDB._instance_dict[str(path.absolute())] = _PDB(path)
    return _PDB._instance_dict[str(path.absolute())]

def _create(tree, path, result=None):
    from DrugDiscovery.objects.file import File
    root = True
    if not result:
        root = False
        result = {}
    for key, value in tree.items():
        if isinstance(value, dict):
            result[key] = _create(value, path)
        else:
            result[key] = File.create(value, path)
    if root:
        return result
    return SimpleNamespace(**result)

