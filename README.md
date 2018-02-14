# o2-tools
Tools for use with Orchestra 2, an HPC cluster managed by the HMS Resesarch Computing group.  
- `jobinfo.sh` Get info on SLURM jobs.  
- `jupyter_o2` Run jupyter over ssh and connect to it in your browser.

## jobinfo.sh
A bash script that provides information on your SLURM jobs.

Usage: `jobinfo` or `jobinfo <job id>`  
Tab autocompletion of the job id is supported.

Source this script in your `~/.bashrc` file.

## jupyter_o2
A command line tool to launch and connect to a Jupyter session on O2.

Usage: `jupyter_o2 <USER> <subcommand>`

Example: `jupyter_o2 js123 notebook`

This will follow the procedure described on the 
[O2 wiki](https://wiki.rc.hms.harvard.edu/display/O2/Jupyter+on+O2).
`jupyter_o2` will launch an X11-enabled SSH session with port forwarding, 
start an interactive node running `jupyter notebook`, 
SSH into that interactive node to allow requests to be forwarded,
and finally open the notebook in your browser.

### Configuration, etc.

#### Installation
Run jupyter_o2 with `./jupyter_o2` or copy the file into a folder within your `$PATH`.

#### Edit `.jupyter_o2.cfg`
- After running jupyter_o2 once, cancel at the PIN entry step using Ctrl-C.
A configuration file should have been created at `~/.jupyter_o2.cfg`. Edit this file.
- Change `MODULE_LOAD_CALL` and `SOURCE_JUPYTER_CALL` to commands that 
activate your jupyter environment (more description in the file itself). 
If one or both of these are not necessary, deleting everything after the `=`
will set it to an empty string.
- Choose a `DEFAULT_JP_PORT` that is open on your machine,
if the current default (`8887`) isn't already open. 
The port can also be specified using `jupyter_o2 -p <port>`.

#### Requirements
##### Packages
- Pexpect

##### Optional
- dnspython
- pyobjc-framework-Quartz
- pinentry (a command line tool)

jupyter_o2 has been tested with Python versions 2.7 and 3.6,
and Pexpect version 4.3. However, other versions may work just as well.

##### Operating system
`jupyter_o2` has been tested on MacOS. It may work on Linux and it would likely require 
both Cygwin and a Cygwin version of Python to work on Windows (for Pexpect and SSH).

