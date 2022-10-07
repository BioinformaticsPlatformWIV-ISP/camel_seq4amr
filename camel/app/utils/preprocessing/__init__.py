from camel.app.utils.preprocessing.illuminahelper import IlluminaHelper
from camel.app.utils.preprocessing.iontorrenthelper import IonTorrentHelper
from camel.app.utils.preprocessing.nanoporehelper import NanoporeHelper

helper_by_read_type = {
    'illumina': IlluminaHelper,
    'iontorrent': IonTorrentHelper,
    'nanopore': NanoporeHelper
}
