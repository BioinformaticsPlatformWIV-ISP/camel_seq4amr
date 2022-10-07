from camel.app.tools.blast.blast import Blast


class Blastn(Blast):
    """
    Nucleotide - nucleotide BLAST.
    """

    def __init__(self) -> None:
        """
        Initialize tool.
        :return: None
        """
        super().__init__('blastn', '2.13.0+')
