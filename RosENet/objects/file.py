from RosENet.storage.storage import *
from RosENet.objects.pdb import PDBObject
import RosENet.storage.storage as storage
import RosENet.rosetta.rosetta as rosetta

class File:
    """Base class for file management. Represents any file, which name may be 
    generic. It allows for read/write access and templates the name of the file
    according to the PDB code(root folder name) and the number of the file (for
    when it represents the result of the Rosetta minimization)"""
    def __init__(self, name, root):
        self.root = root
        self.code = root.name
        self.name = name.format(code=self.code, number="{number}")
        if "{number}" in name:
            self.multiple = True
        else:
            self.multiple = None

    @property
    def path(self):
        return self.resolve_path()

    def resolve_path(self, number=None):
        if number:
            return self.root / self.name.format(number=number)
        else:
            if self.multiple is True:
                scores = rosetta.parse_scores(PDBObject(self.root).minimized.scores.read())
                number = (list(scores.keys()))[0].split("_")[-1]
                self.multiple = self.name.format(number=number)
                return self.root / self.multiple
            elif self.multiple:
                return self.root / self.multiple
            else:
                return self.root / self.name
    
    def read(self):
        return storage.read_plain(self.path)

    def write(self, data):
        return storage.write_plain(self.path, data)
    
    def delete(self):
        return storage.delete(self.path)

    def __getitem__(self, key):
        if self.multiple:
            return File.create(self.name.format(number=key), self.root)
        else:
            return self

    @staticmethod
    def create(path, root):
        if ".pdbqt" in path:
            return PDBQTFile(path, root)
        elif ".pdb" in path:
            return PDBFile(path, root)
        elif ".img"  in path:
            return ImageFile(path, root)
        elif ".attr"  in path:
            return AttributeFile(path, root)
        elif ".tfrecords"  in path:
            return TFRecordsFile(path, root)
        else:
            return File(path, root)


class PDBFile(File):
    def read(self):
        return read_pdb(self.path)

    def write(self, data):
        write_pdb(self.path, data)


class TFRecordsFile(File):
    def read(self):
        return read_tfrecords(self.path)

    def write(self, data):
        write_tfrecords(self.path, data)

class ImageFile(File):
    def read(self):
        return read_image(self.path)

    def write(self, data):
        write_image(self.path, data)

class AttributeFile(File):
    def read(self):
        return read_attributes(self.path)

    def write(self, data):
        write_attributes(self.path, data)

class PDBQTFile(File):
    def read(self):
        return read_pdb(self.resolve_path())

    def write(self, data):
        write_pdb(self.resolve_path(), data)
