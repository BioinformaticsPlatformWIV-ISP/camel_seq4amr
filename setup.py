from pathlib import Path

from setuptools import setup, find_packages

from camel.version import __version__

with open(Path(__file__).parent / 'README.md', encoding='utf-8') as handle:
    long_description = handle.read()


setup(
    name='camel_seq4amr',
    version=__version__,
    description='Workflow for gene detection',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=None,
    author='Bert Bogaerts',
    author_email='bioit@sciensano.be',
    classifiers=[
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Programming Language :: Python :: 3",
    ],
    keywords='gene detection blast kma',
    packages=find_packages() + ['camel.resources', 'camel.snakefiles', 'camel.data'],
    python_requires='>=3',
    include_package_data=True,
    install_requires=[
        'PyYAML==6.0.2',
        'beautifulsoup4==4.12.3',
        'biopython==1.84',
        'humanize==4.11.0',
        'pytest==8.3.4',
        'snakemake==8.25.5',
        'yattag==1.16.1'
    ],
    entry_points={
        'console_scripts': [
            'gene_detection=camel.scripts.__init__:main_gene_detection',
            'gene_detection_create_db=camel.scripts.__init__:main_create_db',
        ],
    }
)
