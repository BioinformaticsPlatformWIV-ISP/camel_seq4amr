class Cluster(object):
    """
    Class that represents a cluster of BlastHit objects.
    """

    def __init__(self, hit):
        """
        Initializes a cluster.
        :param hit: Initial hit
        """
        self.hits = [hit]
        self.seq_id = hit.query
        self._region = set(range(hit.query_start, hit.query_end))

    def add_hit(self, hit):
        """
        Adds a hit to the cluster.
        :param hit: Blast hit
        :return: None
        """
        self.hits.append(hit)
        self._region = self._region.union(list(range(hit.query_start, hit.query_end)))

    def overlaps(self, hit):
        """
        Checks if the given hit overlaps with this cluster.
        :param hit: Blast hit
        :return: True if the hit overlaps with this cluster
        """
        if hit.query != self.seq_id:
            return False
        # noinspection PyTypeChecker
        return len(self._region.intersection(list(range(hit.query_start, hit.query_end)))) != 0
