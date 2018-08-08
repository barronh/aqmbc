#!/bin/bash

#SBATCH -t 24:00:00
#SBATCH --nodes 1
#SBATCH --ntasks 1
#SBATCH -J bc_com
#SBATCH -p singlepe
#SBATCH --gid=romo
#SBATCH -o logs/slog.o%j
#SBATCH -e logs/slog.e%j

make -j1

