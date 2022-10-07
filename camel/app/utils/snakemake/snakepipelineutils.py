import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Any, Dict, Optional

import pkg_resources
import yaml

from camel.app.error.snakemakeexecutionerror import SnakemakeExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.io.tooliovalue import ToolIOValue
from camel.app.utils.command import Command
from camel.app.utils.fileutils import FileUtils
from camel.app.utils.report.htmlcitation import HtmlCitation
from camel.app.utils.report.htmlelement import HtmlElement
from camel.app.utils.report.htmlreport import HtmlReport
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.snakemake.snakemakeutils import SnakemakeUtils


class SnakePipelineUtils(object):
    """
    This class contains utility functions for Snakemake pipelines.
    """

    DATE_FORMAT = '%d/%m/%Y - %X'

    @staticmethod
    def init_pipeline_report(output_path: Path, output_dir: Path, pipeline_info: Dict[str, str]) -> HtmlReport:
        """
        Initializes an empty pipeline report.
        :return: Report
        """
        css_style = Path(pkg_resources.resource_filename('camel', 'resources/style.css'))
        jquery_src = Path(pkg_resources.resource_filename('camel', 'resources/jquery-3.2.1.min.js'))
        report = HtmlReport(output_path, output_dir, [jquery_src])
        report.initialize(pipeline_info['name'], css_style)
        report.add_pipeline_header(f"{pipeline_info['title']} {pipeline_info['version']}")
        return report

    @staticmethod
    def create_input_section(sample_name: str, date: datetime, pipeline_version: str, input_files: str,
                             extra_data: List[Tuple[str, str]], key_citation: str = None) -> HtmlReportSection:
        """
        Creates the input section for the HTML report.
        :param sample_name: Sample name
        :param date: Analysis date
        :param pipeline_version: Pipeline version
        :param input_files: Input files
        :param extra_data: Extra data to include in the input section
        :param key_citation: Citation for the pipeline.
        :return: Input report section
        """
        table_data = [
            ['Sample:', sample_name],
            ['Analysis date:', date.strftime(SnakePipelineUtils.DATE_FORMAT)],
            ['Pipeline version:', pipeline_version],
            ['Input files:', input_files],
        ]
        for key, value in extra_data:
            table_data.append([f'{key}:', value])
        section = HtmlReportSection('Input')
        section.add_table(table_data, table_attributes=[('class', 'information')])
        if key_citation is not None:
            section.add_header('Disclaimer', 2)
            section.add_paragraph('If you use this pipeline for your scientific work, please cite:')
            section.add_html_object(HtmlCitation.parse_from_json(key_citation))
        return section

    @staticmethod
    def add_report_content(report: HtmlReport, report_structure: List[Tuple[str, str, List[Path]]]) -> None:
        """
        Adds the content to the HTML report.
        :param report: Report
        :param report_structure: Report structure
        :return: None
        """
        # Add the overview section
        report.add_module_header('Sections')
        section = HtmlReportSection(None)
        overview_list = HtmlElement('ul')
        for title, key, _ in report_structure:
            list_item = HtmlElement('li')
            list_item.add_html_object(HtmlElement('a', title, [('href', '#{}'.format(key))]))
            overview_list.add_html_object(list_item)
        section.add_html_object(overview_list)
        report.add_html_object(section)

        # Add the different sections
        for title, key, items in report_structure:
            report.add_module_header(title, key)
            for pickle in items:
                if not pickle.exists():
                    continue
                section = SnakemakeUtils.load_object(pickle)[0].value
                report.add_html_object(section)
                section.copy_files(report.output_dir)
        report.save()

    @staticmethod
    def create_empty_report_section(title: str, output_file: Path, header_level: int = 3) -> None:
        """
        Creates an empty report section.
        :param title: Section title
        :param output_file: Output file
        :param header_level: Header level
        :return: None
        """
        section = HtmlReportSection(title, header_level)
        section.add_paragraph('Analysis disabled')
        SnakemakeUtils.dump_object([ToolIOValue(section)], output_file)

    @staticmethod
    def symlink_input_files(output_dir: Path, file_paths: List[str], file_names: List[str], sanitize: bool = False) ->\
            List[Path]:
        """
        Creates symlinks with the given names for the given files.
        This can be used for files that come from Galaxy that have a fixed name (dataset_XXXXX.dat).
        :param output_dir: Directory to save symlinks
        :param file_paths: Input file paths
        :param file_names: Input file names
        :param sanitize: If True, file names are sanitized
        :return: List of absolute paths to symlinks
        """
        if len(file_names) != len(file_paths):
            raise ValueError("File names ({}) and file paths ({}) should be the same length".format(
                len(file_names), len(file_paths)))
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        links = []
        for path, name in zip(file_paths, file_names):
            link_path = output_dir / (FileUtils.make_valid(name) if sanitize else name)
            if link_path.is_symlink():
                link_path.unlink()
            link_path.symlink_to(path)
            links.append(link_path)
        return links

    @staticmethod
    def generate_config_file(config_data: Dict[str, Any], output_dir: Path, output_basename: str = 'config.yml') -> str:
        """
        Generates a configuration file for Snakemake in YAML file format.
        :param config_data: Configuration data
        :param output_dir: Output directory
        :param output_basename: Output basename
        :return: Path to config file
        """
        config_path = output_dir / output_basename
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        with config_path.open('w') as handle:
            yaml.dump(config_data, handle)
        logging.info(f"Configuration file created: {config_path}")
        return str(config_path)

    @staticmethod
    def run_snakemake(snakefile: str, config_path: str, targets: List[Path], working_dir: Path,
                      threads: int = 8, resources: Optional[Dict[str, Any]] = None,
                      slurm_args: Optional[Dict[str, int]] = None) -> Command:
        """
        Helper function to run snakemake workflows.
        :param snakefile: Workflow snakefile
        :param config_path: Path to configuration file
        :param targets: Target output files
        :param working_dir: Working directory
        :param threads: Number of threads to use
        :param resources: Dictionary of resources by keyword
        :param slurm_args: Dictionary of slurm arguments
        :return: None
        """
        if not working_dir.exists():
            working_dir.mkdir(parents=True)

        # Construct basic command
        command_parts = [
            'snakemake',
            *[str(x) for x in targets],
            '--snakefile', str(snakefile),
            '--configfile', str(config_path),
            '--cores', str(threads)
        ]

        # Add resources if they are specified
        if resources is not None:
            command_parts.append('--resources')
            for key, value in resources.items():
                command_parts.append(f'{key}={value}')

        # Add slurm submit file and parameters if specified
        if slurm_args is not None:
            command_parts.append(f'--cluster "{slurm_args["cluster"]}"')
            for key, value in slurm_args.items():
                if key != 'cluster':
                    command_parts.append(f'--{key} {value}')

        # Create and run command
        command = Command(' '.join(command_parts))
        command.run(working_dir)
        if command.returncode != 0:
            logging.error(command.stderr)
            logging.error(command.stdout)
            print(command.stdout)
            print(command.stderr)
            raise SnakemakeExecutionError(command.stdout, command.stderr)
        return command

    @staticmethod
    def create_commands_section(tool_informs: List[Dict[str, Any]], working_dir: Path) -> HtmlReportSection:
        """
        Creates a section with an overview of the commands.
        :param tool_informs: Tool informs
        :param working_dir: Working directory
        :return: Commands section
        """
        section = HtmlReportSection('Commands')
        logging.debug(f"Exporting command for {len(tool_informs)} tools")
        for informs in tool_informs:
            header = f"{informs['_name']} - {informs['_tag']}" if '_tag' in informs else informs['_name']
            section.add_header(header, 3)
            command_txt = informs['_command'].replace(str(working_dir), '$WORKING')
            command_txt = command_txt.replace('\n', '<br />\n')
            section.add_html_object(HtmlElement('code', command_txt, [('class', 'command')]))
        return section

    @staticmethod
    def extracts_fq_input(io_dict: Path, key_pe: Optional[str] = 'FASTQ_PE', key_se: Optional[str] = None,
                          keys_se: Optional[List[str]] = None, drop_empty: bool = False, read_type: str = 'PE') -> \
            Dict[str, List[ToolIOFile]]:
        """
        Extracts a specific FASTQ input dictionary from the standardized FASTQ dictionary.
        :param io_dict: Path to input IO file
        :param key_pe: Key for paired end FASTQ files
        :param key_se: Key for single end FASTQ files
        :param keys_se: Separate keys for the forward and reverse SE FASTQ files
        :param drop_empty: If True, keys with no reads are dropped from the output
        :param read_type: Type of reads ('PE' or 'SE')
        :return: Reformatted dictionary
        """
        io = SnakemakeUtils.load_object(io_dict)
        output_dict = {}

        # Single end reads (no paired / orphaned reads available)
        if read_type == 'SE':
            output_dict[key_se] = io['SE']
            return output_dict

        # PE reads
        output_dict[key_pe] = io['PE']

        # Add SE reads
        if keys_se is not None:
            for key_orig, key_new in zip(['SE_FWD', 'SE_REV'], keys_se):
                try:
                    output_dict[key_new] = io[key_orig]
                except KeyError:
                    logging.warning(f"No '{key_orig}' input found")
        elif key_se is not None:
            se_reads = io.get('SE_FWD', []) + io.get('SE_REV', [])
            output_dict[key_se] = se_reads
        else:
            logging.debug(f"No key(s) provided for SE reads")

        # Remove keys that are empty
        if drop_empty:
            for key in list(output_dict.keys()):
                if (output_dict[key] is not None) and (len(output_dict[key]) > 0):
                    continue
                logging.debug(f'Removing empty input: {key}')
                output_dict.pop(key)

        # Return the reformatted dictionary
        return output_dict

    @staticmethod
    def create_citations_section(keys_other: List[str], key_main: Optional[str] = None) -> HtmlReportSection:
        """
        Creates the report section with the citations.
        :param keys_other: List of key for citations for tools and databases
        :param key_main: Key for the main citation of the workflow
        """
        section_citations = HtmlReportSection('Citations')
        if key_main is not None:
            section_citations.add_header('Pipeline', 3)
            section_citations.add_html_object(HtmlCitation.parse_from_json(key_main))
        section_citations.add_header('Tools and databases', 3)
        for citation_key in keys_other:
            section_citations.add_html_object(HtmlCitation.parse_from_json(citation_key))
        return section_citations
