# Sciensano - gene detection

A software tool for gene discovery using customizable databases. It generates comprehensive, colour-coded reports for 
easy interpretation and visualization of results.

## INSTALLATION

```
virtualenv camel_env --python=python3.11
. camel_env/bin/activate
python setup.py install
```

A config file is required to run the workflow. A sample file is available under `camel/config/config.yml.sample`.
Be sure to check and modify the values for your system.

```
cp {PATH_TO_INSTALLATION}/camel/config/config.yml.sample {PATH_TO_INSTALLATION}/camel/config/config.yml
vim {PATH_TO_INSTALLATION}/camel/config/config.yml
```


### Dependencies

- [BLAST+ 2.14.0](https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/) (for BLAST-based detection)
- [CD-HIT 4.6.8](https://github.com/weizhongli/cdhit/tree/master) (for constructing databases)

The corresponding executables should be in your PATH to run the workflow. 
Other versions of these tools may work, but have not been tested.

## USAGE

**Note:** Absolute paths are recommended for the scripts.

### Gene detection

```
usage: gene_detection [-h] [--sample-name SAMPLE_NAME] --output-dir OUTPUT_DIR --output-html OUTPUT_HTML [--working-dir WORKING_DIR] [--threads THREADS] --fasta FASTA [--fasta-name FASTA_NAME] --database-dir DATABASE_DIR
                      [--blast-min-percent-identity BLAST_MIN_PERCENT_IDENTITY] [--blast-min-percent-coverage BLAST_MIN_PERCENT_COVERAGE] [--blast-task {blastn,megablast}]

optional arguments:
  -h, --help            show this help message and exit
  --sample-name SAMPLE_NAME
                        Dataset name (will be determined from the input if not specified)
  --output-dir OUTPUT_DIR
                        Output directory
  --output-html OUTPUT_HTML
                        Output HTML report
  --working-dir WORKING_DIR
                        Working directory for temporary files
  --threads THREADS     Number of threads to use
  --fasta FASTA         Input FASTA file
  --fasta-name FASTA_NAME
                        Input FASTA file name
  --database-dir DATABASE_DIR
                        Input database directory
  --blast-min-percent-identity BLAST_MIN_PERCENT_IDENTITY
                        Minimum percent identity
  --blast-min-percent-coverage BLAST_MIN_PERCENT_COVERAGE
                        Minimum percent target coverage
  --blast-task {blastn,megablast}
                        Value of the blast '-task' parameter
  --version             Print version and exit
```

A basic usage example is provided below:

```
gene_detection \
  --fasta /path/to/my_contigs.fasta \
  --database-dir /path/to/db \
  --output-html /path/to/output/report.html
```

### Database construction

The tool requires a database in the correct format.
The `mainmakegenedetectiondb.py` script can be used to create databases from FASTA files. Clustering is performed to 
limit the output to a single hit for each database cluster (defined by the `--identity-cutoff` parameter). 

```
usage: gene_detection_create_db [-h] --fasta FASTA [--fasta-name FASTA_NAME] [--identity-cutoff IDENTITY_CUTOFF] --output-html OUTPUT_HTML --output-dir OUTPUT_DIR [--working-dir WORKING_DIR] [--threads THREADS]

optional arguments:
  -h, --help            show this help message and exit
  --fasta FASTA         Input FASTA file.
  --fasta-name FASTA_NAME
                        Name of the input FASTA file (for Galaxy input).
  --identity-cutoff IDENTITY_CUTOFF
                        Clustering identity cutoff (%), entries with a higher value are combined into a single cluster.
  --output-html OUTPUT_HTML
                        Output HTML file with database construction information.
  --output-dir OUTPUT_DIR
                        Output directory.
  --working-dir WORKING_DIR
                        Working directory for temporary files.
  --threads THREADS     Number of threads to use.
```

A basic usage example is provided below:

```
mainmakegenedetectiondb.py --fasta /path/to/my_db.fasta --identity-cutoff 90 --output-dir /path/to/db/out
```

## CONTACT

In case of questions, issues or other feedback, you can contact:

- bioit@sciensano.be
- bert.bogaerts@sciensano.be
