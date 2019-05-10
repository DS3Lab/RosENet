from htmd.home import home
from os.path import join
from htmd.builder.solvate import solvate
from htmd.parameterization.fftype import fftype, FFTypeMethod
from htmd.parameterization.writers import writeFRCMOD
from htmd.molecule.molecule import Molecule
from htmd.builder.amber import defaultParam, build

# Test protein ligand building with parametrized ligand
refdir = home(dataDir=join('test-amber-build', 'protLig'))
tmpdir = './protLig'

mol = Molecule(join(refdir, '3ptb_mod.pdb'))
mol.center()
lig = Molecule(join(refdir, 'benzamidine.pdb'), guess=('bonds', 'angles', 'dihedrals'))
prm, lig = fftype(lig, method=FFTypeMethod.GAFF2)
writeFRCMOD(lig, prm, join(tmpdir, 'mol.frcmod'))
lig.segid[:] = 'L'
lig.center()

from htmd.molecule.util import maxDistance
D = maxDistance(mol, 'all')
D += 6
lig.moveBy([0, 0, D])

newmol = Molecule()
newmol.append(lig)
newmol.append(mol)
smol = solvate(newmol, posz=3)

params = defaultParam() + [join(tmpdir, 'mol.frcmod'),]

_ = build(smol, outdir=tmpdir, param=params, ionize=False)
