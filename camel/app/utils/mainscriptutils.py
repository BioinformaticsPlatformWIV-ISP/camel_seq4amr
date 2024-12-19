"""
Contains helper function for main scripts with a report output.
"""
import argparse
import collections
import datetime
from pathlib import Path
from typing import Optional, List, Any, Dict

import pkg_resources

from camel.app.utils.report.htmlreport import HtmlReport
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.snakemake.snakepipelineutils import SnakePipelineUtils


def generate_analysis_info_section(
        args: argparse.Namespace, additional_info: Optional[List[List[str]]] = None) -> HtmlReportSection:
    """
    Generates the report section with the analysis info.
    :param args: Command line arguments
    :param additional_info: Additional info to add to the report section
    :return: Analysis info section
    """
    section = HtmlReportSection('Analysis info')
    input_files = args.fasta.name if args.fasta_name is None else args.fasta_name
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


def sanitize_input_name(name: str, extension: str) -> str:
    """
    Sanitizes the input file name.
    :param name: Name
    :param extension: Expected file extension (e.g., 'bam' or 'fasta')
    :return: None
    """
    invalid_chars = '/!@#$\\"'

    # Replace spaces by dashes
    name = name.replace(' ', '_')

    # Avoid double dot before the extension
    if name.endswith('.'):
        name = name[:-1]

    # Add extension
    name = ''.join(c for c in name if c not in invalid_chars)
    if not name.endswith(f'.{extension}'):
        return f'{name}.{extension}'

    # Return sample name without invalid characters
    return name
