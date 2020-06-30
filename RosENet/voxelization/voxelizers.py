import numpy as np
from htmd.molecule.molecule import Molecule
from htmd.molecule.voxeldescriptors import getVoxelDescriptors
from operator import itemgetter
from itertools import compress
from prody import parsePDB, calcCenter, moveAtoms
from mendeleev import element
from types import SimpleNamespace
from RosENet.preprocessing.make_pdbqt import MakePDBQT
from RosENet.preprocessing.compute_rosetta_energy import ComputeRosettaEnergy
from .utils import *
from .filter import voxel_filter
from .interpolation import voxel_interpolation



class Voxelizer:
    """Voxelizer abstract class.
    Voxelizers implement the algorithms that generate 3D voxelized images of
    structural attributes.

    Parameters
    ----------
    size : int
        Size of each side of the 3D image, represented as a cube of voxels.

    Attributes
    ----------
    size : int
        Size of each side of the 3D image, represented as a cube of voxels.
    protein : SimpleNamespace
        Storage object for protein-specific values used during computation and
        protein-specific images.
    ligand : SimpleNamespace
        Storage object for ligand-specific values used during computation and
        ligand-specific images.
    image : numpy.ndarray
        3D image of the structure obtained as a result of the voxelization.
        
    """

    def __init__(self, size):
        self.protein = type('', (), {})
        self.ligand = type('', (), {})
        self.image = None
        self.size = size

    def voxelize(self):
        """Compute the voxelized 3D image and store it in self.image"""
        pass


class PointwiseVoxelizer(Voxelizer):
    """Base voxelizer class implementing the methods to generate 3D images given
    pointwise-values assigned to each atom.
    
    See Also
    --------
    RosettaVoxelizer : Voxelizer for the Rosetta energy-function features.
    ElectronegativityVoxelizer : Voxelizer for the electronegativity features.

    Parameters
    ----------
    complex_path : str or os.PathLike
        Path to the complex structure, a .pdb file.
    size : int
        Size of each side of the 3D image, represented as a cube of voxels.
    method_type : str
        Name of the method to voxelize the pointwise-values. Accepted values are
        "filter" or "interpolation".
    method_fn : str or callable
        If method_type == "filter", a function handle with two parameters that
        implements the filter to be applied. If method_type == "interpolation",
        a string or function handle suitable for scipy.interpolate.Rbf's
        function.
    """

    def __init__(self, complex_path, data_object, size, method_type, method_fn):
        super(PointwiseVoxelizer, self).__init__(size)
        self.path = str(complex_path)
        self.data_object = data_object
        self.method_type = method_type
        self.method_fn = method_fn

    def _prepare_points(self):
        """Load structures and compute the location of the points of the
        3D image to be generated.
        """
        self.complex = parsePDB(self.path)
        protein = self.complex.select("not (resname WER or water)")
        ligand = self.complex.select("resname WER")
        center = calcCenter(ligand.getCoords())
        moveAtoms(self.complex, by=-center)
        center = calcCenter(self.complex.select("resname WER").getCoords())
        self.protein.structure = protein
        self.ligand.structure = ligand
        self.points = grid_around(center, self.size, spacing=24/(self.size-1))

    def _load_attributes(self):
        """Load the computed energies, radii and charges for the atoms in the
        complex. These may not include all atoms, but only the ones around 20 A
        around the center of mass of the ligand."""
        data = self.data_object.read()
        self.radii = dict(zip(data['rc_keys'], data['radius_values']))
        self.charges = dict(zip(data['rc_keys'], data['charge_values']))
        self.energies = data['energy_values'].squeeze()
        self.energy_keys = data['energy_keys']
        self.energy_dict = dict(zip(self.energy_keys, self.energies))

    def _apply_filter(self):
        """Apply the filter to generate the voxelized images, for both protein 
        and ligand separately."""
        self.protein.image = voxel_filter(
            self.method_fn, self.protein, self.points)\
                    .reshape(3*(self.size,) + (-1,))
        self.ligand.image = voxel_filter(
                self.method_fn, self.ligand,  self.points)\
                    .reshape(3*(self.size,) + (-1,))

    def _apply_interpolation(self):
        """Apply the interpolation method to generate the voxelized images, for
        both protein and ligand separately."""
        self.protein.image = voxel_interpolation(
            self.method_fn, self.protein, self.points)\
                    .reshape(3*(self.size,) + (-1,))
        self.ligand.image = voxel_interpolation(
            self.method_fn, self.ligand,  self.points)\
                    .reshape(3*(self.size,) + (-1,))

    def _prepare_attributes(self, obj):
        """Special method for loading and masking the atom coordinates, names,
        radii and charges, masking the selection to only the atoms that have
        energies computed.

        Notes
        -----

        This method is only used to load the attributes of self.protein
        and self.ligand.

        Parameters
        ----------
        obj : SimpleNamespace
        """
        try:
            obj.keys = get_keys(obj.structure)
            obj.atoms_in_scope = [x in self.energy_keys for x in obj.keys]
            obj.coordinates = np.compress(obj.atoms_in_scope, obj.structure.getCoords(), axis=0).reshape((-1, 3))
            obj.keys = list(compress(obj.keys, obj.atoms_in_scope))
            obj.radii = np.array(itemgetter(*obj.keys)
                                 (self.radii)).reshape((-1, 1))
            obj.charges = np.array(itemgetter(*obj.keys)
                                   (self.charges)).reshape((-1, 1))
        except Exception as e:
            print(self.path)
            print("#"*81)
            raise e

    def _prepare_values(self):
        """Voxelizer specific value loading."""
        pass

    def _normalize(self):
        """Voxelizer specific after-voxelization normalization."""
        pass

    def _merge(self):
        """Merges protein and ligand 3D images into the resulting self.image."""
        self.image = np.concatenate(
            (self.protein.image, self.ligand.image), axis=-1)

    def voxelize(self):
        """Main voxelization method, overrides Voxelizer's voxelize method.
        Implements the steps to perform a pointwise-valued voxelization."""
        self._load_attributes()
        self._prepare_points()
        self._prepare_attributes(self.protein)
        self._prepare_attributes(self.ligand)
        self._prepare_values()
        if self.method_type == "filter":
            self._apply_filter()
        elif self.method_type == "interpolation":
            self._apply_interpolation()
        self._normalize()
        self._merge()

class ElectronegativityVoxelizer(PointwiseVoxelizer):
    """Voxelizer class to generate 3D images given per-atom electronegativity
    values.
    
    See Also
    --------
    RosettaVoxelizer : Voxelizer for the Rosetta energy-function features.
    PointwiseVoxelizer : Base voxelizer for pointwise features.
    """
    def _prepare_values(self):
        """Sets up the electronegativities as values for the voxelization,
        for both protein and ligand."""
        elements = set(self.complex.getElements())
        el_dict = {name: element(
            name.capitalize()).en_pauling for name in elements}
        self.protein.values = np.array(list(compress((el_dict[name] for name in self.protein.structure.getElements()), self.protein.atoms_in_scope)))\
                .reshape((-1, 1))
        self.ligand.values = np.array(list(compress([el_dict[name] for name in self.ligand.structure.getElements()], self.ligand.atoms_in_scope)))\
				.reshape((-1, 1))


    def _normalize(self):
        """Normalizes the electronegativities by dividing by the highest values
        in the protein's and ligand's electronegativies."""
        self.protein.image = self.protein.image / 3.44
        self.ligand.image = self.ligand.image / 3.98


class RosettaVoxelizer(PointwiseVoxelizer):
    """Voxelizer class to generate 3D images given per-atom Rosetta
    energy-function values.
    
    See Also
    --------
    ElectronegativityVoxelizer : Voxelizer for electronegativity features.
    PointwiseVoxelizer : Base voxelizer for pointwise features.
    """
    def _prepare_values(self):
        """Prepare energy values for voxelization"""
        self.protein.values = np.array(itemgetter(
            *self.protein.keys)(self.energy_dict)).reshape((-1, 4))
        self.ligand.values = np.array(itemgetter(
            *self.ligand.keys)(self.energy_dict)).reshape((-1, 4))

    def _normalize(self):
        """Normalize the energy maps to 0-1 range and split positive and
        negative maps."""
        protein_limits = [-2.27475644, 4.11150004e+02,
                          4.01129569e+00,  1.28136470e+00,
                          -0.37756078, -3.79981632]
        ligand_limits = [-1.7244696, 0.59311066,  2.67294434,
                         0.40072521, -0.44943017, -2.00621753]
        self.protein.image = np.concatenate((self.protein.image,
                                             self.protein.image[...,2:]),axis=-1)
        self.ligand.image = np.concatenate((self.ligand.image,
                                             self.ligand.image[...,2:]),axis=-1)
        self.protein.image = clip(self.protein.image, protein_limits)
        self.ligand.image = clip(self.ligand.image, ligand_limits)


class HTMDVoxelizer(Voxelizer):
    """Base voxelizer class implementing the methods to generate 3D images given
    pointwise-values assigned to each atom.
    
    Parameters
    ----------
    protein_path : str or os.PathLike
        Path to the protein structure, a .pdb file.
    ligand_path : str or os.PathLike
        Path to the ligand structure, a .pdb file.
    size : int
        Size of each side of the 3D image, represented as a cube of voxels.
    """
    def __init__(self, protein_path, ligand_path, size):
        super(HTMDVoxelizer, self).__init__(size)
        self.protein.path = protein_path
        self.ligand.path = ligand_path

    def _prepare_points(self):
        """Load structures and compute the location of the points of the
        3D image to be generated.
        """
        protein = Molecule(str(self.protein.path))
        ligand = Molecule(str(self.ligand.path))
        protein.filter(
            'not (water or name CO or name NI or name CU or name NA)')
        center = np.mean(ligand.get('coords'), axis=0)
        ligand.moveBy(-center)
        protein.moveBy(-center)
        center = np.mean(ligand.get('coords'), axis=0)
        self.protein.structure = protein
        self.ligand.structure = ligand
        self.points = grid_around(center, self.size, spacing=24/(self.size-1)).reshape((-1,3))


    def voxelize(self):
        """Compute the voxelized 3D image and store it in self.image"""
        self._prepare_points()
        self.protein.image = getVoxelDescriptors(
            self.protein.structure, usercenters=self.points)[0]\
                    .reshape(3*(self.size,) + (-1,))
        self.ligand.image = getVoxelDescriptors(
            self.ligand.structure, usercenters=self.points)[0]\
                    .reshape(3*(self.size,) + (-1,))
        self.image = np.concatenate((self.protein.image, self.ligand.image), axis=-1)

def VoxelizeRosetta(pdb_object, method, size):
    """Wrapper function for voxelizing and storing Rosetta features.

    pdb_object : PDBObject
        PDB structure to voxelize.
    method : tuple of (string, string or callable)
        Voxelization method and function. See underlying function for more information.
    size : int
        Size of voxel cube side.
    """
    if not ComputeRosettaEnergy.computed(pdb_object):
        return False
    complex_path = pdb_object.minimized.complex.pdb.path
    data_object = pdb_object.minimized.complex.attr
    output_path = pdb_object.image.rosetta.path
    if output_path.exists():
        return True
    method_type, method_fn = method
    voxelizer = RosettaVoxelizer(complex_path, data_object, size, method_type, method_fn)
    voxelizer.voxelize()
    pdb_object.image.rosetta.write(voxelizer.image)
    return True

def VoxelizeElectronegativity(pdb_object, method, size):
    """Wrapper function for voxelizing and storing electronegativity features.

    pdb_object : PDBObject
        PDB structure to voxelize.
    method : tuple of (string, string or callable)
        Voxelization method and function. See underlying function for more information.
    size : int
        Size of voxel cube side.
    """
    if not ComputeRosettaEnergy.computed(pdb_object):
        return False
    complex_path = pdb_object.minimized.complex.pdb.path
    data_object = pdb_object.minimized.complex.attr
    output_path = pdb_object.image.electronegativity.path
    if output_path.exists():
        return True
    method_type, method_fn = method
    voxelizer = ElectronegativityVoxelizer(complex_path, data_object, size, method_type, method_fn)
    voxelizer.voxelize()
    pdb_object.image.electronegativity.write(voxelizer.image)

def VoxelizeHTMD(pdb_object, size):
    """Wrapper function for voxelizing and storing HTMD features.

    pdb_object : PDBObject
        PDB structure to voxelize.
    size : int
        Size of voxel cube side.
    """
    if not MakePDBQT.computed(pdb_object):
        return False
    protein_path = pdb_object.minimized.protein.pdbqt.path
    ligand_path = pdb_object.minimized.ligand.pdbqt.path
    output_path = pdb_object.image.htmd.path
    if output_path.exists():
        return True
    voxelizer = HTMDVoxelizer(protein_path, ligand_path, size)
    voxelizer.voxelize()
    pdb_object.image.htmd.write(voxelizer.image)
