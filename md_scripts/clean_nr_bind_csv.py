import re
from collections import defaultdict
import itertools
import numpy as np

with open('./scratch/nr_bind.csv', 'r') as f:
  lines = f.readlines()
lines = list(filter(lambda x: not x.startswith('"'), lines))
family_lines = list(filter(lambda x: x[1].startswith(',Family. Representative Entry is ,'), zip(range(len(lines)),lines)))
family_lines = list(map(lambda x: (x[0],x[1][34:38]), family_lines))


valid_regexp = re.compile(',,,([^,:]*)(?::[^,]*)?,valid,(Ki|Kd|ic50|Ka),(=|~|<|>),(\d*|\d+(?:\.\d+)?(?:e(?:\+|-)\d+)?),([^,]*),[^,]*,')

pdb_map = defaultdict(set)
unit_normalization_dict = {'nM': -9, 'fM': -15, 'M^-1': -1, 'mM': -3, 'pM': -12, 'uM': -6, 'M': 0}
i = 0
while i < len(family_lines):
  if i == len(family_lines) - 1:
    top = len(lines)
  else:
    top = family_lines[i+1][0]
  for j in range(family_lines[i][0]+1,top):
    grps = valid_regexp.match(lines[j])
    if grps:
      row = grps.groups()
      exp = unit_normalization_dict[row[-1]]
      value = np.round(-(np.log(float(row[-2])) + exp),decimals=2)
      new_row = (row[0], row[1], row[2], value)
      pdb_map[family_lines[i][1]].add(new_row)
  i = i + 1

with open('./scratch/nr_bind_cleaned.csv', 'w') as f:
  for key, val in pdb_map.items():
    for entry in val:
      f.write(f'{key} {{{" ".join(map(str,entry))}}}\n')
