# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import random

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from ..functions import vids_helpers


async def get_thumbnail(file_path, user_id=None):
    metadata = extractMetadata(createParser(file_path))
    try:
        duration = metadata.get("duration")
    except:
        duration = 3

    if user_id is not None:
        pass  # todo code for custom thumbnails here mostly will be with db
    else:
        path = await vids_helpers.gen_ss(file_path, random.randint(2, duration.seconds))
        path = await vids_helpers.resize_img(path, 320)
        return path
