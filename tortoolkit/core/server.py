from aiohttp import web
import qbittorrentapi as qba
from . import nodes
import asyncio,logging

torlog = logging.getLogger(__name__)

routes = web.RouteTableDef()

page = """
<html>
<head>
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha256-4+XzXVhsDmqanXGHaHvgh1gMQKX40OUvDEBTu8JcmNs=" crossorigin="anonymous"></script>
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
<h1>TorToolKit : <a href="#">Github</a></h1>
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

@routes.get('/tortk/files/{hash_id}')
async def list_torrent_contents(request):
    # not using templates cuz wanted to keem things in one file, might change in future #todo

    torr = request.match_info["hash_id"]
    client = qba.Client(host="localhost",port="8090",username="admin",password="adminadmin")
    client.auth_log_in()

    res = client.torrents_files(torrent_hash=torr)
    txt = "<html><form method=\"POST\" action=\"/\"><table>"
    j = 0
    par = nodes.make_tree(res)
    
    cont = ["",0]
    nodes.create_list(par,cont)

    rend_page = page.replace("{My_content}",cont[0])
    rend_page = rend_page.replace("{form_url}",f"/tortk/files/{torr}")

    return web.Response(text=rend_page,content_type='text/html')
    

@routes.post('/tortk/files/{hash_id}')
async def set_priority(request):
    torr = request.match_info["hash_id"]
    client = qba.Client(host="localhost",port="8090",username="admin",password="adminadmin")
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
        client.torrents_filePrio(torrent_hash=torr,file_ids=pause,priority=0)
    except:pass
    try:
        client.torrents_filePrio(torrent_hash=torr,file_ids=resume,priority=1)
    except:pass

    await asyncio.sleep(2)

    return await list_torrent_contents(request)

@routes.get('/')
async def homepage(request):
    return web.Response(text="<h1>See TorTookit <a href=\"#\">@GitHub</a> By YashDK</h1>",content_type="text/html")

async def e404_middleware(app, handler):
  async def middleware_handler(request):
      try:
          response = await handler(request)
          if response.status == 404:
              return web.Response(text="<h1>404: Page not found</h2><br><h3>Tortoolkit</h3>",content_type="text/html")
          return response
      except web.HTTPException as ex:
          if ex.status == 404:
              return web.Response(text="<h1>404: Page not found</h2><br><h3>Tortoolkit</h3>",content_type="text/html")
          raise
  return middleware_handler

app = web.Application(middlewares=[e404_middleware])
app.add_routes(routes)

web.run_app(app)