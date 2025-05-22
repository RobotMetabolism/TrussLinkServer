#!/bin/sh
workingDirectory=$(pwd)
echo $workingDirectory
export PYTHONPATH=$PYTHONPATH:$workingDirectory
export PYTHONPATH=$PYTHONPATH:$workingDirectory/server
export PYTHONPATH=$PYTHONPATH:$workingDirectory/retinas
export PYTHONPATH=$PYTHONPATH:$workingDirectory/RM_dashboard


