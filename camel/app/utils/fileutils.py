import binascii
import datetime
import fileinput
import gzip
import hashlib
import logging
import pickle
import re
from pathlib import Path
from typing import List, Any

from camel.app.utils.command import Command


class FileUtils(object):
    """
    This class contains utility function to work with the file system.
    """

    TIMESTAMP_FILENAME = "%Y%m%d-%H%M%S"

    @staticmethod
    def make_valid(value: str) -> str:
        """
        Converts arbitrary strings to URL- and filename friendly values.
        :param value: Input value
        :return: URL- and filename friendly value
        """
        value = value.replace(' ', '_')
        return "".join([c for c in value if re.match(r'[\w\-_\\.]', c)])

    @staticmethod
    def get_file_with_extension(input_folder: Path, extension: str) -> Path:
        """
        Returns a single file with the given extension from the given directory.
        :param input_folder: Input directory
        :param extension: File extension
        :return: Path to file
        """
        all_files = FileUtils.get_files_with_extension(input_folder, extension)
        if len(all_files) == 0:
            raise IOError(f"No {extension} file found in '{input_folder}'")
        elif len(all_files) > 1:
            raise IOError(f"Multiple {extension} files found in '{input_folder}'")
        return all_files[0]

    @staticmethod
    def get_files_with_extension(folder: Path, extension: str) -> List[Path]:
        """
        Returns the files with the given extension from the folder.
        :param folder: Input folder
        :param extension: File extension
        :return: List of paths to files
        """
        return [file_ for file_ in folder.iterdir() if file_.suffix.endswith(extension)]

    @staticmethod
    def get_timestamp_str(timestamp: datetime.datetime = datetime.datetime.now()) -> str:
        """
        Returns the given time stamp as a string that can be used in a filename.
        :param timestamp: Timestamp (default to current time)
        :return: Timestamp as string
        """
        return timestamp.strftime(FileUtils.TIMESTAMP_FILENAME)

    @staticmethod
    def is_gzipped(path: Path) -> bool:
        """
        Checks if the given file is compressed with gzip.
        :param path: Path
        :return: True if gzipped, False otherwise
        """
        with path.open('rb') as handle:
            magic_number = binascii.hexlify(handle.read(2))
        return magic_number == b'1f8b'

    @staticmethod
    def gzip_extract(input_gz_file: Path, output_gz_file: Path) -> None:
        """
        Extracts a GZIP compressed file, the original file is left untouched.
        :param input_gz_file: Input GZ file
        :param output_gz_file: Output path
        :return: None
        """
        logging.info(f"Extracting: {input_gz_file}")
        command = Command(f'gunzip -k -c {input_gz_file} > {output_gz_file}')
        command.run(Path.cwd())
        if not command.returncode == 0:
            raise RuntimeError(f"Cannot extract '{input_gz_file}': {command.stderr}")

    @staticmethod
    def hash_file(file_path: Path, block_size: int = 65536) -> str:
        """
        Creates a hash for the file with a default block size of 65536 and the sha256 algorithm.
        :param file_path: File that needs to be hashed
        :param block_size: Block size to be used
        :return: String of the hash with alphanumeric symbols
        """
        if not file_path.is_file():
            raise IOError(f"'{file_path}' is not a file")
        hasher = hashlib.sha256()
        with file_path.open('rb') as file_to_hash:
            buf = file_to_hash.read(block_size)
            while len(buf) > 0:
                hasher.update(buf)
                buf = file_to_hash.read(block_size)
            return hasher.hexdigest()

    @staticmethod
    def get_all_files(directory_path: Path) -> List[Path]:
        """
        Returns all files in a directory recursively.
        """
        files_list = []
        for entry in directory_path.glob('**/*'):
            if entry.is_file():
                files_list.append(entry)
        return files_list

    @staticmethod
    def hash_directory(path: Path) -> str:
        """
        Creates a hash for a folder with a default block size of 65536 and the sha256 algorithm.
        :param path: Directory path
        :return: String of the hash with alphanumeric symbols
        """
        hasher = hashlib.sha256()
        for file_ in sorted(FileUtils.get_all_files(path)):
            hasher.update(FileUtils.hash_file(file_).encode('ascii'))
        return hasher.hexdigest()

    @staticmethod
    def hash_value(value: Any) -> str:
        """
        Creates a hash for a value.
        :param value: Value
        :return: String of the hash with alphanumeric symbols
        """
        hasher = hashlib.sha256()
        hasher.update(pickle.dumps(value))
        return hasher.hexdigest()

    @staticmethod
    def concatenate_files(output_path: Path, input_files: List[Path]):
        """
        Concatenate the input files specified into one output file. If the input is gzipped,
        the output will also be a gzipped file.
        :param input_files: input files to be concatenated
        :param output_path: Filename of the output
        :return: None
        """
        def get_hook(file):
            if FileUtils.is_gzipped(file):
                return lambda file_name, mode: gzip.open(file_name, mode='rt')
            else:
                return open

        fin = fileinput.input(input_files, openhook=get_hook(input_files[0]))
        output_fn = gzip.open if FileUtils.is_gzipped(input_files[0]) else open
        with output_fn(output_path, 'wt') as fout:
            for line in fin:
                fout.write(line)
        fin.close()
