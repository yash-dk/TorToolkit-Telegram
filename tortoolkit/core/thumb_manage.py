# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from ..functions import vids_helpers
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
import random

async def get_thumbnail(file_path, user_id = None):
    metadata = extractMetadata(createParser(file_path))
    try:
        duration = metadata.get("duration")
    except:
        duration = 3

    if user_id is not None:
        pass # todo code for custom thumbnails here mostly will be with db
    else:
        path = await vids_helpers.gen_ss(file_path,random.randint(2,duration.seconds))
        path = await vids_helpers.resize_img(path,320)
        return path