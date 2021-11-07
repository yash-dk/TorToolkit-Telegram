# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import os
import shutil
async def clear_stuff(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except:pass
    