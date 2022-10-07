import logging

from camel.app.utils.blasttyping.cluster import Cluster


class BlastHitClustering(object):
    """
    Class that clusters overlapping BlastHit objects.
    Hits are considered overlapping if:
    - They are located on the same contig
    - They have at least one base overlap
    """

    @staticmethod
    def cluster_overlapping(hits):
        """
        Clusters the given blast hits into groups of overlapping hits.
        :param hits: Hits
        :return: Clusters
        """
        clusters = []
        while len(hits) > 0:
            new_cluster = Cluster(hits[0])
            for hit in hits[1:]:
                if new_cluster.overlaps(hit):
                    new_cluster.add_hit(hit)
            for hit in new_cluster.hits:
                hits.remove(hit)
            clusters.append(new_cluster)
        BlastHitClustering.__log_clusters(clusters)
        logging.info('{} clusters of overlapping hits found'.format(len(clusters)))
        return clusters

    @staticmethod
    def __log_clusters(clusters):
        """
        Logs the clusters.
        :param clusters: Clusters
        :return: None
        """
        for cluster in clusters:
            logging.debug('Cluster {}:'.format(clusters.index(cluster) + 1))
            for hit in cluster.hits:
                logging.debug(str(hit))
