# Introduction

*Camel* is our in-house system to run pipelines. In this repository you can find the code to run the gene detection workflow.

# Installation

Start by cloning the repository.

```
git clone https://github.com/BertBog/camel_seq4amr.git;
```

- The required dependencies can be installed using conda
- **Optional**: Speed up the installation using *mamba*. First install *mamba* in your current conda environment and replace `conda` by `mamba` in the commands.

```
conda env create -f camel_seq4amr/camel_env.yml;
```

## Special case: SRST2

- SRST2 is an old tool that still uses Python2.7 and, therefore, it is not compatible with the main Conda installation.
- The problem can be solved by creating a separate Conda environment for SRST2 (based on Python 2.7)

```
conda activate base;
conda create -c bioconda -n srst2 srst2;
```

## Configuration

To finalize the installation, some config variables need to be set.
The configuration file needs to be stored in `${DIR_INSTALL}/camel/config/config.yml`.
A sample file is provided `${DIR_INSTALL}/camel/config/config.yml.sample`.

```
cp ${DIR_INSTALL}/camel/config/config.yml.sample ${DIR_INSTALL}/camel/config/config.yml;
vim ${DIR_INSTALL}/camel/config/config.yml;
```

The variables that need to be set are:
- **dir_logs**: directory to store logs
- **dir_temp**: directory to store temporary files

# Testing the installation
The gene detection scripts can be tested using the following commands (change the DIR_INSTALL to the directory containing the CAMEL repository):
```
conda activate camel_env;
export DIR_INSTALL={DIR_INSTALL}; 
export PYTHONPATH=${DIR_INSTALL};
pytest ${DIR_INSTALL}/camel/tests/test_genedetection.py -n {NB_OF_JOBS};
```

# Setting up the databases


# Galaxy integration

The Galaxy wrappers are included in the *galaxy* directory.
The *.loc* file for the databases also included (the path to the databases still needs to be updated!). 
Examples for the shell scripts that are called by the Galaxy wrappers are also included. 
But, these have to be updated by setting the *PYTHONPATH* environment variable and adding the *scripts* directory to the PATH (otherwise the command *MainGeneDetection.py* will not be found).  
