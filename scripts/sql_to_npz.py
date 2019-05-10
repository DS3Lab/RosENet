from collections import OrderedDict, defaultdict
from pathlib import Path
import sqlite3
import numpy as np
import sys

def _import_energies(path):
    """Import connectivity topology from sql database
    This function will initialize connect_topology
    """
    try:
        conn = sqlite3.connect(str(path))
    except sqlite3.Error:
        print(
            "Error while connecting to the database " +
            path)
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

def _import_radii(self):
    """Import atomic charges from sql database
    This function will initialize
    """
    try:
        conn = sqlite3.connect(str(self))
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

def _import_charges(self):
    """Import atomic charges from sql database
    This function will initialize
    """
    try:
        conn = sqlite3.connect(str(self))
    except sqlite3.Error:
        print("Error while connecting to the database " + self.charges_path)
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

def sql_to_numpy(en, rd, ch, output_file):
    energies, pairs = _import_energies(en)
    radii = _import_radii(rd)
    charges = _import_charges(ch)
    np_keys = list(energies.keys())
    np_values = np.array(list(energies.values()))
    radii = OrderedDict(sorted(radii.items(), key=lambda t: t[0]))
    charges = OrderedDict(sorted(charges.items(), key=lambda t: t[0]))
    radii_keys = np.array(list(radii.keys()))
    radii_values = np.array(list(radii.values()))
    charges_values = np.array(list(charges.values()))
    np.savez_compressed(output_file, np_keys, np_values, radii_keys, radii_values, charges_values)

if __name__ == '__main__':
    en = Path(sys.argv[1])
    rd = en.parent / en.name.replace('energies','radii')
    ch = en.parent / en.name.replace('energies','charges')
    output_file = en.parent / (en.stem.replace('energies','attr') + '.npz')
    sql_to_numpy(str(en),str(rd),str(ch), output_file)
