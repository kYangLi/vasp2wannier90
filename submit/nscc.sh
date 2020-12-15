#!/bin/bash
#SBATCH -J __task_name__
#SBATCH -N __nodes_quantity__
#SBATCH -n __total_cores__
#SBATCH -p __job_queue__

declare -r PYTHON_EXEC=__python_exec__
declare -r VA2WA_CALC_SCRIPT=__va2wa_calc_script__

${PYTHON_EXEC} ${VA2WA_CALC_SCRIPT}
