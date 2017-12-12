# jupyter-ssh
Run jupyter over ssh and connect to it in your browser.

Currently only one script, only tested or used on one cluster.

## jupyter_o2
A python script to launch and connect to a Jupyter session on Orchestra 2, an HPC cluster managed by the HMS Resesarch Computing group.

Usage: `jupyter_o2 <USER> <subcommand>`

Example: `jupyter_o2 js123 notebook`

This will launch an X11-enabled ssh with port forwarding, start an interactive node running `jupyter notebook`, ssh into that interactive node to allow requests to be forwarded, and finally open the notebook in your browser.

### Configuration, etc.

#### Installation
Within `jupyter_o2`:
- Change `SOURCE_JUPYTER_CALL` to a one-line command you use to enter the environment containing jupyter. Use semicolons if necessary.
- Choose a `DEFAULT_JP_PORT` that is open on your machine (if the current default isn't already)

Either run jupyter_o2 with `./jupyter_o2` or copy it into a folder within your `$PATH`. 

#### Troubleshooting
##### nbsignatures.db
If jupyter hangs when opening notebooks for the first time in any session, and the console shows error messages such as:
  > `The signatures database cannot be opened; maybe it is corrupted or encrypted.` 
  
  > `Failed commiting signatures database to disk.`

  Disabling the signatures database may be the best option, since there is no non-networked file system shared between all the interactive compute nodes.
  
  1. enter an interactive session and generate a notebook config using
   `jupyter notebook --generate-config`
  2. in `~/.jupyter/jupyter_notebook_config.py` set `c.NotebookNotary.db_file = ':memory:'`
