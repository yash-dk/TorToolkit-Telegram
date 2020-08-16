from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin,ChannelParticipantCreator,ChannelParticipantsAdmins
import logging,traceback
torlog = logging.getLogger(__name__)

async def is_admin(client,user_id,chat_id):
    res = await client(GetParticipantRequest(
        channel=chat_id,
        user_id=user_id
    ))

    try:
        if isinstance(res.participant,(ChannelParticipantAdmin,ChannelParticipantCreator,ChannelParticipantsAdmins)):
            return True
        else:
            return False
    except:
        torlog.error("Error in admin check {}".format(traceback.format_exc()))
        return False