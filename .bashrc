# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi

export PS1="[\[\033[36m\]\u\[\033[0m\]@\[\033[0;33m\]\h:\[\033[0m\]\W\[\033[0m\]]\[\033[0m\]$ "
# export PS1="[\[\033[1;35m\]\#\[\033[0;35m\]:\!\[\033[0m\]@\[\033[31m\]\t\[\033[0m\]] $PS1"

# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
# alias ll="ls -lhA"

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

function htopu {
    htop -u $USER "$@"
}

function topu {
    top -u $USER "$@"
}

# alias interactive='srun --pty -p interactive --mem 500M -t 0-06:00 /bin/bash'
function interactive {
    srun --pty -p interactive --mem 1G -t 0-12:00 "$@" /bin/bash
}

function interactive_gpu {
    srun --pty -p gpu,gpu_marks --gres=gpu:1 -c 4 --mem 30G -t 0-12:00 "$@" /bin/bash
}

function fairshare {
    sshare -u $USER -U
}

alias twork="tmux attach -t work"
alias vi="$HOME/bin/vim"

function csview {
column -s, -t < $1 | less -#2 -N -S
}

function tsview {
column -s'      ' -t < $1 | less -#2 -N -S
}

# Source jobinfo script to get info on running jobs
source ~/.jobinfo.sh
