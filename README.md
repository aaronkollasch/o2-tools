# o2-tools
Tools for use with Orchestra 2, an HPC cluster managed by the HMS Resesarch Computing group.  
- `jobinfo.sh` Get info on currently running SLURM jobs.  
- `jupyter_o2` Run jupyter over ssh and connect to it in your browser.

## jobinfo.sh
A bash script that provides information on your SLURM jobs.

Usage: `jobinfo <job id>`  
Tab autocompletion of the job id is supported.

Source this script in your `~/.bashrc` file.

## jupyter_o2
A python script to launch and connect to a Jupyter session on O2.

Usage: `jupyter_o2 <USER> <subcommand>`

Example: `jupyter_o2 js123 notebook`

This will launch an X11-enabled ssh with port forwarding, start an interactive node
running `jupyter notebook`, ssh into that interactive node to allow requests to be forwarded,
and finally open the notebook in your browser.

### Configuration, etc.

#### Installation
Within `jupyter_o2`:
- Change `SOURCE_JUPYTER_CALL` to a one-line command you use to enter the environment
    containing jupyter. Use semicolons if necessary.
- Choose a `DEFAULT_JP_PORT` that is open on your machine (if the current default isn't already)

Either run jupyter_o2 with `./jupyter_o2` or copy it into a folder within your `$PATH`.  

##### Required packages
- Pexpect

##### Optional packages
- dnspython
- pyobjc-framework-Quartz
- pinentry (a command line tool)

##### Operating system
`jupyter_o2` has been tested on MacOS. It may work on Linux and it would likely require 
Cygwin and a Cygwin version of Python to work on Windows (for Pexpect and SSH).

