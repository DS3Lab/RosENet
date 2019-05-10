from pathlib import Path
from subprocess import call
import numpy as np
from prody import writePQR
from utils import isfloat


class APBS:
    _APBS_BIN_PATH = '/cluster/home/hhussein/apbs.sh'
    _TEMPLATE_FILE = '/cluster/home/hhussein/apbs.in'
    @staticmethod
    def run(
            output_path,
            name,
            pose,
            selection,
            grid_dim,
            grid_space,
            center,
            cglen,
            fglen):
        apbs_bin_path = APBS._APBS_BIN_PATH
        apbs_template_file = Path(APBS._TEMPLATE_FILE)
        apbs_input_file = output_path / f'apbs_{name}.in'
        apbs_output_file = output_path / f'{name}_potential.dx'
        if apbs_input_file.exists():
          apbs_input_file.unlink()
        if apbs_output_file.exists():
          apbs_output_file.unlink()
        writePQR(f'{output_path/name}.pqr', pose.select(selection))
        with apbs_template_file.open('r') as f:
            file_data = f.read()
        file_data = APBS._replace_apbs(
            file_data, str(output_path/name), grid_dim, grid_space, center, cglen, fglen)
        with apbs_input_file.open('w') as f:
            f.write(file_data)
        call([apbs_bin_path,
             f'{apbs_input_file.absolute()}'],
             cwd=str(output_path))
        apbs_input_file.unlink()
        o, d, potential = APBS._import_dx(apbs_output_file)
        apbs_output_file.unlink()
        return potential

    @staticmethod
    def _replace_apbs(
            filedata,
            xxx,
            grid_dim,
            grid_space,
            center,
            cglen,
            fglen):
        filedata = filedata \
            .replace('XXX', xxx) \
            .replace('GRID_DIM', grid_dim) \
            .replace('GRID_SPACE', grid_space) \
            .replace('INH_CENTER', center) \
            .replace('CG_LEN', cglen) \
            .replace('FG_LEN', fglen)
        return filedata

    @staticmethod
    def _import_dx(filename):
        origin = delta = data = dims = None
        counter = 0
        with open(filename, 'r') as dxfile:
            for row in dxfile:
                row = row.strip().split()
                if not row:
                    continue
                if row[0] == '#':
                    continue
                elif row[0] == 'origin':
                    origin = np.array(row[1:], dtype=float)
                elif row[0] == 'delta':
                    delta = np.array(row[2:], dtype=float)
                elif row[0] == 'object':
                    if row[1] == '1':
                        dims = np.array(row[-3:], dtype=int)
                        data = np.empty(np.prod(dims))
                elif isfloat(row[0]):
                    data[3 * counter:min(3 * (counter + 1), len(data))
                         ] = np.array(row, dtype=float)
                    counter += 1
        data = data.reshape(dims)
        return origin, delta, data

    @staticmethod
    def _export_dx(filename, density, origin, delta):
        nx, ny, nz = density.shape
        with open(filename, 'w') as dxfile:
            dxfile.write(
                f'object 1 class gridpositions counts {nx} {ny} {nz}\n')
            dxfile.write(f'origin {origin[0]} {origin[1]} {origin[2]}\n')
            dxfile.write(f'delta {delta} 0.0 0.0\n')
            dxfile.write(f'delta 0.0 {delta} 0.0\n')
            dxfile.write(f'delta 0.0 0.0 {delta}\n')
            dxfile.write(
                f'object 2 class gridconnections counts {nx}, {ny}, {nz}\n')
            dxfile.write(
                f'object 3 class array type double rank 0 items {nx * ny * nz} data follows\n')
            i = 1
            for d in density.flatten(order='C'):
                if i % 3:
                    dxfile.write('{} '.format(d))
                else:
                    dxfile.write('{}\n'.format(d))
                i += 1

            dxfile.write('\n')
