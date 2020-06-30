SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPTPATH

conda remove --name rosenet || true
conda create --name rosenet python=3.7 --file conda-requirements.txt -y 
conda init bash
conda activate rosenet && (yes | pip install -r pip-requirements.txt)

rm -r ./htmd
wget -qO- https://anaconda.org/acellera/HTMD/1.13.10/download/linux-64/htmd-1.13.10-py36_0.tar.bz2 | tar -xvj lib/python3.6/site-packages/htmd
mv lib/python3.6/site-packages/htmd/ .
rm -r lib

echo "Copy the pyrosetta folder in $SCRIPTPATH or add pyrosetta to PYTHONPATH"
