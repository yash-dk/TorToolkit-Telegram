# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin,ChannelParticipantCreator,ChannelParticipantsAdmins
import logging,traceback
from ..core.getVars import get_val
torlog = logging.getLogger(__name__)

#todo add alpha admin if needed

async def is_admin(client,user_id,chat_id):
    try:
        res = await client(GetParticipantRequest(
            channel=chat_id,
            user_id=user_id
        ))

        try:
            if isinstance(res.participant,(ChannelParticipantAdmin,ChannelParticipantCreator,ChannelParticipantsAdmins)):
                return True
            else:
                
                if user_id in get_val("ALD_USR"):
                    return True
                else:
                    return False
        except:
            torlog.error("Error in admin check {}".format(traceback.format_exc()))
            return False
    except Exception as e:
        torlog.error("Error in admin check {}".format(e))
        if user_id in get_val("ALD_USR"):
            return True
        else:
            return False