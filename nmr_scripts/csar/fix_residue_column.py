from pathlib import Path

def get_files(root):
  return list(root.glob('*/*/*_protein.pdb'))

def process_file(file):
  with file.open('r') as f:
    lines = f.readlines()
  for i, line in enumerate(lines[1:-1]):
    j=i+1
    lines[j] = line[:20] + ' ' + line[21:]
  with file.open('w') as f:
    f.write("".join(lines))

if __name__ == "__main__":
  list(map(process_file,get_files(Path('/cluster/scratch/hhussein/Structures'))))
