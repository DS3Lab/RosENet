class File:
    def __init__(self, name, root):
        self.root = root
        self.code = root.name
        self.name = name.format(code=self.code)
        if "{number}" in path.name:
            self.multiple = True

    def resolve_path(self, number=None):
        if number:
            return self.root / self.name.format(number=number)
        else:
            if self.multiple is True:
                self.multiple = next(self.root.glob(self.name.format(number="*"))).name
            elif self.multiple:
                return self.root / self.multiple
            else:
                return self.root / self.name

    def read(self):
        with self.resolve_path().open("r") as f:
            return f.read()

    def write(self, data):
        with self.resolve_path().open("w") as f:
            return f.write(data)

    def __getitem__(self, key):
        if self.multiple:
            return File.create(self.name.format(number=key), self.root)
        else:
            return self

    @staticmethod
    def create(path):
        if path

class PDBFile(File):
    def read(self):
        return parsePDB(str(self.resolve_path()))

    def write(self, data):
        writePDB(str(self.resolve_path()), data)

class PDBQTFile(File):
    def read(self):
        return parsePDB(str(self.resolve_path()))

    def write(self, data):
        writePDB(str(self.resolve_path()), data)

_property_tree = {
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
        "ligand" : {
            "mol2" : "{code}_ligand_{number}.mol2",
            "pdbqt": "{code}_ligand_{number}.pdbqt"
            },
        "protein" : {
            "mol2" : "{code}_protein_{number}.mol2",
            "pdbqt": "{code}_protein_{number}.pdbqt"
            },
        "complex" : {
            "pdb": "{code}_protein_{number}.pdb",
            "pdbqt": "{code}_protein_{number}.pdbqt",
            "attr": "{code}_protein_{number}.attr"
            }
        }
    }

def PDBObject(path):
    return _create(_property_tree, path)

def _create(tree, path):
        result = {}
        for key, value in tree.iteritems():
            if instanceof(value) is dict:
                result[key] = create(value, path)
            else:
                result[key] = File.create(value, path)
        return SimpleNamespace(**result)

