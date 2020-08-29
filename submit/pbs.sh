#!/bin/bash
#PBS -N __task_name__
#PBS -l nodes=__nodes_quantity__:ppn=__cores_per_node__
#PBS -l walltime=__pbs_walltime__:00:00
#PBS -q __pbs_queue__
#PBS -j oe

declare -r PYTHON_EXEC=__python_exec__
declare -r va2wa_calc_SCRIPT=__va2wa_calc_script__
# Enter the Calculate Folder
cd ${PBS_O_WORKDIR}
# Copy the Machinefile
cp ${PBS_NODEFILE} __mpi_mechinefile__

${PYTHON_EXEC} ${va2wa_calc_SCRIPT}
