#!/bin/bash
#SBATCH --job-name=simrisk       # job short name 
#SBATCH --nodes=1                # node count
#SBATCH --ntasks=1               # total number of tasks across all nodes
#SBATCH --cpus-per-task=20       # cpu-cores per task 
#SBATCH --mem-per-cpu=600M       # memory per cpu-core
#SBATCH --time=02:00:00          # total run time limit (HH:MM:SS)
#SBATCH --mail-type=begin        # send email when job begins
#SBATCH --mail-type=end          # send email when job ends
#SBATCH --mail-type=fail         # send email if job fails
#SBATCH --mail-user=EMAIL

module purge
module load anaconda3/2023.9
conda activate simrisk

# change working directory for data output
cd /scratch/network/<USER>/simrisk

# test run: one iteration, max of 125 steps, no progress bar
# (typically completes in less than 15 minutes)
simrisk-hawkdovemulti-batchrun --iterations 1 --max-step 125 --no-progress

# longer run: 10 iterations, max of 125 steps, no progress bar
# (typically completes in less than 15 minutes)
simrisk-hawkdovemulti-batchrun --iterations 10 --max-step 125 --no-progress

# To generate data for a larger total number of iterations, 
# run the script as a job array. 
# e.g. for 100 iterations, run with --iterations 10  and 10 tasks with #SBATCH --array=0-9
# and add a file prefix option to generate separate files that can be grouped
simrisk-hawkdovemulti-batchrun --iterations 10 --max-step 125 --no-progress --file-prefix "job${SLURM_ARRAY_JOB_ID}_task${SLURM_ARRAY_TASK_ID}_"

3000 in one minute  

8100 with one iteration

try with larger max step?


81000 with ten iterations

3000

8100 with one iteration, 125 max step
00:11:03


10 iterations, 125 steps, 2 hours = 66395 runs

