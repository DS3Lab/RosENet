from pathlib import Path
from prody import parsePDB, writePDB
from threading import Thread
from queue import Queue
import sys

def get_folders():
  return Path('/cluster/scratch/hhussein/Proteins/PDBBind/').glob('*/')

def get_files(folder):
  pdb_code = folder.stem
  return (folder / 'minimized').glob(pdb_code + '_complex_*.pdb')

def job(pdb_folder):
  for pdb_file in get_files(pdb_folder):
    receptor_file = pdb_file.parent / pdb_file.stem.replace("complex", "receptor")
    ligand_file = pdb_file.parent / pdb_file.stem.replace("complex", "ligand")
    if receptor_file.exists() and ligand_file.exists():
      continue
    print(pdb_file, "started.")
    complex_pdb = parsePDB(str(pdb_file))
    receptor_pdb = complex_pdb.select("protein")
    ligand_pdb = complex_pdb.select("resname INH")
    writePDB(str(receptor_file), receptor_pdb)
    writePDB(str(ligand_file), ligand_pdb)
    print(pdb_file, "completed.")
    

def worker(queue):
  while True:
    pdb_folder = queue.get()
    if pdb_folder is None:
      break
    job(pdb_folder)
    queue.task_done()

def spawn(n=48):
  folders = get_folders()
  threads = []
  queue = Queue()
  for i in range(n):
    t = Thread(target=worker, args=(queue,))
    t.start()
    threads.append(t)
  
  for folder in list(folders):
    queue.put(folder)

  queue.join()

  for i in range(n):
    q.put(None)
  for t in threads:
    t.join()

if __name__ == "__main__":
  try:
    n_threads = int(sys.argv[1])
  except:
    print("Parameter needs to be an integer")
    exit()
  spawn(n_threads)
