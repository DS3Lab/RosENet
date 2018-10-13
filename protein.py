from pathlib import Path
import re
import sqlite3
from operator import itemgetter
import numpy as np
from prody import parsePDB, calcCenter, parseDCD
from utils import apply_gaussian_filter
import pickle
import itertools
from config import Config
from scipy.interpolate import Rbf
from apbs import APBS
from multiprocessing import Pool
from collections import defaultdict


class Protein:
    def __init__(self, path):
        super(Protein, self).__init__()
        self.path = Path(path)
        self.name = self.path.name
        self.rmsf = None
        self.protein_pdb = None
        self._pdb_path = self.path / f'{self.name}_MD.pdb'
        self._dcd_path = self.path / 'dynamics' / f'{self.name}_MD.dcd'
        self._detect_structures()

    def _detect_structures(self):
        structures_folder = self.path / 'structures'
        self.structures = [ProteinStructure(
            x) for x in structures_folder.iterdir() if x.is_dir()]

    def compute_grids(self, interpolation, parallel=False):
        if self.rmsf is None:
            self._compute_rmsf()
        if parallel:
            rmsf = self.rmsf
            pool = Pool(10)
            r = pool.map_async(func,
                               zip(self.structures,
                                   itertools.repeat(rmsf),
                                   itertools.repeat(interpolation)))
            r.get()

        else:
            for structure in self.structures:
                structure.compute_grids(self.rmsf, interpolation)
                structure.save_grids(interpolation)

    def _compute_rmsf(self):
        self.protein_pdb = parsePDB(self._pdb_path)
        ensemble_dcd = parseDCD(str(self._dcd_path))
        ensemble_dcd.setAtoms(self.protein_pdb)
        ensemble_dcd.setCoords(self.protein_pdb)
        ensemble_dcd.superpose()
        self.atom_res_idxs = self.protein_pdb.getResindices() + 1
        self.atom_names = self.protein_pdb.getNames()
        self.atoms = np.char.add(
            np.char.mod(
                '%d-',
                self.atom_res_idxs),
            self.atom_names)
        self.rmsf = dict(zip(self.atoms, ensemble_dcd.getRMSFs()))


class ProteinStructure:
    def __init__(self, path):
        super(ProteinStructure, self).__init__()
        self.path = path
        self.id = path.name
        self.protein_name = path.parents[1].name
        self._detect_poses()

    def _detect_poses(self):
        self.poses = [ProteinPose(pose_filename) for pose_filename in self.path.glob(
            f'''{self.protein_name}_complex_{self.id}_{'[0-9]' * 4}.pdb''')]

    def compute_grids(self, rmsf, interpolation):
        for pose in self.poses:
            pose.compute_grids(rmsf, interpolation)

    def save_grids(self, interpolation):
        for pose in self.poses:
            pose.save_grids(interpolation)


class ProteinPose:
    _FILENAME_PATTERN = r'([^_]+)_complex_([^_]+)_(\d{4})'

    def __init__(self, pdb_path):
        super(ProteinPose, self).__init__()
        self.grid_size = int(Config.config['Grid Parameters']['GridSize'])
        self.grid_spacing = float(
            Config.config['Grid Parameters']['GridSpacing'])
        self.grid_radius = float(
            Config.config['Grid Parameters']['GridRadius'])
        self.rmsf_window = int(
            np.floor(
                2 *
                self.grid_radius /
                self.grid_spacing))
        self.pdb_path = pdb_path
        self.protein_name, self.structure_id, self.id = re.match(
            ProteinPose._FILENAME_PATTERN, pdb_path.stem).groups()
        self.path = pdb_path.parent
        self.charges_path = self.path / \
            f'{self.protein_name}_charges_{self.id}.db'
        self.radii_path = self.path / f'{self.protein_name}_radii_{self.id}.db'
        self.energies_path = self.path / \
            f'{self.protein_name}_energies_{self.id}.db'
        self.charges = None
        self.radii = None
        self.energies = None
        self.grid = None
        self.energy_pairs = None

    def compute_grids(self, rmsf, interpolation):
        print(f'Computing grids for {self.pdb_path.stem}')
        self.charges = self._import_charges()
        self.radii = self._import_radii()
        self.energies, self.energy_pairs = self._import_energies()
        self.grid = self._build_images(rmsf, interpolation)

    def save_grids(self, interpolation):
        print(f'Saving grids for {self.pdb_path.stem}')
        saving_path = self.path.parents[1] / 'images' / \
            f'{self.protein_name}_{self.structure_id}_{self.id}_{interpolation}.pkl'
        with open(saving_path, 'wb') as output_file:
            pickle.dump(self.grid, output_file, pickle.HIGHEST_PROTOCOL)

    def _import_energies(self):
        """Import connectivity topology from sql database
        This function will initialize connect_topology
        """
        try:
            conn = sqlite3.connect(str(self.energies_path))
        except sqlite3.Error:
            print(
                "Error while connecting to the database " +
                self.energies_path)
            return -1
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM energy")
        data = cursor.fetchall()

        energies = {}
        pairs = defaultdict(list)
        for d in data:
            r1, a1, r2, a2, fa_atr, fa_rep, fa_sol, fa_elec = d
            key_1 = f'{r1}-{a1}'
            key_2 = f'{r2}-{a2}'
            key = f'{key_1}-{key_2}'
            pairs[key_1].append(key_2)
            pairs[key_2].append(key_1)
            e = [fa_atr, fa_rep, fa_sol, fa_elec]
            energies[key] = e
        return energies, pairs

    def _import_charges(self):
        """Import atomic charges from sql database
        This function will initialize
        """
        try:
            conn = sqlite3.connect(str(self.charges_path))
        except sqlite3.Error:
            print(
                "Error while connecting to the database " +
                self.charges_path)
            return -1
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM charges")
        data = cursor.fetchall()

        charges = {}
        for d in data:
            r1, a1, charge = d
            key = '-'.join([r1, a1])
            charges[key] = charge
        return charges

    def _import_radii(self):
        """Import atomic charges from sql database
        This function will initialize
        """
        try:
            conn = sqlite3.connect(str(self.radii_path))
        except sqlite3.Error:
            print("Error while connecting to the database " + self.radii_path)
            return -1
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lj_radius")
        data = cursor.fetchall()

        radii = {}
        for d in data:
            r1, a1, radius = d
            key = '-'.join([r1, a1])
            radii[key] = radius
        return radii

    def _build_images(self, rmsf, interpolation):

        protein_complex = parsePDB(self.pdb_path)
        inhibitor = protein_complex.select("resname INH")

        center = calcCenter(inhibitor.getCoords())

        # compute PCA for inhibitor and orient protein ?
        # orient_inibitor()
        protein_potential, ligand_potential = self._compute_electro_potential(
            protein_complex)

        size_ang = (self.grid_size - 1) / 2. * self.grid_spacing
        ex_min = center - size_ang
        ex_max = center + size_ang

        x = np.linspace(ex_min[0], ex_max[0], self.grid_size)
        y = np.linspace(ex_min[1], ex_max[1], self.grid_size)
        z = np.linspace(ex_min[2], ex_max[2], self.grid_size)

        # Select atoms with grid
        selected_atoms = protein_complex.select(
            f'within {size_ang} of resname INH')
        coordinates = selected_atoms.getCoords()
        res = selected_atoms.getResindices() + 1
        names = selected_atoms.getNames()
        # Select only atoms on grid
        mask = np.all(
            np.logical_and(
                coordinates >= ex_min,
                coordinates <= ex_max),
            axis=1)
        coordinates = coordinates[mask, :]
        res = res[mask]
        names = names[mask]
        keys = np.char.add(np.char.mod('%d-', res), names)
        key_map = dict(zip(keys, range(len(keys))))

        # identify index for each grid point
        x_idx = np.digitize(coordinates[:, 0], x) - 1
        y_idx = np.digitize(coordinates[:, 1], y) - 1
        z_idx = np.digitize(coordinates[:, 2], z) - 1
        d_coordinates = np.vstack((x_idx, y_idx, z_idx)).T
        protein_res = np.unique(
            protein_complex.select('protein').getResindices() + 1)

        grid_rmsf = np.zeros(3 * (self.grid_size,))
        arr_atr, arr_rep, arr_sol, arr_elec = np.zeros((4, len(keys)))
        energy_idxs = set()
        image = {}
        for field in ['fa_atr', 'fa_rep', 'fa_sol', 'fa_elec']:
            image[field] = np.zeros(3 * (self.grid_size,))
        print(f'Generating RMSF grid for {self.pdb_path.stem}')
        for key in keys:
            r1 = int(key.split('-')[0])
            if r1 in protein_res and key in rmsf:
                apply_gaussian_filter(d_coordinates[key_map[key]],
                                      self.rmsf_window,
                                      rmsf[key],
                                      self.radii[key] / self.grid_spacing,
                                      grid_rmsf)

        aa = np.array(np.meshgrid(x, y, z)).T
        print(f'Calculating energy maps for {self.pdb_path.stem}')
        ccccc = 0
        for key_1 in keys:
            if key_1 not in self.energy_pairs:
                continue
            print(ccccc)
            ccccc += 1
            aa1 = np.array(np.meshgrid(x -
                                       coordinates[key_map[key_1]][0], y -
                                       coordinates[key_map[key_1]][1], z -
                                       coordinates[key_map[key_1]][2])).T
            r1 = np.linalg.norm(aa1, axis=3)
            prev_aux = (
                r1 ** (1 / self.radii[key_1] - 3)) * (np.exp(-2 * r1 / self.radii[key_1])) ** 2
            for key_2 in self.energy_pairs[key_1]:
                if key_2 not in keys:
                    continue
                if f'{key_1}-{key_2}' not in self.energies:
                    key_2, key_1 = key_1, key_2
                if f'{key_1}-{key_2}' not in self.energies:
                    continue
                fa_atr, fa_rep, fa_sol, fa_elec = self.energies[f'{key_1}-{key_2}']
                r1, n1 = key_1.split('-')
                r2, n2 = key_2.split('-')
                r1 = int(r1)
                r2 = int(r2)
                # if n1 in backbone and n2 in backbone and np.abs(r1-r2) == 1:
                # skip connected residue
                if r1 in protein_res and r2 in protein_res and np.abs(
                        r1 - r2) == 1:
                    continue
                arr_atr[key_map[key_1]] += fa_atr
                arr_rep[key_map[key_1]] += fa_rep
                arr_sol[key_map[key_1]] += fa_sol
                arr_elec[key_map[key_1]] += fa_elec
                energy_idxs.add(key_map[key_1])
                if interpolation == 'pointwise_angular':
                    v = coordinates[key_map[key_2]] - \
                        coordinates[key_map[key_1]]
                    cos_theta = np.dot([1, 1, 1], v) / (3 * np.linalg.norm(v))
                    sin_theta = np.sqrt(1 - cos_theta ** 2)
                    rot_axis = np.cross([1, 1, 1], v) / (3 * np.linalg.norm(v))
                    rot_matrix1 = cos_theta * np.identity(3) + \
                        sin_theta * np.cross(np.identity(3), rot_axis) + \
                        (1 - cos_theta) * np.tensordot(rot_axis, rot_axis, axes=0)
                    filt = np.prod(
                        np.dot(
                            aa1,
                            rot_matrix1.T),
                        axis=3) * prev_aux
                    for field, values in {
                            'fa_atr': fa_atr, 'fa_rep': fa_rep, 'fa_sol': fa_sol, 'fa_elec': fa_elec}.items():
                        image[field] += values * filt

        energy_idxs = list(energy_idxs)
        arr_atr = arr_atr[energy_idxs]
        arr_rep = arr_rep[energy_idxs]
        arr_sol = arr_sol[energy_idxs]
        arr_elec = arr_elec[energy_idxs]
        x_idx = x_idx[energy_idxs]
        y_idx = y_idx[energy_idxs]
        z_idx = z_idx[energy_idxs]
        radii = [self.radii[keys[i]] for i in energy_idxs]

        aux_x, aux_y, aux_z = np.meshgrid(np.linspace(0, self.grid_size - 1, num=self.grid_size),
                                          np.linspace(0, self.grid_size - 1, num=self.grid_size),
                                          np.linspace(0, self.grid_size - 1, num=self.grid_size))
        grid_points = np.array(
            [aux_x.flatten(), aux_y.flatten(), aux_z.flatten()]).T
        print(f'Interpolating energies for {self.pdb_path.stem}')

        interpolation_class, mode = interpolation.split('_', maxsplit=1)
        f = id
        if interpolation_class == 'pointwise' and mode is not 'angular':
            aa = np.array(np.meshgrid(x, y, z)).T
            if mode == 'exp_vdw':
                def f(i):
                    return (
                        1 - np.exp(-((radii[i] / np.linalg.norm(aa - coordinates[energy_idxs[i]], axis=3)) ** 12)))
            elif mode == 'gaussian':
                def f(i):
                    return np.exp(-0.5 * ((np.linalg.norm(aa -
                                  coordinates[energy_idxs[i]], axis=3) / radii[i]) ** 2))
            for i in range(len(energy_idxs)):
                aa1 = f(i)
                for field, values in {
                        'fa_atr': arr_atr, 'fa_rep': arr_rep, 'fa_sol': arr_sol, 'fa_elec': arr_elec}.items():
                    image[field] = np.max(image[field], values[i] * aa1)
        else:
            for field, values in {'fa_atr': arr_atr, 'fa_rep': arr_rep,
                                  'fa_sol': arr_sol, 'fa_elec': arr_elec}.items():
                if interpolation_class == 'rbf':
                    rbf = Rbf(x_idx, y_idx, z_idx, values, function=mode)
                    for i in range(self.grid_size):
                        image[field][:, i, :] = (
                            rbf(grid_points[(self.grid_size ** 2) * i:(self.grid_size ** 2) * (i + 1), 0],
                                grid_points[(self.grid_size ** 2) * i:(self.grid_size ** 2) * (i + 1), 1],
                                grid_points[(self.grid_size ** 2) * i:(self.grid_size ** 2) * (i + 1), 2])
                        ).reshape((self.grid_size, self.grid_size))
        image['fa_atr'] = image['fa_atr'].clip(max=0)
        image['fa_rep'] = image['fa_rep'].clip(min=0)
        image['fa_elec'] = image['fa_elec'].clip(max=0)
        image['origin'] = ex_min
        image['protein_pot'] = protein_potential
        image['ligand_pot'] = ligand_potential
        image['rmsf'] = grid_rmsf
        print(f'Finished grid generation for {self.pdb_path.stem}')
        return image

    def _compute_electro_potential(self, pose_pdb):
        res = pose_pdb.getResindices() + 1
        names = pose_pdb.getNames()
        atoms = np.char.add(np.char.mod('%d-', res), names)
        atom_charges = np.array(itemgetter(*atoms)(self.charges))
        atom_radii = np.array(itemgetter(*atoms)(self.radii))
        pose_pdb.setCharges(atom_charges)
        pose_pdb.setRadii(atom_radii)
        center = np.array2string(
            calcCenter(
                pose_pdb.select('resname INH').getCoords()))[
            1:-1]
        grid_dim = ' '.join(3 * [str(self.grid_size)])
        grid_space = ' '.join(3 * [str(self.grid_spacing)])
        # size of coarse grained grid (avoid bondary artifacts)
        cglen = ' '.join(3 * [str(self.grid_spacing * self.grid_size + 10)])
        fglen = ' '.join(3 * [str(self.grid_spacing * (self.grid_size - 1))])
        # Compute protein and ligand potential
        protein_potential = APBS.run(self.path, 'protein', pose_pdb,
                                     'protein',
                                     grid_dim,
                                     grid_space, center, cglen, fglen)
        ligand_potential = APBS.run(
            self.path,
            'ligand',
            pose_pdb,
            'not protein and same residue as (within 3 of resname INH)',
            grid_dim,
            grid_space,
            center,
            cglen,
            fglen)

        return protein_potential, ligand_potential


def func(tpl):
    obj, rmsf, interpolation = tpl
    obj.compute_grids(rmsf, interpolation)
    obj.save_grids(interpolation)
    return True
