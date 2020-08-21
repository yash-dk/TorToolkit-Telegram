from aiohttp import web
import qbittorrentapi as qba
import nodes

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
<form action="/" method="POST">

{My_content}
<input type="submit" name="Select these files ;)">
</form>

<script>
$('input[type="checkbox"]').change(function(e) {

  var checked = $(this).prop("checked"),
      container = $(this).parent(),
      siblings = container.siblings();

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

@routes.get('/')
async def hello(request):
    torr = "937712b36beb9f9e4a878c5acce72250c646443d"
    client = qba.Client(host="localhost",port="8090",username="admin",password="adminadmin")
    client.auth_log_in()
    txt = ""
    res = client.torrents_files(torrent_hash=torr)
    txt = "<html><form method=\"POST\" action=\"/\"><table>"
    j = 0
    par = nodes.make_tree(res)
    
    cont = [""]
    nodes.create_list(par,cont)
        
    return web.Response(text=page.replace("{My_content}",cont[0]),content_type='text/html')

@routes.post('/')
async def hello1(request):
    data = await request.post()
    print(data)
    
    return web.Response(text="got it")


app = web.Application()
app.add_routes(routes)

web.run_app(app)