pipeline = [(preprocessing.make_ligand_pdb_params, None), 
            (preprocessing.make_complex_pdb, [0]),
            (preprocessing.minimize_rosetta, [1]),
            (preprocessing.make_protein_pdb, [2]),
            (preprocessing.make_ligand_mol2_renamed, [2]),
            (preprocessing.make_ligand_mol2, [4]),
            (preprocessing.make_pdbqt, [5]),
            (preprocessing.compute_rosetta_energy, [2]),
            (voxelization.voxelize_rosetta, [7]),
            (voxelization.voxelize_htmd, [6]),
            (voxelization.voxelize_electroneg, [7]),
            (postprocessing.combine_maps, [8,9,10])]

def step(number, path, force=False):
    done = check_done(path)
    if number in done and not force:
        return True
    else:
        for requirement in pipeline_requirements[number]:
            if requirement is not done:
                step(requirement, path, force=True)
        pipeline_fn[number](path)
        return True
