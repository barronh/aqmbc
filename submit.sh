#!/bin/bash

#SBATCH -t 24:00:00
#SBATCH --nodes 1
#SBATCH --ntasks 8
#SBATCH -J BCON
#SBATCH -p oar
#SBATCH --gid=romo
#SBATCH -o logs/slog.o%j
#SBATCH -e logs/slog.e%j

make -j8

