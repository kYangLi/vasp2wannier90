#!/bin/bash
#SBATCH -J __task_name__
#SBATCH -N __nodes_quantity__
#SBATCH -n __total_cores__

declare -r PYTHON_EXEC=__python_exec__
declare -r va2wa_calc_SCRIPT=__va2wa_calc_script__

${PYTHON_EXEC} ${va2wa_calc_SCRIPT}
