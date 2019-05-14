import Repo.storage.storage as storage
from Repo.objects.pdb import PDBObject
from Repo.objects.file import TFRecordsFile, File
import Repo.settings as settings

class _Dataset:
    _instance_dict = {}
    def __init__(self, path):
        self.path = path
        self.metadata = storage.read_json(self.path / "metadata.json")

    def __getitem__(self, key):
        return PDBObject(self.path / key)

    def list(self):
        return [x.name for x in self.path.iterdir() if x.is_dir() and x.name[0] != "_"]

    @property
    def name(self):
        return f'_{self.path.stem}_{settings.voxelization_type}_{settings.voxelization_fn}_{settings.size}'

    @property
    def tfrecords(self):
        return self.path / self.name
    
    def tfrecord(self, i):
        return TFRecordsFile(f"{i}.tfrecords",self.tfrecords)

    @property
    def images(self):
        return [x for x in (self.path/settings.options).iterdir()]

    @property
    def labels(self):
        return File("labels", self.path)

def DatasetObject(path):
    if str(path.absolute()) not in _Dataset._instance_dict:
        _Dataset._instance_dict[str(path.absolute())] = _Dataset(path)
    return _Dataset._instance_dict[str(path.absolute())]

