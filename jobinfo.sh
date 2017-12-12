#!/bin/bash
# jobinfo provides information on your SLURM jobs
# source this script in ~/.bashrc

jobinfo() {
    if [ $# -eq 0 ]; then
        squeue -u $USER -t 'all'
	return 1
    fi

# # print job name and time limit before seff output
#    printf "Job Name: "
#    sacct -o jobname -j $1 -n -P | head -n 1
#    printf "Time Limit: "
#    sacct -o timelimit -j $1 -n -P | head -n 1
    echo "Job Name: $(sacct -o jobname,timelimit -j $1 -n -P | head -n 1 | sed -e 's/|/\nTime Limit: /')"

    seff $1
    echo
    sacct -o jobid,alloccpus,state,reqmem,maxrss,averss,maxvmsize,elapsed -j $1
    
    if [ -z "$( sstat -j $1 2>&1 > /dev/null )" ]; then
        echo
        sstat -o jobid,ntasks,avecpu,avecpufreq,maxrss,averss,maxvmsize,avevmsize -j $1
    fi
}

# jobinfo supports tab autocomplete to fill job ids
# - if there are currently running jobs, only these will be filled.
# - if there are no currently running jobs, recently completed jobs will also appear.
_comp_jobinfo()
{
    _script_commands="$(squeue -u $USER -h -o '%i' | tr '\n' ' ')"

    if [ -z "$_script_commands" ]; then
        _script_commands="$(squeue -u $USER -h -o '%i' -t 'all' -S '-e' | tr '\n' ' ')"
    fi

    if [ -z "$_script_commands" ]; then
        _script_commands=" "
    fi

    local cur
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    COMPREPLY=( $(compgen -W "${_script_commands}" -- ${cur}) )

    return 0
}
complete -o nospace -F _comp_jobinfo jobinfo

