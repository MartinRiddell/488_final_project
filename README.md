For running on the Cloud:

Install miniconda environment:
```
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
```
Download repo from github (you might need to install git first)
```
git clone git@github.com:MartinRiddell/Martin-Riddell-Summer-2023.git
cd Martin-Riddell-Summer
```
Copy github split from lab server:
```
scp -r user@morana.cs.yale.edu:/home/mr2489/StarcoderRobustness/gcloud/Github_Split ~
```
Make results folder:
```
mkdir results
```
Create the conda environment:
```
conda env create -f environment.yml
```
Activate conda environment:
```
conda activate myenv
```
You can run the pipeline with the following command. This will run the pipeline on the first 10 questions in the humaneval benchmark
```
python main.py 1 10
```

------------------------------------------------------------

For running on Grace Cluster:

Copy and Paste the following commands into the terminal on the Grace cluster:
```
salloc # Request a compute node
module load miniconda
conda create -n myenv python=3.9 datasets fuzzywuzzy[speedup]
```
The batch script will automatically load that environment with this:
```
module load miniconda
conda activate myenv
python main.py 
```
Change the start and end variables in eval.slurm to control where the program starts and finishes. It is indexed at 1, so the following setup will search for the first 10 problems:
```
start=1
end=10
```
