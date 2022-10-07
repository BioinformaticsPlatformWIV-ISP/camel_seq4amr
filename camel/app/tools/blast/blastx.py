from camel.app.tools.blast.blast import Blast


class Blastx(Blast):
    """
    Nucleotide - protein BLAST.
    """

    def __init__(self) -> None:
        """
        Initialize tool.
        :return: None
        """
        super().__init__('blastx', '2.13.0+')
