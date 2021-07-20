# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import asyncio
import logging

import qbittorrentapi as qba
from aiohttp import web

from . import nodes
from .database_handle import TtkTorrents

torlog = logging.getLogger(__name__)

routes = web.RouteTableDef()

page = """
<html>
<head>
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha256-4+XzXVhsDmqanXGHaHvgh1gMQKX40OUvDEBTu8JcmNs=" crossorigin="anonymous"></script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
  padding: 20px;
}
ul { 
  list-style: none;
  margin: 5px 20px;
}
li {
  margin: 10px 0;
}


p { font-size: 12px; margin: 24px;}
</style>
</head>
<body>
<h1>👇Select the Files that you want to Be downloaded from Below 👇</h1>
<form action="{form_url}" method="POST">

{My_content}

<input type="submit" name="Select these files ;)">
</form>

<script>
$('input[type="checkbox"]').change(function(e) {

  var checked = $(this).prop("checked"),
      container = $(this).parent(),
      siblings = container.siblings();
/*
  $(this).attr('value', function(index, attr){
     return attr == 'yes' ? 'noo' : 'yes';
  });
*/
  container.find('input[type="checkbox"]').prop({
    indeterminate: false,
    checked: checked
  });

  function checkSiblings(el) {

    var parent = el.parent().parent(),
        all = true;

    el.siblings().each(function() {
      let returnValue = all = ($(this).children('input[type="checkbox"]').prop("checked") === checked);
      return returnValue;
    });
    
    if (all && checked) {

      parent.children('input[type="checkbox"]').prop({
        indeterminate: false,
        checked: checked
      });

      checkSiblings(parent);

    } else if (all && !checked) {

      parent.children('input[type="checkbox"]').prop("checked", checked);
      parent.children('input[type="checkbox"]').prop("indeterminate", (parent.find('input[type="checkbox"]:checked').length > 0));
      checkSiblings(parent);

    } else {

      el.parents("li").children('input[type="checkbox"]').prop({
        indeterminate: true,
        checked: false
      });

    }

  }

  checkSiblings(container);
});
</script>
</body>
</html>

"""

code_page = """
<html>
<head>
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" integrity="sha384-JcKb8q3iqJ61gNV9KGb8thSsNjpSL0n8PARn9HuZOnIxN0hoP+VmmDGMN5t9UJ0Z" crossorigin="anonymous">
<title>
TorToolKitX Torrent Files
</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
<div class="container">
<form action="{form_url}">
  <div class="form-group">
    <label for="pin_code">Pin Code</label>
    <input type="text" class="form-control" name="pin_code" placeholder="Enter code to access the torrent">
    <small class="form-text text-muted">Dont mess around. You download will get messed up.</small>
  </div>
  <button type="submit" class="btn btn-primary">Submit</button>
</form>
</div>
</body>
</html>
"""


@routes.get("/tortk/files/{hash_id}")
async def list_torrent_contents(request):
    # not using templates cuz wanted to keem things in one file, might change in future #todo
    torr = request.match_info["hash_id"]

    gets = request.query

    if not "pin_code" in gets.keys():
        rend_page = code_page.replace("{form_url}", f"/tortk/files/{torr}")
        return web.Response(text=rend_page, content_type="text/html")

    client = qba.Client(
        host="localhost", port="8090", username="admin", password="adminadmin"
    )
    client.auth_log_in()
    try:
        res = client.torrents_files(torrent_hash=torr)
    except qba.NotFound404Error:
        raise web.HTTPNotFound()

    # Central object is not used its Acknowledged
    db = TtkTorrents()
    passw = db.get_password(torr)
    if isinstance(passw, bool):
        raise web.HTTPNotFound()
    pincode = passw
    if gets["pin_code"] != pincode:
        return web.Response(text="Incorrect pin code")

    par = nodes.make_tree(res)

    cont = ["", 0]
    nodes.create_list(par, cont)

    rend_page = page.replace("{My_content}", cont[0])
    rend_page = rend_page.replace(
        "{form_url}", f"/tortk/files/{torr}?pin_code={pincode}"
    )
    client.auth_log_out()
    return web.Response(text=rend_page, content_type="text/html")


# this will be a depri if causes more traffic
# mostly will not as internal routing
async def re_verfiy(paused, resumed, client, torr):
    paused = paused.strip()
    resumed = resumed.strip()
    if paused:
        paused = paused.split("|")
    if resumed:
        resumed = resumed.split("|")
    k = 0
    while True:

        res = client.torrents_files(torrent_hash=torr)
        verify = True

        for i in res:
            if str(i.id) in paused:
                if i.priority == 0:
                    continue
                else:
                    verify = False
                    break

            if str(i.id) in resumed:
                if i.priority != 0:
                    continue
                else:
                    verify = False
                    break

        if not verify:
            torlog.info("Reverification Failed :- correcting stuff")
            # reconnect and issue the request again
            client.auth_log_out()
            client = qba.Client(
                host="localhost", port="8090", username="admin", password="adminadmin"
            )
            client.auth_log_in()
            try:
                client.torrents_file_priority(
                    torrent_hash=torr, file_ids=paused, priority=0
                )
            except:
                torlog.error("Errored in reverification paused")
            try:
                client.torrents_file_priority(
                    torrent_hash=torr, file_ids=resumed, priority=1
                )
            except:
                torlog.error("Errored in reverification resumed")
            client.auth_log_out()
        else:
            break
        k += 1
        if k >= 2:
            # avoid an infite loop here
            return False
    return True


@routes.post("/tortk/files/{hash_id}")
async def set_priority(request):
    torr = request.match_info["hash_id"]
    client = qba.Client(
        host="localhost", port="8090", username="admin", password="adminadmin"
    )
    client.auth_log_in()

    data = await request.post()
    resume = ""
    pause = ""
    data = dict(data)

    for i in data.keys():
        if i.find("filenode") != -1:
            node_no = i.split("_")[-1]

            if data[i] == "on":
                resume += f"{node_no}|"
            else:
                pause += f"{node_no}|"

    pause = pause.strip("|")
    resume = resume.strip("|")
    torlog.info(f"Paused {pause} of {torr}")
    torlog.info(f"Resumed {resume} of {torr}")

    try:
        client.torrents_file_priority(torrent_hash=torr, file_ids=pause, priority=0)
    except qba.NotFound404Error:
        raise web.HTTPNotFound()
    except:
        torlog.info("Errored in paused")

    try:
        client.torrents_file_priority(torrent_hash=torr, file_ids=resume, priority=1)
    except qba.NotFound404Error:
        raise web.HTTPNotFound()
    except:
        torlog.info("Errored in resumed")

    await asyncio.sleep(2)
    if not await re_verfiy(pause, resume, client, torr):
        torlog.error("The torrent choose errored reverification failed")
    client.auth_log_out()
    return await list_torrent_contents(request)


@routes.get("/")
async def homepage(request):
    return web.Response(
        text='<h1>🤗TorToolkitX webserver is Up and Running successfully🟢</h1>\n<h2>⚡See TorToolkitX on <a href="https://github.com/XcodersHub/TorToolkitX">@GitHub</a></h2>\n<h2>🥲Join XcodersHub <a href="https://t.me/XcodersHub">TG channel</a></h2>',
        content_type="text/html",
    )


async def e404_middleware(app, handler):
    async def middleware_handler(request):
        try:
            response = await handler(request)
            if response.status == 404:
                return web.Response(
                    text="<h1>404: Page not found</h2><br><h3>TorToolKitX</h3>",
                    content_type="text/html",
                )
            return response
        except web.HTTPException as ex:
            if ex.status == 404:
                return web.Response(
                    text="<h1>404: Page not found</h2><br><h3>TorToolKitX</h3>",
                    content_type="text/html",
                )
            raise

    return middleware_handler


async def start_server():
    # REMOVED HEROKU BLOCK

    app = web.Application(middlewares=[e404_middleware])
    app.add_routes(routes)
    return app


async def start_server_async(port=8080):
    # REMOVED HEROKU BLOCK

    app = web.Application(middlewares=[e404_middleware])
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    # todo provide the config for the host and port for vps only
    await web.TCPSite(runner, "0.0.0.0", port).start()
