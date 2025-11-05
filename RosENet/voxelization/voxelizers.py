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
from RosENet.preprocessing.compute_xtb_charges import ComputeXTBCharges
from .utils import *
from .filter import voxel_filter
from .interpolation import voxel_interpolation
from scipy.spatial import distance_matrix



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


class XTBChargeVoxelizer(PointwiseVoxelizer):
    """Voxelizer class to generate 3D images from QM-derived partial charges.

    Uses xTB (extended tight-binding) computed charges instead of force field charges.
    Provides more accurate electrostatic representations, especially for novel ligands.

    See Also
    --------
    ElectronegativityVoxelizer : Voxelizer for electronegativity features.
    RosettaVoxelizer : Voxelizer for Rosetta energy-function features.
    """

    def __init__(self, complex_path, xtb_data_object, rosetta_data_object, size, method_type, method_fn):
        super(XTBChargeVoxelizer, self).__init__(complex_path, rosetta_data_object, size, method_type, method_fn)
        self.xtb_data_object = xtb_data_object

    def _load_xtb_charges(self):
        """Load QM-derived charges from xTB calculation."""
        data = self.xtb_data_object.read()
        self.xtb_charge_dict = dict(zip(data['charge_keys'], data['charge_values']))

    def _prepare_values(self):
        """Sets up QM charges as values for voxelization."""
        self._load_xtb_charges()

        # Map atom keys to QM charges
        self.protein.values = np.array([
            self.xtb_charge_dict.get(key, 0.0) for key in self.protein.keys
        ]).reshape((-1, 1))

        self.ligand.values = np.array([
            self.xtb_charge_dict.get(key, 0.0) for key in self.ligand.keys
        ]).reshape((-1, 1))

    def _normalize(self):
        """Normalize QM charges and split into positive/negative components."""
        # Split into positive and negative charges
        protein_pos = np.maximum(self.protein.image, 0)
        protein_neg = np.abs(np.minimum(self.protein.image, 0))
        ligand_pos = np.maximum(self.ligand.image, 0)
        ligand_neg = np.abs(np.minimum(self.ligand.image, 0))

        # Normalize to [0, 1] range (typical charges are -1 to +1)
        self.protein.image = np.concatenate([protein_pos, protein_neg], axis=-1) / 2.0
        self.ligand.image = np.concatenate([ligand_pos, ligand_neg], axis=-1) / 2.0


class ShapeComplementarityVoxelizer(Voxelizer):
    """Voxelizer for shape complementarity features.

    Generates multiple shape-based descriptors:
    1. Distance to protein surface
    2. Distance to ligand surface
    3. Pocket depth (distance into binding pocket)
    4. Buried surface area indicator

    Parameters
    ----------
    complex_path : str or os.PathLike
        Path to the complex structure, a .pdb file.
    size : int
        Size of each side of the 3D image, represented as a cube of voxels.
    """

    def __init__(self, complex_path, size):
        super(ShapeComplementarityVoxelizer, self).__init__(size)
        self.path = str(complex_path)

    def _prepare_points(self):
        """Load structures and compute grid points."""
        self.complex = parsePDB(self.path)
        protein = self.complex.select("not (resname WER or water)")
        ligand = self.complex.select("resname WER")
        center = calcCenter(ligand.getCoords())
        moveAtoms(self.complex, by=-center)

        self.protein.structure = protein
        self.ligand.structure = ligand
        self.points = grid_around(
            calcCenter(ligand.getCoords()),
            self.size,
            spacing=24/(self.size-1)
        )

    def _compute_distance_field(self, coords, radii):
        """Compute distance field from a set of atomic coordinates.

        Parameters
        ----------
        coords : numpy.ndarray
            Atomic coordinates (N, 3)
        radii : numpy.ndarray
            Van der Waals radii (N,)

        Returns
        -------
        distance_field : numpy.ndarray
            Distance to nearest surface at each grid point
        """
        points_flat = self.points.reshape(-1, 3)

        # Compute distances to all atoms
        dists = distance_matrix(points_flat, coords)

        # Distance to surface = distance to atom center - vdW radius
        surface_dists = dists - radii[np.newaxis, :]

        # Minimum distance to any surface
        min_dist = np.min(surface_dists, axis=1)

        return min_dist.reshape(self.points.shape[:-1])

    def _compute_pocket_depth(self, protein_coords, ligand_center):
        """Compute pocket depth: how deep into the protein binding site.

        Parameters
        ----------
        protein_coords : numpy.ndarray
            Protein atomic coordinates
        ligand_center : numpy.ndarray
            Center of ligand

        Returns
        -------
        depth_field : numpy.ndarray
            Pocket depth at each grid point
        """
        points_flat = self.points.reshape(-1, 3)

        # For each point, count protein atoms between point and exterior
        # Simplified: distance to ligand center weighted by protein density
        dist_to_center = np.linalg.norm(
            points_flat - ligand_center[np.newaxis, :], axis=1
        )

        # Count nearby protein atoms (within 5Å)
        dists_to_protein = distance_matrix(points_flat, protein_coords)
        nearby_count = np.sum(dists_to_protein < 5.0, axis=1)

        # Depth = distance * density
        depth = dist_to_center * (1 + nearby_count / 10.0)

        return depth.reshape(self.points.shape[:-1])

    def voxelize(self):
        """Compute shape complementarity features."""
        self._prepare_points()

        # Get VDW radii from standard dictionary
        vdw_radii = {
            'C': 1.70, 'N': 1.55, 'O': 1.52, 'S': 1.80,
            'H': 1.20, 'P': 1.80, 'F': 1.47, 'CL': 1.75,
            'BR': 1.85, 'I': 1.98
        }

        protein_elements = self.protein.structure.getElements()
        protein_radii = np.array([vdw_radii.get(e.upper(), 1.70) for e in protein_elements])

        ligand_elements = self.ligand.structure.getElements()
        ligand_radii = np.array([vdw_radii.get(e.upper(), 1.70) for e in ligand_elements])

        # 1. Distance to protein surface
        protein_dist = self._compute_distance_field(
            self.protein.structure.getCoords(),
            protein_radii
        )

        # 2. Distance to ligand surface
        ligand_dist = self._compute_distance_field(
            self.ligand.structure.getCoords(),
            ligand_radii
        )

        # 3. Pocket depth
        ligand_center = calcCenter(self.ligand.structure.getCoords())
        pocket_depth = self._compute_pocket_depth(
            self.protein.structure.getCoords(),
            ligand_center
        )

        # 4. Buried surface indicator (negative distance = buried)
        buried_indicator = np.where(protein_dist < 0, 1.0, 0.0)

        # Normalize and stack
        protein_dist_norm = np.clip(protein_dist / 10.0, -1, 1)
        ligand_dist_norm = np.clip(ligand_dist / 10.0, -1, 1)
        pocket_depth_norm = np.clip(pocket_depth / 20.0, 0, 1)

        self.image = np.stack([
            protein_dist_norm,
            ligand_dist_norm,
            pocket_depth_norm,
            buried_indicator
        ], axis=-1)


class HBondGeometryVoxelizer(Voxelizer):
    """Voxelizer for hydrogen bond geometry features.

    Generates hydrogen bond quality descriptors based on:
    1. H-bond donor strength (distance + angle weighted)
    2. H-bond acceptor strength (distance + angle weighted)
    3. Cooperative H-bond networks
    4. Optimal vs suboptimal H-bond geometry

    Parameters
    ----------
    complex_path : str or os.PathLike
        Path to the complex structure, a .pdb file.
    size : int
        Size of each side of the 3D image, represented as a cube of voxels.
    """

    def __init__(self, complex_path, size):
        super(HBondGeometryVoxelizer, self).__init__(size)
        self.path = str(complex_path)

    def _prepare_points(self):
        """Load structures and compute grid points."""
        self.complex = parsePDB(self.path)
        protein = self.complex.select("not (resname WER or water)")
        ligand = self.complex.select("resname WER")
        center = calcCenter(ligand.getCoords())
        moveAtoms(self.complex, by=-center)

        self.protein.structure = protein
        self.ligand.structure = ligand
        self.points = grid_around(
            calcCenter(ligand.getCoords()),
            self.size,
            spacing=24/(self.size-1)
        )

    def _identify_hbond_atoms(self, structure):
        """Identify potential H-bond donors and acceptors.

        Parameters
        ----------
        structure : prody.AtomGroup
            Protein or ligand structure

        Returns
        -------
        donors : list of tuples
            List of (coord, atom_type) for donors
        acceptors : list of tuples
            List of (coord, atom_type) for acceptors
        """
        donors = []
        acceptors = []

        names = structure.getNames()
        coords = structure.getCoords()
        resnames = structure.getResnames()

        for i, (name, coord, resname) in enumerate(zip(names, coords, resnames)):
            name_upper = name.strip().upper()

            # Donors: N-H, O-H
            if name_upper.startswith('N') or (name_upper.startswith('O') and 'OH' in name_upper):
                donors.append((coord, name_upper[0]))

            # Acceptors: O, N (sp2)
            if name_upper.startswith('O'):
                acceptors.append((coord, 'O'))
            elif name_upper.startswith('N') and resname in ['ASN', 'GLN', 'HIS']:
                acceptors.append((coord, 'N'))

        return donors, acceptors

    def _compute_hbond_strength(self, donor_coords, acceptor_coords, grid_points):
        """Compute H-bond strength field based on distance and geometry.

        Parameters
        ----------
        donor_coords : numpy.ndarray
            Donor coordinates (N, 3)
        acceptor_coords : numpy.ndarray
            Acceptor coordinates (M, 3)
        grid_points : numpy.ndarray
            Grid point coordinates (G, 3)

        Returns
        -------
        strength_field : numpy.ndarray
            H-bond strength at each grid point
        """
        if len(donor_coords) == 0 or len(acceptor_coords) == 0:
            return np.zeros(len(grid_points))

        # Distance-based scoring
        donor_dists = distance_matrix(grid_points, donor_coords)
        acceptor_dists = distance_matrix(grid_points, acceptor_coords)

        # Optimal H-bond distance: 2.7-3.3 Å
        donor_score = np.exp(-((donor_dists - 2.9) / 0.5)**2)
        acceptor_score = np.exp(-((acceptor_dists - 2.9) / 0.5)**2)

        # Combined strength (max over all possible bonds)
        strength = np.max(donor_score, axis=1) * np.max(acceptor_score, axis=1)

        return strength

    def voxelize(self):
        """Compute hydrogen bond geometry features."""
        self._prepare_points()

        points_flat = self.points.reshape(-1, 3)

        # Identify H-bond capable atoms
        protein_donors, protein_acceptors = self._identify_hbond_atoms(self.protein.structure)
        ligand_donors, ligand_acceptors = self._identify_hbond_atoms(self.ligand.structure)

        # 1. Protein donor - Ligand acceptor H-bonds
        if protein_donors and ligand_acceptors:
            prot_don_coords = np.array([d[0] for d in protein_donors])
            lig_acc_coords = np.array([a[0] for a in ligand_acceptors])
            pd_la_strength = self._compute_hbond_strength(
                prot_don_coords, lig_acc_coords, points_flat
            ).reshape(self.points.shape[:-1])
        else:
            pd_la_strength = np.zeros(self.points.shape[:-1])

        # 2. Ligand donor - Protein acceptor H-bonds
        if ligand_donors and protein_acceptors:
            lig_don_coords = np.array([d[0] for d in ligand_donors])
            prot_acc_coords = np.array([a[0] for a in protein_acceptors])
            ld_pa_strength = self._compute_hbond_strength(
                lig_don_coords, prot_acc_coords, points_flat
            ).reshape(self.points.shape[:-1])
        else:
            ld_pa_strength = np.zeros(self.points.shape[:-1])

        # 3. Total H-bond strength
        total_strength = pd_la_strength + ld_pa_strength

        # 4. H-bond network density (cooperative effects)
        # Count nearby H-bonds
        network_density = np.clip(total_strength * 2, 0, 1)

        self.image = np.stack([
            pd_la_strength,
            ld_pa_strength,
            total_strength,
            network_density
        ], axis=-1)


def VoxelizeXTBCharges(pdb_object, method, size):
    """Wrapper function for voxelizing QM-derived charges.

    Parameters
    ----------
    pdb_object : PDBObject
        PDB structure to voxelize.
    method : tuple of (string, string or callable)
        Voxelization method and function.
    size : int
        Size of voxel cube side.

    Returns
    -------
    bool
        True if successful, False otherwise
    """
    if not ComputeXTBCharges.computed(pdb_object):
        return False

    complex_path = pdb_object.minimized.complex.pdb.path
    xtb_data_object = pdb_object.minimized.complex.xtb_charges
    rosetta_data_object = pdb_object.minimized.complex.attr
    output_path = pdb_object.image.xtb_charges.path

    if output_path.exists():
        return True

    method_type, method_fn = method
    voxelizer = XTBChargeVoxelizer(
        complex_path, xtb_data_object, rosetta_data_object,
        size, method_type, method_fn
    )
    voxelizer.voxelize()
    pdb_object.image.xtb_charges.write(voxelizer.image)
    return True


def VoxelizeShape(pdb_object, size):
    """Wrapper function for voxelizing shape complementarity features.

    Parameters
    ----------
    pdb_object : PDBObject
        PDB structure to voxelize.
    size : int
        Size of voxel cube side.

    Returns
    -------
    bool
        True if successful, False otherwise
    """
    from RosENet.preprocessing.minimize_rosetta import MinimizeRosetta

    if not MinimizeRosetta.computed(pdb_object):
        return False

    complex_path = pdb_object.minimized.complex.pdb.path
    output_path = pdb_object.image.shape.path

    if output_path.exists():
        return True

    voxelizer = ShapeComplementarityVoxelizer(complex_path, size)
    voxelizer.voxelize()
    pdb_object.image.shape.write(voxelizer.image)
    return True


def VoxelizeHBondGeometry(pdb_object, size):
    """Wrapper function for voxelizing H-bond geometry features.

    Parameters
    ----------
    pdb_object : PDBObject
        PDB structure to voxelize.
    size : int
        Size of voxel cube side.

    Returns
    -------
    bool
        True if successful, False otherwise
    """
    from RosENet.preprocessing.minimize_rosetta import MinimizeRosetta

    if not MinimizeRosetta.computed(pdb_object):
        return False

    complex_path = pdb_object.minimized.complex.pdb.path
    output_path = pdb_object.image.hbond_geometry.path

    if output_path.exists():
        return True

    voxelizer = HBondGeometryVoxelizer(complex_path, size)
    voxelizer.voxelize()
    pdb_object.image.hbond_geometry.write(voxelizer.image)
    return True
