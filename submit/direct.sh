#!/bin/bash
#

declare -r PYTHON_EXEC=__python_exec__
declare -r V2W_CALC_SCRIPT=__va2wa_calc_script__
declare -r TASK_NAME=__task_name__

echo "[calc] Start!!!"
${PYTHON_EXEC} ${V2W_CALC_SCRIPT} > ${TASK_NAME}.out
