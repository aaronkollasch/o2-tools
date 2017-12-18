## Useful jupyter addons

### Kernels
There are [many kernels](https://github.com/jupyter/jupyter/wiki/Jupyter-kernels)
available for Jupyter, allowing the user to write notebooks in their desired language.

#### [bash_kernel](https://pypi.python.org/pypi/bash_kernel)
Since jupyter_o2 runs jupyter on an interactive node, 
notebooks running a Bash kernel can be used to document the commands 
you run on O2, without using SLURM to submit additional jobs. 
`%%bash` can be used to run a command in a subprocess in a notebook running any kernel,
but it does not remember your working directory or other variables from previous cells.  
 
Just be sure that your node has sufficient memory for the desired tasks,
or you could find your notebook server shutting down unexpectedly.
SLURM jobs can also be submitted and monitored from within a notebook to avoid this issue.

### jupyter contrib nbextensions
jupyter contrib nbextensions adds a useful nbextensions configuration tab 
to the main jupyter site. It also includes several useful extensions.
##### AutoSaveTime
Set the autosave time to 2 minutes to reduce the chance of losing changes 
due to a lost connection or to unexpected closure of the interactive node
(if it runs out of time, for example).

### [JupyterLab](https://github.com/jupyterlab/jupyterlab)
While JupyterLab is currently an alpha preview, 
it is a more complete environment than a jupyter notebook. 
With notebook and terminal tabs, a text editor, and a file browser, 
you could run everything you needed on O2 without leaving a single
browser window.

## Troubleshooting
#### nbsignatures.db
If jupyter hangs when opening notebooks for the first time in any session, and the console 
shows error messages such as:
  > `The signatures database cannot be opened; maybe it is corrupted or encrypted.`  
  > `Failed commiting signatures database to disk.`  

  Disabling the signatures database may be the best option, since there is no non-networked
  file system shared between all the interactive compute nodes.
  
  1. enter an interactive session and generate a notebook config using
   `jupyter notebook --generate-config`
  2. in `~/.jupyter/jupyter_notebook_config.py` set `c.NotebookNotary.db_file = ':memory:'`
  
