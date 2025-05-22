#!/bin/sh
workingDirectory=$(pwd)
echo $workingDirectory
export PYTHONPATH=$PYTHONPATH:$workingDirectory
export PYTHONPATH=$PYTHONPATH:$workingDirectory/Experiments/LifeChoreography/triangleFormation
export PYTHONPATH=$PYTHONPATH:$workingDirectory/Experiments/LifeChoreography/tetrahedronFormation
export PYTHONPATH=$PYTHONPATH:$workingDirectory/Experiments
export PYTHONPATH=$PYTHONPATH:$workingDirectory/../RM_dashboard
export PYTHONPATH=$PYTHONPATH:$workingDirectory/../RM_Retinas
export PYTHONPATH=$PYTHONPATH:$workingDirectory/../
