import asyncio
import os
import re
import shutil
import logging

from instaloader import Instaloader, LoginRequiredException, NodeIterator, Post, Profile, BadCredentialsException, TwoFactorAuthRequiredException, ConnectionException, TooManyRequestsException
from natsort import natsorted
from telethon.errors import FloodWaitError

from ..core.thumb_manage import get_thumbnail
from ..core.getVars import get_val

torlog = logging.getLogger(__name__)

# Thanks TO https://github.com/UsergeTeam/Userge/blob/alpha/userge/plugins/misc/instadl.py

# some helpers
def get_caption(post: Post) -> str:
    """adds link to profile for tagged users"""
    caption = post.caption
    replace = '<a href="https://instagram.com/{}/">{}</a>'
    for mention in post.caption_mentions:
        men = "@" + mention
        val = replace.format(mention, men)
        caption = caption.replace(men, val)
    header = f"♥️<code>{post.likes}</code>  💬<code>{post.comments}</code>"
    if post.is_video:
        header += f"  👀`{post.video_view_count}`"
    caption = header + "\n\n" + (caption or "")
    return caption


async def upload_to_tg(
    message, dirname: str, post: Post, sender_id: int
) -> None:  # pylint: disable=R0912
    """uploads downloaded post from local to telegram servers"""
    pto = (".jpg", ".jpeg", ".png", ".bmp")
    vdo = (".mkv", ".mp4", ".webm")
    paths = []
    if post.typename == "GraphSidecar":
        # upload media group
        captioned = False
        caption = ""
        media = []
        for path in natsorted(os.listdir(dirname)):
            ab_path = dirname + "/" + path
            paths.append(ab_path)
            if str(path).endswith(pto):
                if captioned:
                    media.append(ab_path)
                else:
                    media.append(ab_path)
                    caption = get_caption(post)[:1023]
                    caption += (
                        f"\n\n<a href='tg://user?id={sender_id}'>Done</a>\n#uploads\n"
                    )
                    captioned = True
            elif str(path).endswith(vdo):
                if captioned:
                    media.append(ab_path)
                else:
                    media.append(ab_path)
                    caption = get_caption(post)[:1023]
                    caption += (
                        f"\n\n<a href='tg://user?id={sender_id}'>Done</a>\n#uploads\n"
                    )
                    captioned = True
        if media:
            await message.client.send_file(
                message.chat_id,
                media,
                caption=caption,
                parse_mode="html",
                reply_to=message.id,
            )
            # await message.client.send_media_group(Config.LOG_CHANNEL_ID, media)

    if post.typename == "GraphImage":
        # upload a photo
        for path in natsorted(os.listdir(dirname)):
            if str(path).endswith(pto):
                ab_path = dirname + "/" + path
                paths.append(ab_path)
                await message.client.send_file(
                    message.chat_id,
                    ab_path,
                    caption=get_caption(post)[:1023]
                    + f"\n\n<a href='tg://user?id={sender_id}'>Done</a>\n#uploads\n",
                    parse_mode="html",
                    reply_to=message.id,
                )

    if post.typename == "GraphVideo":
        # upload a video
        for path in natsorted(os.listdir(dirname)):
            if str(path).endswith(vdo):
                ab_path = dirname + "/" + path
                paths.append(ab_path)
                thumb = await get_thumbnail(ab_path)

                await message.client.send_file(
                    entity=message.chat_id,
                    file=ab_path,
                    thumb=thumb,
                    caption=get_caption(post)[:1023]
                    + f"\n\n<a href='tg://user?id={sender_id}'>Done</a>\n#uploads\n",
                    parse_mode="html",
                    reply_to=message.id,
                )
                if thumb is not None:
                    try:
                        os.remove(thumb)
                    except:
                        pass
    for del_p in paths:
        if os.path.lexists(del_p):
            os.remove(del_p)


# run some process in threads?


def download_post(client: Instaloader, post: Post) -> bool:
    """Downloads content and returns True"""
    client.download_post(post, post.owner_username)
    return True


def get_post(client: Instaloader, shortcode: str) -> Post:
    """returns a post object"""
    return Post.from_shortcode(client.context, shortcode)


def get_profile(client: Instaloader, username: str) -> Profile:
    """returns profile"""
    return Profile.from_username(client.context, username)


def get_profile_posts(profile: Profile) -> NodeIterator[Post]:
    """returns a iterable Post object"""
    return profile.get_posts()


# pylint: disable=R0914, R0912, R0915, R0911
async def _insta_post_downloader(message):
    """download instagram post"""
    omess = await message.get_reply_message()
    if omess is None:
        await message.reply("Reply to a Instagram Link.")
        return
    message = await message.reply("`Setting up Configs. Please don't flood.`")
    dirname = "instadl_{target}"
    filename = "{target}'s_post"
    insta = Instaloader(
        dirname_pattern=dirname,
        filename_pattern=filename,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )
    if get_val("INSTA_UNAME") is not None and get_val("INSTA_PASS") is not None:
        login = True
    else:
        login = False

    if login:
        try: 
            insta.login(get_val("INSTA_UNAME"), get_val("INSTA_PASS"))
            torlog.info("InstaDL running in Logged Mode")
        except (
            BadCredentialsException,
            TwoFactorAuthRequiredException,
            ConnectionException,
            TooManyRequestsException,
        ) as e:
            await message.edit(f"**InstaDL ERROR:** " + str(e))
            torlog.warning(str(e))
    else:
        torlog.info("Insta-DL running without credentials")
        await message.edit(
            "Login Credentials not found.\n`[NOTE]`: "
            "**Private stuff will not be downloaded**"
        )
        await asyncio.sleep(2)

    p = r"^https:\/\/www\.instagram\.com\/(p|tv|reel)\/([A-Za-z0-9\-_]*)\/(\?igshid=[a-zA-Z0-9]*)?$"
    match = re.search(p, omess.raw_text)
    print(omess.raw_text)
    if False:
        # have plans here
        pass
    elif match:
        dtypes = {"p": "POST", "tv": "IGTV", "reel": "REELS"}
        d_t = dtypes.get(match.group(1))
        if not d_t:
            await message.edit("Unsupported Format")
            return
        await message.edit(f"`Fetching {d_t} Content.`")
        shortcode = match.group(2)
        post = get_post(insta, shortcode)
        try:
            download_post(insta, post)
            await upload_to_tg(
                message,
                dirname.format(target=post.owner_username),
                post,
                sender_id=omess.sender_id,
            )
        except (KeyError, LoginRequiredException):
            await message.edit("Post is private. Cant Download")
            return
        except FloodWaitError as f_w:
            await asyncio.sleep(f_w.seconds + 5)
            await upload_to_tg(
                message,
                dirname.format(target=post.owner_username),
                post,
                sender_id=omess.sender_id,
            )
        finally:
            shutil.rmtree(
                dirname.format(target=post.owner_username), ignore_errors=True
            )

    else:
        await message.edit("`Invalid Link that you provided`")
