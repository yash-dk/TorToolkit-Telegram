import asyncio, aria2p, logging, os
from ..core.getVars import get_val
from telethon.errors.rpcerrorlist import MessageNotModifiedError

# referenced from public leech
# pylint: disable=no-value-for-parameter
torlog = logging.getLogger(__name__)

async def aria_start():
    aria2_daemon_start_cmd = []
    # start the daemon, aria2c command
    aria2_daemon_start_cmd.append("aria2c")
    # aria2_daemon_start_cmd.append("--allow-overwrite=true")
    aria2_daemon_start_cmd.append("--daemon=true")
    # aria2_daemon_start_cmd.append(f"--dir={DOWNLOAD_LOCATION}")
    # TODO: this does not work, need to investigate this.
    # but for now, https://t.me/TrollVoiceBot?start=858
    # maybe, :\ but https://t.me/c/1374712761/1142
    aria2_daemon_start_cmd.append("--enable-rpc")
    aria2_daemon_start_cmd.append("--follow-torrent=mem")
    aria2_daemon_start_cmd.append("--max-connection-per-server=10")
    aria2_daemon_start_cmd.append("--min-split-size=10M")
    aria2_daemon_start_cmd.append("--rpc-listen-all=false")
    aria2_daemon_start_cmd.append(f"--rpc-listen-port=8100")
    aria2_daemon_start_cmd.append("--rpc-max-request-size=1024M")
    aria2_daemon_start_cmd.append("--seed-ratio=0.0")
    aria2_daemon_start_cmd.append("--seed-time=1")
    aria2_daemon_start_cmd.append("--split=10")
    aria2_daemon_start_cmd.append(f"--bt-stop-timeout=100")
    #
    torlog.info(aria2_daemon_start_cmd)
    #
    process = await asyncio.create_subprocess_exec(
        *aria2_daemon_start_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    torlog.info(stdout)
    torlog.info(stderr)
    aria2 = aria2p.API(
        aria2p.Client(
            host="http://localhost",
            port=8100,
            secret=""
        )
    )
    return aria2

def add_magnet(aria_instance, magnetic_link, c_file_name):
    try:
        download = aria_instance.add_magnet(
            magnetic_link
        )
    except Exception as e:
        return False, "**FAILED** \n" + str(e) + " \nPlease do not send SLOW links. Read /help"
    else:
        return True, "" + download.gid + ""


def add_torrent(aria_instance, torrent_file_path):
    if torrent_file_path is None:
        return False, "**FAILED** \n\nsomething wrongings when trying to add <u>TORRENT</u> file"
    if os.path.exists(torrent_file_path):
        # Add Torrent Into Queue
        try:
            download = aria_instance.add_torrent(
                torrent_file_path,
                uris=None,
                options=None,
                position=None
            )
        except Exception as e:
            return False, "**FAILED** \n" + str(e) + " \nPlease do not send SLOW links. Read /help"
        else:
            return True, "" + download.gid + ""
    else:
        return False, "**FAILED** \n" + str(e) + " \nPlease try other sources to get workable link"


def add_url(aria_instance, text_url, c_file_name):
    uris = [text_url]
    # Add URL Into Queue
    try:
        download = aria_instance.add_uris(
            uris
        )
    except Exception as e:
        return False, "**FAILED** \n" + str(e) + " \nPlease do not send SLOW links. Read /help"
    else:
        return True, "" + download.gid + ""

async def check_metadata(aria2, gid):
    file = aria2.get_download(gid)
    torlog.info(file)
    if not file.followed_by_ids:
        # https://t.me/c/1213160642/496
        return None
    new_gid = file.followed_by_ids[0]
    torlog.info("Changing GID " + gid + " to " + new_gid)
    return new_gid

async def aria_dl(
    incoming_link,
    c_file_name,
    sent_message_to_update_tg_p
):
    aria_instance = await aria_start()
    # TODO: duplicate code -_-
    if incoming_link.lower().startswith("magnet:"):
        sagtus, err_message = add_magnet(aria_instance, incoming_link, c_file_name)
    elif incoming_link.lower().endswith(".torrent"):
        sagtus, err_message = add_torrent(aria_instance, incoming_link)
    else:
        sagtus, err_message = add_url(aria_instance, incoming_link, c_file_name)
    if not sagtus:
        return sagtus, err_message
    torlog.info(err_message)
    # https://stackoverflow.com/a/58213653/4723940
    op = await check_progress_for_dl(
        aria_instance,
        err_message,
        sent_message_to_update_tg_p,
        None
    )
    if incoming_link.startswith("magnet:"):
        #
        err_message = await check_metadata(aria_instance, err_message)
        #
        await asyncio.sleep(1)
        if err_message is not None:
            op = await check_progress_for_dl(
                aria_instance,
                err_message,
                sent_message_to_update_tg_p,
                None
            )
        else:
            return False, "can't get metadata \n\n#stopped"
    await asyncio.sleep(1)
    if op:
        file = aria_instance.get_download(err_message)
        to_upload_file = file.name
    
        return to_upload_file
    else:
        return False

async def check_progress_for_dl(aria2, gid, event, previous_message):
    try:
        file = aria2.get_download(gid)
        complete = file.is_complete
        if not complete:
            if not file.error_message:
                msg = ""
                # sometimes, this weird https://t.me/c/1220993104/392975
                # error creeps up
                # TODO: temporary workaround
                downloading_dir_name = "N/A"
                try:
                    # another derp -_-
                    # https://t.me/c/1220993104/423318
                    downloading_dir_name = str(file.name)
                except:
                    pass
                #
                msg = f"\nDownloading File: <code>{downloading_dir_name}</code>"
                msg += f"\nSpeed: {file.download_speed_string()} 🔽 / {file.upload_speed_string()} 🔼"
                msg += f"\nProgress: {file.progress_string()}"
                msg += f"\nTotal Size: {file.total_length_string()}"
                msg += f"\n<b>Info:</b>| P: {file.connections} |"
                if file.seeder is False:
                    """https://t.me/c/1220993104/670177"""
                    msg += f"| S: {file.num_seeders} |"
                # msg += f"\nStatus: {file.status}"
                msg += f"\nETA: {file.eta_string()}"
                msg += f"\n<code>/cancel {gid}</code>"
                # LOGGER.info(msg)
                if msg != previous_message:
                    await event.edit(msg,parse_mode="html")
                    previous_message = msg
            else:
                msg = file.error_message
                await event.edit(f"`{msg}`",parse_mode="html")
                return False
            await asyncio.sleep(get_val("EDIT_SLEEP_SECS"))
            return await check_progress_for_dl(
                aria2, gid, event, previous_message
            )
        else:
            await event.edit(f"File Downloaded Successfully: <code>{file.name}</code>",parse_mode="html")
            return True
    except aria2p.client.ClientException:
        pass
    except MessageNotModifiedError:
        pass
    except RecursionError:
        file.remove(force=True)
        await event.edit(
            "Download Auto Canceled :\n\n"
            "Your Torrent/Link {} is Dead.".format(
                file.name
            ),
            parse_mode="html"
        )
        return False
    except Exception as e:
        torlog.info(str(e))
        if " not found" in str(e) or "'file'" in str(e):
            await event.edit(
                "Download Canceled :\n<code>{}</code>".format(file.name),
                parse_mode="html"
            )
            return False
        else:
            torlog.info(str(e))
            await event.edit("<u>error</u> :\n<code>{}</code> \n\n#error".format(str(e)),parse_mode="html")
            return False