import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from camel.app.io.tooliofile import ToolIOFile
from camel.app.utils.snakemake.snakemakeutils import SnakemakeUtils


@dataclass(frozen=True)
class FastqInput:
    read_type: str
    pe: Optional[List[ToolIOFile]] = None
    se: Optional[List[ToolIOFile]] = None
    se_fwd: Optional[List[ToolIOFile]] = None
    se_rev: Optional[List[ToolIOFile]] = None
    is_trimmed: bool = False
    is_pe: bool = True

    @property
    def is_paired(self) -> bool:
        """
        Returns true if the read input is paired.
        :return: True if paired, False otherwise
        """
        return self.pe is not None

    def to_fq_dict(self) -> Dict[str, List[ToolIOFile]]:
        """
        Converts the FASTQ input to a input dictionary for the workflow.
        :return: FASTQ dictionary
        """
        if self.is_pe:
            fq_dict = {'PE': self.pe}
            if self.se_fwd is not None:
                fq_dict['SE_FWD'] = self.se_fwd
            if self.se_rev is not None:
                fq_dict['SE_REV'] = self.se_rev
            return fq_dict
        else:
            return {'SE': self.se}

    @staticmethod
    def from_fq_dict(io: Path, read_type: str) -> 'FastqInput':
        """
        Creates a FastqInput from an IO object.
        :param io: IO object
        :param read_type: Read type
        :return: FastqInput
        """
        fq_dict = SnakemakeUtils.load_object(io)
        return FastqInput(
            read_type,
            pe=fq_dict.get('PE'),
            se_fwd=fq_dict.get('SE_FWD'),
            se_rev=fq_dict.get('SE_REV'),
            se=fq_dict.get('SE'),
            is_pe=fq_dict.get('SE') is None
        )

    @staticmethod
    def determine_read_status(path_fq: Path) -> Tuple[str, str]:
        """
        Attempts to determine the forward / reverse state designator of the reads based on the filename.
        This is useful for SRST2 which can have problems with uncommon read names.
        Supported formats: read_1P.fastq, read_1.fastq
        :param path_fq: Path to input FASTQ file
        :return: Forward designator, reverse designator
        """
        if re.match('.*(_[12]P\\.).*', path_fq.name) is not None:
            return '1P', '2P'
        elif re.match('.*(_[12]\\.).*', path_fq.name) is not None:
            return '_1', '_2'
        raise ValueError(f"Cannot determine read name from: {path_fq}")
