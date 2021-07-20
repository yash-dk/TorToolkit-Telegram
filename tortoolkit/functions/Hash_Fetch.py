# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import logging
from urllib.parse import parse_qs, urlparse

from torrentool.api import Torrent

# logging.basicConfig(level=logging.DEBUG)


def get_hash_magnet(mgt):
    if mgt.startswith("magnet:"):
        _, _, _, _, query, _ = urlparse(mgt)

    qs = parse_qs(query)
    v = qs.get("xt", None)

    if v == None or v == []:
        logging.error('Invalid magnet URI: no "xt" query parameter.')
        return False

    v = v[0]
    if not v.startswith("urn:btih:"):
        logging.error('Invalid magnet URI: "xt" value not valid for BitTorrent.')
        return False

    mgt = v[len("urn:btih:") :]
    return mgt.lower()


def get_hash_file(path):
    tr = Torrent.from_file(path)
    mgt = tr.magnet_link
    return get_hash_magnet(mgt)
