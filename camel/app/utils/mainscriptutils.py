"""
Contains helper function for main scripts with a report output.
"""
import argparse
import collections
import datetime
import logging
from pathlib import Path
from typing import Optional, List, Any, Dict

import pkg_resources

from camel.app.utils.fastqutils import FastqUtils
from camel.app.utils.report.htmlreport import HtmlReport
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.snakemake.snakepipelineutils import SnakePipelineUtils


def add_common_arguments(argument_parser: argparse.ArgumentParser) -> None:
    """
    Adds the common arguments to the argument parser.
    :param argument_parser: Argument parser
    :return: None
    """
    argument_parser.add_argument('--sample-name', type=str)
    argument_parser.add_argument('--output-dir', required=True, type=Path)
    argument_parser.add_argument('--working-dir', default=Path.cwd(), type=Path)
    argument_parser.add_argument('--output-html', required=True, type=Path)
    argument_parser.add_argument('--threads', default=8, type=int)


def add_input_files_arguments(argument_parser: argparse.ArgumentParser, fasta_input_enabled: bool = True) -> None:
    """
    Adds the arguments for the input files (FASTA / FASTQ PE).
    :param argument_parser: Argument parser
    :param fasta_input_enabled: Boolean to indicate if FASTA input should be enabled
    :return: None
    """
    if fasta_input_enabled:
        argument_parser.add_argument('--fasta', help="Input FASTA file", type=Path)
        argument_parser.add_argument('--fasta-name', help="Input FASTA file name", type=str)
    argument_parser.add_argument('--fastq-pe', help="Input PE FASTQ files", nargs=2, type=Path)
    argument_parser.add_argument('--fastq-pe-names', help="Input PE FASTQ file names", nargs=2, type=Path)
    argument_parser.add_argument('--fastq-se', help="Input SE FASTQ file", type=Path)
    argument_parser.add_argument('--fastq-se-name', help="Input SE FASTQ file name")
    argument_parser.add_argument(
        '--read-type', help="Read type", choices=['illumina', 'iontorrent', 'nanopore'], default='illumina')
    argument_parser.add_argument('--trim-reads', help="Perform read trimming", action='store_true')
    argument_parser.add_argument(
        '--adapter', choices=['NexteraPE', 'TruSeq2', 'TruSeq3'],
        help="(Illumina) Adapter that was used for sequencing, used for read-trimming")
    argument_parser.add_argument(
        '--report-include-fastq', help="Include trimmed FASTQ files in the report", action='store_true')


def add_assembly_arguments(argument_parser: argparse.ArgumentParser) -> None:
    """
    Adds the arguments that are used for the assembly.
    :param argument_parser: Argument parser
    :return: None
    """
    argument_parser.add_argument('--assembly-kmers', help="Kmers to use for assembly", type=str)
    argument_parser.add_argument(
        '--assembly-cov-cutoff', help="Minimal k-mer coverage for assembled contigs", type=int)
    argument_parser.add_argument(
        '--assembly-min-contig-length', help="Minimal length for assembled contigs", type=int)


def determine_input_file_str(args: argparse.Namespace) -> str:
    """
    Determines the input files based on the given command line arguments.
    :param args: Command line arguments
    :return: Input files as string
    """
    if ('fasta' in args) and (args.fasta is not None) and (args.fasta_name is not None):
        return args.fasta_name
    elif ('fasta' in args) and (args.fasta is not None):
        return args.fasta.name
    elif (args.fastq_pe is not None) and (args.fastq_pe_names is not None):
        return ', '.join(f.name for f in args.fastq_pe_names)
    elif args.fastq_pe is not None:
        return ', '.join(f.name for f in args.fastq_pe)
    elif args.fastq_se_name is not None:
        return args.fastq_se_name
    elif args.fastq_se is not None:
        return args.fastq_se.name
    logging.warning("Cannot determine input files from given arguments")
    return 'NA'


def generate_analysis_info_section(
        args: argparse.Namespace, additional_info: Optional[List[List[str]]] = None,
        input_file_str: str = None) -> HtmlReportSection:
    """
    Generates the report section with the analysis info.
    :param args: Command line arguments
    :param additional_info: Additional info to add to the report section
    :param input_file_str: Input file string, is determined based on input files if it is not set.
    :return: Analysis info section
    """
    section = HtmlReportSection('Analysis info')
    input_files = determine_input_file_str(args) if input_file_str is None else input_file_str
    data = [
        ('Analysis date:', datetime.datetime.now().strftime(SnakePipelineUtils.DATE_FORMAT)),
        ('Input file(s):', input_files),
    ]
    if ('read_type' in args) and (args.read_type is not None):
        read_type = args.read_type if ('fasta' in args) and (args.fasta is None) else 'NA'
        data.append(('Read type:', read_type))
    if additional_info is not None:
        data.extend(additional_info)
    section.add_table(data, table_attributes=[('class', 'information')])
    return section


def determine_sample_name(args: argparse.Namespace) -> str:
    """
    Determines the sample names based on the given command line arguments.
    :return: Sample name
    """
    if ('sample_name' in args) and (args.sample_name is not None):
        return args.sample_name
    elif ('fasta_name' in args) and (args.fasta_name is not None):
        return Path(args.fasta_name).stem
    elif ('fasta' in args) and (args.fasta is not None):
        return Path(args.fasta).stem
    elif args.fastq_pe is not None:
        names = [Path(x) for x in args.fastq_pe_names] if args.fastq_pe_names else [Path(x) for x in args.fastq_pe]
        try:
            # See if it matches a standard FASTQ format
            return FastqUtils.get_sample_name(names[0])
        except ValueError:
            # Check if it matches a Galaxy format
            return FastqUtils.determine_sample_name_from_fq(names, True, 'NA')
    elif args.fastq_se is not None:
        names = [Path(args.fastq_se_name if args.fastq_se_name else args.fastq_se)]
        return FastqUtils.determine_sample_name_from_fq(names, False, 'NA')
    logging.warning("Cannot determine sample name from given arguments")
    return 'NA'


def init_report(output_path: Path, output_dir: Path, title: str, header: str) -> HtmlReport:
    """
    Initializes the HTML report.
    :param output_path: Output path
    :param output_dir: Output directory
    :param title: Report title
    :param header: Report header
    :return: Report
    """
    jquery_src = pkg_resources.resource_filename('camel', 'resources/jquery-3.2.1.min.js')
    report = HtmlReport(output_path, output_dir, [Path(jquery_src)])
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    css_style = pkg_resources.resource_filename('camel', 'resources/style.css')
    report.initialize(title, Path(css_style))
    report.add_pipeline_header(header)
    report.save()
    return report


def prepare_galaxy_output(output_dir: Path, output_html: Path) -> None:
    """
    Prepares the Galaxy output files at the start of the script.
    - The output HTML file is removed, so Snakemake can regenerate it
    - The output directory is created if it does not exist yet.
    :param output_dir: Output directory
    :param output_html: Output report path
    :return: None
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    if output_html.exists():
        output_html.unlink()


def dict_merge(dct: Dict[str, Any], merge_dct) -> None:
    """
    Recursive dict merge. Inspired by :meth:``dict.update()``, instead of updating only top-level keys,
    dict_merge recurses down into dicts nested to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct`` (https://gist.github.com/angstwad/bf22d1822c38a92ec0a9).
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]
