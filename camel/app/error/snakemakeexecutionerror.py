class SnakemakeExecutionError(RuntimeError):
    """
    This error is raised when a Snakemake execution error occurs.
    """

    def __init__(self, stdout: str, stderr: str) -> None:
        """
        This class is raised when a snakemake error occurs.
        :param stdout: Standard output
        :param stderr: Error output
        """
        super().__init__()
        self.stdout = stdout
        self.stderr = stderr
