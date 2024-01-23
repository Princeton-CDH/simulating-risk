#!/bin/bash
#SBATCH --job-name=simrisk       # job short name 
#SBATCH --nodes=1                # node count
#SBATCH --ntasks=1               # total number of tasks across all nodes
#SBATCH --cpus-per-task=20       # cpu-cores per task 
#SBATCH --mem-per-cpu=525M       # memory per cpu-core
#SBATCH --time=02:00:00          # total run time limit (HH:MM:SS)
#SBATCH --mail-type=begin        # send email when job begins
#SBATCH --mail-type=end          # send email when job ends
#SBATCH --mail-type=fail         # send email if job fails
#SBATCH --mail-user=EMAIL

# Template for batch running hawkdovemulti simulation with slurm. 
# Assumes a conda environment named simrisk is set up with required dependencies.
#
# Update before using:
# - EMAIL for slurm notification
# - customize path for working directory (set username if using Princeton HPC)
#   (and make sure the directory exists)
# - add an SBATCH array directive if desired
# - customize the batch run command as appropriate
# - configure the time appropriately for the batch run

module purge
module load anaconda3/2023.9
conda activate simrisk

# change working directory for data output
cd /scratch/network/<USER>/simrisk

# test run: one iteration, max of 200 steps, no progress bar
# (completed in ~18 minutes on 20 CPUs)
#simrisk-hawkdovemulti-batchrun --iterations 1 --max-step 200 --no-progress

# longer run: 10 iterations, max of 200 steps, no progress bar
#simrisk-hawkdovemulti-batchrun --iterations 10 --max-step 200 --no-progress

# To generate data for a larger total number of iterations, 
# run the script as a job array. 
# e.g. for 100 iterations, run with --iterations 10  and 10 tasks with #SBATCH --array=0-9
# and add a file prefix option to generate separate files that can be grouped
simrisk-hawkdovemulti-batchrun --iterations 10 --max-step 125 --no-progress --file-prefix "job${SLURM_ARRAY_JOB_ID}_task${SLURM_ARRAY_TASK_ID}_"


