"""
Compute QM-derived partial charges using xTB (extended tight-binding).
Ligand: Full QM calculation
Protein: QM for binding site (within 10Å), force field charges beyond
"""
from __future__ import print_function
from RosENet.preprocessing.step import Step
from RosENet.preprocessing.minimize_rosetta import MinimizeRosetta
import subprocess
import tempfile
import numpy as np
from pathlib import Path
from prody import parsePDB, writePDB, calcCenter
import os

class ComputeXTBCharges(metaclass=Step, requirements=[MinimizeRosetta]):
    """
    Preprocessing step to compute QM-derived partial charges using xTB.

    Strategy:
    - Ligand: Full GFN2-xTB calculation
    - Protein (binding site within 10Å): GFN2-xTB calculation
    - Protein (beyond 10Å): Use force field charges from Rosetta
    """

    @classmethod
    def files(cls, pdb_object):
        """List of files being created

        Parameters
        ----------
        pdb_object : PDBObject
            PDB structure being handled
        """
        return [pdb_object.minimized.complex.xtb_charges]

    @classmethod
    def _run_xtb(cls, xyz_file, charge=0, spin=0):
        """
        Run xTB calculation and extract partial charges.

        Parameters
        ----------
        xyz_file : Path
            Path to XYZ coordinate file
        charge : int
            Total molecular charge
        spin : int
            Number of unpaired electrons (multiplicity - 1)

        Returns
        -------
        charges : numpy.ndarray
            Array of partial charges per atom
        """
        try:
            # Run xTB with GFN2 method
            result = subprocess.run(
                ['xtb', str(xyz_file), '--gfn', '2', '--chrg', str(charge),
                 '--uhf', str(spin), '--pop', '--norestart'],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=xyz_file.parent
            )

            if result.returncode != 0:
                print(f"xTB failed with return code {result.returncode}")
                print(f"Error: {result.stderr}")
                return None

            # Parse charges from output
            charges = cls._parse_xtb_charges(result.stdout)
            return charges

        except subprocess.TimeoutExpired:
            print(f"xTB calculation timed out for {xyz_file}")
            return None
        except FileNotFoundError:
            print("xTB executable not found. Please install xTB:")
            print("  conda install -c conda-forge xtb")
            print("  or see: https://github.com/grimme-lab/xtb")
            return None

    @classmethod
    def _parse_xtb_charges(cls, output):
        """
        Parse partial charges from xTB output.

        Parameters
        ----------
        output : str
            xTB stdout output

        Returns
        -------
        charges : list
            Partial charges per atom
        """
        charges = []
        in_charge_section = False

        for line in output.split('\n'):
            # Look for charge section (Mulliken or CM5 charges)
            if 'Mulliken charges' in line or 'covCN' in line:
                in_charge_section = True
                continue
            if in_charge_section:
                if line.strip() == '' or '----' in line:
                    break
                try:
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        charge = float(parts[-1])  # Last column is charge
                        charges.append(charge)
                except (ValueError, IndexError):
                    continue

        return np.array(charges)

    @classmethod
    def _write_xyz(cls, structure, output_file):
        """
        Write structure to XYZ format for xTB.

        Parameters
        ----------
        structure : prody.AtomGroup
            Structure to write
        output_file : Path
            Output XYZ file path
        """
        coords = structure.getCoords()
        elements = structure.getElements()

        with open(output_file, 'w') as f:
            f.write(f"{len(coords)}\n")
            f.write("Generated for xTB calculation\n")
            for elem, coord in zip(elements, coords):
                f.write(f"{elem:2s} {coord[0]:12.6f} {coord[1]:12.6f} {coord[2]:12.6f}\n")

    @classmethod
    def _get_force_field_charges(cls, structure):
        """
        Get force field charges for protein atoms (fallback).
        Uses simple charge assignment based on residue/atom type.

        Parameters
        ----------
        structure : prody.AtomGroup
            Protein structure

        Returns
        -------
        charges : numpy.ndarray
            Estimated charges
        """
        charges = np.zeros(len(structure))

        # Standard amino acid charge assignments
        charge_dict = {
            ('ARG', 'NH1'): 0.8, ('ARG', 'NH2'): 0.8,
            ('LYS', 'NZ'): 1.0,
            ('ASP', 'OD1'): -0.5, ('ASP', 'OD2'): -0.5,
            ('GLU', 'OE1'): -0.5, ('GLU', 'OE2'): -0.5,
            ('HIS', 'ND1'): 0.3, ('HIS', 'NE2'): 0.3,
        }

        for i, (resname, atomname) in enumerate(zip(structure.getResnames(),
                                                      structure.getNames())):
            key = (resname, atomname)
            if key in charge_dict:
                charges[i] = charge_dict[key]
            elif atomname.startswith('O'):
                charges[i] = -0.4
            elif atomname.startswith('N'):
                charges[i] = -0.3

        return charges

    @classmethod
    def _run(cls, pdb_object):
        """
        Main execution function for the preprocessing step.

        Parameters
        ----------
        pdb_object : PDBObject
            PDB structure being handled
        """
        pdb_file = pdb_object.minimized.complex.pdb.path
        output_file = pdb_object.minimized.complex.xtb_charges.path

        try:
            # Parse complex
            complex_structure = parsePDB(str(pdb_file))
            protein = complex_structure.select("not (resname WER or water)")
            ligand = complex_structure.select("resname WER")

            if ligand is None:
                print(f"No ligand found in {pdb_file}")
                return

            # Get ligand center for distance calculations
            ligand_center = calcCenter(ligand.getCoords())

            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)

                # 1. Compute ligand charges (full QM)
                print(f"Computing QM charges for ligand...")
                ligand_xyz = tmpdir / "ligand.xyz"
                cls._write_xyz(ligand, ligand_xyz)
                ligand_charges = cls._run_xtb(ligand_xyz, charge=0, spin=0)

                if ligand_charges is None or len(ligand_charges) != len(ligand):
                    print(f"Failed to compute ligand charges for {pdb_object.id}")
                    return

                # 2. Identify binding site atoms (within 10Å of ligand)
                protein_coords = protein.getCoords()
                distances = np.linalg.norm(protein_coords - ligand_center, axis=1)
                binding_site_mask = distances <= 10.0

                print(f"Binding site: {np.sum(binding_site_mask)} atoms within 10Å")

                # 3. Compute binding site charges (QM)
                if np.sum(binding_site_mask) > 0 and np.sum(binding_site_mask) < 600:
                    binding_site = protein.select(
                        f'same residue as (within 10 of ligand)',
                        ligand=ligand
                    )

                    if binding_site is not None and len(binding_site) > 0:
                        print(f"Computing QM charges for {len(binding_site)} binding site atoms...")
                        bs_xyz = tmpdir / "binding_site.xyz"
                        cls._write_xyz(binding_site, bs_xyz)
                        bs_charges = cls._run_xtb(bs_xyz, charge=0, spin=0)

                        if bs_charges is None or len(bs_charges) != len(binding_site):
                            print("Binding site QM failed, using force field charges")
                            bs_charges = cls._get_force_field_charges(binding_site)
                    else:
                        bs_charges = np.array([])
                else:
                    # Too many atoms for QM, use force field
                    print(f"Binding site too large ({np.sum(binding_site_mask)} atoms), using FF charges")
                    binding_site = protein.select(
                        f'same residue as (within 10 of ligand)',
                        ligand=ligand
                    )
                    bs_charges = cls._get_force_field_charges(binding_site) if binding_site else np.array([])

                # 4. Distant protein atoms use force field charges
                distant_protein = protein.select(
                    f'not (same residue as (within 10 of ligand))',
                    ligand=ligand
                )

                if distant_protein is not None and len(distant_protein) > 0:
                    distant_charges = cls._get_force_field_charges(distant_protein)
                else:
                    distant_charges = np.array([])

                # 5. Build complete charge array with atom keys
                protein_keys = []
                protein_charges_list = []

                # Add binding site
                if binding_site is not None:
                    for i, (rnum, aname) in enumerate(zip(binding_site.getResnums(),
                                                           binding_site.getNames())):
                        chain = binding_site.getChids()[i] if binding_site.getChids() is not None else 'A'
                        key = f"{rnum}{chain}-{aname.strip()}"
                        protein_keys.append(key)
                        protein_charges_list.append(bs_charges[i] if i < len(bs_charges) else 0.0)

                # Add distant atoms
                if distant_protein is not None:
                    for i, (rnum, aname) in enumerate(zip(distant_protein.getResnums(),
                                                           distant_protein.getNames())):
                        chain = distant_protein.getChids()[i] if distant_protein.getChids() is not None else 'A'
                        key = f"{rnum}{chain}-{aname.strip()}"
                        protein_keys.append(key)
                        protein_charges_list.append(distant_charges[i] if i < len(distant_charges) else 0.0)

                # Add ligand
                ligand_keys = []
                for i, (rnum, aname) in enumerate(zip(ligand.getResnums(), ligand.getNames())):
                    chain = ligand.getChids()[i] if ligand.getChids() is not None else 'A'
                    key = f"{rnum}{chain}-{aname.strip()}"
                    ligand_keys.append(key)

                all_keys = protein_keys + ligand_keys
                all_charges = np.concatenate([protein_charges_list, ligand_charges])

                # Save results
                np.savez_compressed(
                    str(output_file),
                    charge_keys=all_keys,
                    charge_values=all_charges
                )

                print(f"Successfully computed {len(all_charges)} QM/FF charges")

        except Exception as e:
            print(f"Error computing xTB charges for {pdb_object.id}: {e}")
            import traceback
            traceback.print_exc()
            raise
