import time
from flask import Flask, render_template, request, send_file, redirect, session,jsonify
import os
import sys
import json
from flask_fontawesome import FontAwesome
import zipfile
from werkzeug.utils import secure_filename
from hurry.filesize import size
from datetime import datetime
import filetype
from flask_qrcode import QRcode
from flask import jsonify
import shutil
import logging
import qbittorrentapi as qba
from ..database.dbhandler import TtkTorrents
from . import nodes
from urllib.parse import unquote
import socket    

torlog = logging.getLogger(__name__)
hostname = socket.gethostname()    
IPAddr = socket.gethostbyname(hostname)    
print("Your Computer Name is: " + hostname)    
print("Your Computer IP Address is: " + IPAddr)   
maxNameLength = 15


app = Flask(__name__)

#FoNT AWESOME
fa = FontAwesome(app)

qrcode = QRcode(app)



app.secret_key = 'my_secret_key'

with open('config.json') as json_data_file:
    data = json.load(json_data_file)
hiddenList = data["Hidden"]
favList = data["Favorites"]
# process Fav List
for i in range(len(favList)):
    if favList[i] in ['userdata', 'Downloads']:
        favList[i] = str(os.path.join(os.getcwd(), favList[i]))
password = data["Password"]


rootDir = data["rootDir"]
currentDirectory=rootDir



osWindows = False #Not Windows

default_view = 1

tp_dict = {'image':'photo-icon.png','audio':'audio-icon.png','video':'video-icon.png'}

if 'win32' in sys.platform or 'win64' in sys.platform:
    # import win32api
    osWindows = True

if(len(favList)>3):
    favList=favList[0:3]
    

def make_zipfile(output_filename, source_dir):
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip:
        for root, dirs, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename): # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)



@app.route('/login/')
@app.route('/login/<path:var>')
def loginMethod(var=""):
    global password

    if(password==''):
        session['login'] = True


    if('login' in session):
        return redirect('/'+var)
    else:
        return render_template('login.html')


@app.route('/login/', methods=['POST'])
@app.route('/login/<path:var>', methods=['POST'])
def loginPost(var = ""):
    global password



    text = request.form['text']
    if(text==password):
        session['login'] = True

        return redirect('/'+var)
    else:
        return redirect('/login/'+var)

@app.route('/logout/')
def logoutMethod():
    if('login' in session):
        session.pop('login',None)
    return redirect('/login/')
    
#@app.route('/exit/')
#def exitMethod():
#    exit()




def hidden(path):

    for i in hiddenList:
        if i != '' and i in path:
            return True
    
    return False



def changeDirectory(path):
    global currentDirectory, osWindows


    pathC = path.split('/')
    # print(path)

    if(osWindows):
        myPath = '//'.join(pathC)+'//'
    else:
        myPath = '/'+'/'.join(pathC)

    # print(myPath)
    myPath = unquote(myPath)
    # print("HELLO")
    # print(myPath)

    #print(currentDirectory)
    
    try:
        os.chdir(myPath)
        ans=True
        if (osWindows):
            if(currentDirectory.replace('/','\\') not in os.getcwd()):
                ans = False
        else: 
            if(currentDirectory not in os.getcwd()):
                ans = False
        
    except:
        ans=False
    
    

    return ans
    

@app.route('/changeView')
def changeView():
    global default_view

    # print('view received')

    v = int(request.args.get('view', 0))

    if v in [0,1]:
        default_view = v
    else:
        default_view = 0


    return jsonify({
 
        "txt":default_view,
     
    })



def getDirList():
    # print(default_view)

    global maxNameLength,tp_dict,hostname

    dList = list(os.listdir('.'))
    dList= list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
    dir_list_dict = {}
    fList = list(filter(lambda x: not os.path.isdir(x), os.listdir('.')))
    file_list_dict = {}
    curDir=os.getcwd()
    # print(os.stat(os.getcwd()))



    for i in dList:
        if(hidden(curDir+'/'+i)==False):
            image = 'folder5.png'

            if len(i)>maxNameLength:
                dots = "..."
            else:
                dots = ""

            dir_stats = os.stat(i)
            dir_list_dict[i]={}
            dir_list_dict[i]['f'] = i[0:maxNameLength]+dots
            dir_list_dict[i]['f_url'] = i
            dir_list_dict[i]['currentDir'] = curDir
            dir_list_dict[i]['f_complete'] = i
            dir_list_dict[i]['image'] = image
            dir_list_dict[i]['dtc'] = datetime.utcfromtimestamp(dir_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            dir_list_dict[i]['dtm'] = datetime.utcfromtimestamp(dir_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            dir_list_dict[i]['size'] = "---"


    for i in fList:
        if(hidden(curDir+'/'+i)==False):
            image = None
            try:
                kind = filetype.guess(i)

                if kind:
                    tp = kind.mime.split('/')[0]

                    if tp in tp_dict:
                        image = tp_dict[tp]
            except:
                pass

            if not image:
                image = 'file-test2.png'

            if len(i)>maxNameLength:
                dots = "..."
            else:
                dots = ""
        
            

            file_list_dict[i]={}
            file_list_dict[i]['f'] = i[0:maxNameLength]+dots
            file_list_dict[i]['f_url'] = i
            file_list_dict[i]['currentDir'] = curDir
            file_list_dict[i]['f_complete'] = i
            file_list_dict[i]['image'] = image

            try:
                dir_stats = os.stat(i)
                file_list_dict[i]['dtc'] = datetime.utcfromtimestamp(dir_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                file_list_dict[i]['dtm'] = datetime.utcfromtimestamp(dir_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                file_list_dict[i]['size'] = size(dir_stats.st_size)
            except:
                file_list_dict[i]['dtc'] = "---"
                file_list_dict[i]['dtm'] = "---"
                file_list_dict[i]['size'] = "---"


    return dir_list_dict,file_list_dict


def getFileList():

    dList = list(filter(lambda x: os.path.isfile(x), os.listdir('.')))

    finalList = []
    curDir=os.getcwd()

    for i in dList:
        if(hidden(curDir+'/'+i)==False):
            finalList.append(i)

    return(finalList)





@app.route('/files/', methods=['GET'])
@app.route('/files/<path:var>', methods=['GET'])
def filePage(var = ""):
    global default_view


    if('login' not in session):
        return redirect('/login/files/'+var)

    # print(var)
    if(changeDirectory(var)==False):
        #Invalid Directory
        print("Directory Doesn't Exist")
        return render_template('404.html',errorCode=300,errorText='Invalid Directory Path',favList=favList)
     
    print(default_view)

    try:
        dir_dict,file_dict = getDirList()
        #print(default_view)
        if default_view == 0:
            var1,var2 = "DISABLED",""
            default_view_css_1,default_view_css_2 = '','style=display:none'
        else:
            var1,var2 = "","DISABLED"
            default_view_css_1,default_view_css_2 = 'style=display:none',''


    except:
        return render_template('404.html',errorCode=200,errorText='Permission Denied',favList=favList)
    


    if osWindows:
        cList = var.split('/')
        var_path = '<a style = "color:black;"href = "/files/'+cList[0]+'">'+unquote(cList[0])+'</a>'
        for c in range(1,len(cList)):
            var_path += ' / <a style = "color:black;"href = "/files/'+'/'.join(cList[0:c+1])+'">'+unquote(cList[c])+'</a>'
        
    else:
        cList = var.split('/')
        var_path = '<a href = "/files/"><img src = "/static/root.png" style = "height:25px;width: 25px;">&nbsp;</a>'
        for c in range(0,len(cList)):
            var_path += ' / <a style = "color:black;"href = "/files/'+'/'.join(cList[0:c+1])+'">'+unquote(cList[c])+'</a>'


    return render_template('home.html',currentDir=var,favList=favList,default_view_css_1=default_view_css_1,default_view_css_2=default_view_css_2,view0_button=var1,view1_button = var2,currentDir_path=var_path,dir_dict=dir_dict,file_dict=file_dict)


@app.route('/delete/<path:var>', methods=['GET'])
def deleteResp(var = ""):
    # Not compatible with Windows
    var = "/"+var
    global default_view


    if('login' not in session):
        return redirect('/login/files/'+var)

    # print(var)
    
    #print(default_view)

    try:
        if not os.path.exists(var):
            print(var)
            return jsonify({'status':'error','errorCode':300,'errorText':'Invalid Path'})
        if os.path.isfile(var):
            print("removing file")
            os.remove(var)
        else:
            print("removing dir")
            print(var)
            shutil.rmtree(var)


    except:
        print("404. Page not found.")
        return jsonify({'status':'error','errorCode':404,'errorText':'Permission Denied'})
    

    return jsonify({'status':'success'})



@app.route('/', methods=['GET'])
def homePage():

    global currentDirectory, osWindows

    
    
    return render_template("index.html")
        
        #REDIRECT TO UNTITLED OR C DRIVE FOR WINDOWS OR / FOR MAC



@app.route('/download/<path:var>')
def downloadFile(var):

    if('login' not in session):
        return redirect('/login/download/'+var)
    
    #os.chdir(currentDirectory)

    
    pathC = unquote(var).split('/')
    if(pathC[0]==''):
        pathC.remove(pathC[0])
    
    # if osWindows:
    #     fPath = currentDirectory+'//'.join(pathC)
    # else:
    #     fPath = '/'+currentDirectory+'//'.join(pathC)


    if osWindows:
        fPath = '//'.join(pathC)
    else:
        fPath = '/'+'//'.join(pathC)

    # print("HELLO")
    # print('//'.join(fPath.split("//")[0:-1]))
    # print(hidden('//'.join(fPath.split("//")[0:-1])))

    f_path_hidden = '//'.join(fPath.split("//")[0:-1])



    
    if(hidden(f_path_hidden) == True or changeDirectory(f_path_hidden)== False):
        #FILE HIDDEN
        return render_template('404.html',errorCode=100,errorText='File Hidden',favList=favList)


    fName=pathC[len(pathC)-1]
    #print(fPath)
    return send_file(fPath, download_name=fName)
    try:
        return send_file(fPath, download_name=fName)
    except:
        return render_template('404.html',errorCode=200,errorText='Permission Denied',favList=favList)



@app.route('/downloadFolder/<path:var>')
def downloadFolder(var):

    if('login' not in session):
        return redirect('/login/downloadFolder/'+var)
    

    pathC = var.split('/')
    if(pathC[0]==''):
        pathC.remove(pathC[0])
    
    if osWindows:
        fPath = '//'.join(pathC)
    else:
        fPath = '/'+'//'.join(pathC)
    
    
    
    f_path_hidden = '//'.join(fPath.split("//")[0:-1])
    
    if(hidden(f_path_hidden) == True or changeDirectory(f_path_hidden)== False):
        #FILE HIDDEN
        return render_template('404.html',errorCode=100,errorText='File Hidden',favList=favList)


    fName=pathC[len(pathC)-1]+'.zip'
    
    try:
        make_zipfile('C:\\Users\\reall\\Downloads\\temp\\abc.zip',os.getcwd())
        return send_file('C:\\Users\\reall\\Downloads\\temp\\abc.zip', attachment_filename=fName)
    except:
        return render_template('404.html',errorCode=200,errorText='Permission Denied',favList=favList)


@app.errorhandler(404)
def page_not_found(e):
    if('login' not in session):
        return redirect('/login/')
    
    # note that we set the 404 status explicitly
    return render_template('404.html',errorCode=404,errorText='Page Not Found',favList=favList), 404


@app.route('/upload/', methods = ['GET', 'POST'])
@app.route('/upload/<path:var>', methods = ['GET', 'POST'])
def uploadFile(var=""):

    if('login' not in session):
    
        return render_template('login.html')

    text = ""
    if request.method == 'POST':
        pathC = var.split('/')

        if(pathC[0]==''):
            pathC.remove(pathC[0])
        
        # if osWindows:
        #     fPath = currentDirectory+'//'.join(pathC)
        # else:
        #     fPath = '/'+currentDirectory+'//'.join(pathC)

        if osWindows:
            fPath = +'//'.join(pathC)
        else:
            fPath = '/'+'//'.join(pathC)
    
        f_path_hidden = fPath

        # print(f_path_hidden)
        # print(hidden(f_path_hidden))

        if(hidden(f_path_hidden) == True or changeDirectory(f_path_hidden)== False):
            #FILE HIDDEN
            return render_template('404.html',errorCode=100,errorText='File Hidden',favList=favList)


        files = request.files.getlist('files[]') 
        fileNo=0
        for file in files:
            fupload = os.path.join(fPath,file.filename)

            if secure_filename(file.filename) and not os.path.exists(fupload):
                try:
                    file.save(fupload)    
                    print(file.filename + ' Uploaded')
                    text = text + file.filename + ' Uploaded<br>'
 
                    fileNo = fileNo +1
                except Exception as e:
                    print(file.filename + ' Failed with Exception '+str(e))
                    text = text + file.filename + ' Failed with Exception '+str(e) + '<br>'

                    continue
            else:
                print(file.filename + ' Failed because File Already Exists or File Type Issue')
                text = text + file.filename + ' Failed because File Already Exists or File Type not secure <br>'

            
          
    fileNo2 = len(files)-fileNo
    return render_template('uploadsuccess.html',text=text,fileNo=fileNo,fileNo2=fileNo2,favList=favList)



    
        

@app.route('/qr/<path:var>')
def qrFile(var):
    global hostname

    if('login' not in session):
        return redirect('/login/qr/'+var)
    
    #os.chdir(currentDirectory)
    
    
    pathC = unquote(var).split('/')
    if(pathC[0]==''):
        pathC.remove(pathC[0])
    

    if osWindows:
        fPath = '//'.join(pathC)
    else:
        fPath = '/'+'//'.join(pathC)

    
    f_path_hidden = '//'.join(fPath.split("//")[0:-1])
    
    if(hidden(f_path_hidden) == True or changeDirectory(f_path_hidden)== False):
        #FILE HIDDEN
        return render_template('404.html',errorCode=100,errorText='File Hidden',favList=favList)
    

    fName=pathC[len(pathC)-1]
    #print(fPath)
    # print(fPath)
    qr_text = 'http://'+hostname+"//download//"+fPath

    # print(qr_text)
    return send_file(qrcode(qr_text, mode="raw"), mimetype="image/png")
    return send_file(fPath, attachment_filename=fName)


@app.route('/tortk/files/<path:hashid>/', methods = ['GET'])
def tortkFile(hashid):
    torr = hashid.split("/")[0]
    
    

    pinc = request.args.get("pin_code")

    if pinc is None:
        return render_template('pin_code.html',form_url=f"/tortk/files/{torr}")
        
    
    client = qba.Client(host="localhost",port="8090",username="admin",password="adminadmin")
    client.auth_log_in()
    try:
      res = client.torrents_files(torrent_hash=torr)
    except qba.NotFound404Error:
      return render_template('index.html',err404=True)

    
    # Central object is not used its Acknowledged 
    db = TtkTorrents()
    #passw = db.get_password(torr)
    passw="101010"
    if isinstance(passw,bool):
          return render_template('index.html',err404=True)
    
    if pinc != passw:
        return jsonify({"error":"Wrong Pin Code"})

    
    par = nodes.make_tree(res)
    
    cont = ["",0]
    nodes.create_list(par,cont)


    client.auth_log_out()
    return render_template("file_select.html", My_content=cont[0], form_url=f"/tortk/files/{torr}?pin_code={passw}")

def re_verfiy(paused,resumed,client,torr):
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
            client = qba.Client(host="localhost",port="8090",username="admin",password="adminadmin")
            client.auth_log_in()
            try:
                client.torrents_file_priority(torrent_hash=torr,file_ids=paused,priority=0)
            except:
                torlog.error("Errored in reverification paused")
            try:
                client.torrents_file_priority(torrent_hash=torr,file_ids=resumed,priority=1)
            except:
                torlog.error("Errored in reverification resumed")
            client.auth_log_out()
        else:
            break
        k += 1
        if k == 4:
            # avoid an infite loop here
            return False
    return True

@app.route('/tortk/files/<path:hashid>/', methods = ['POST'])
def tortkFile2(hashid):
    
    torr = hashid.split("/")[0]
    client = qba.Client(host="localhost",port="8090",username="admin",password="adminadmin")
    client.auth_log_in()

    
    
    resume = ""
    pause = ""
    data = request.form
    
    
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
        client.torrents_file_priority(torrent_hash=torr,file_ids=pause,priority=0)
    except qba.NotFound404Error:
        return render_template('index.html',err404=True)
    except:
        torlog.info("Errored in paused")
    
    try:
        client.torrents_file_priority(torrent_hash=torr,file_ids=resume,priority=1)
    except qba.NotFound404Error:
        return render_template('index.html',err404=True)
    except:
        torlog.info("Errored in resumed")

    time.sleep(2)
    if not re_verfiy(pause,resume,client,torr):
        torlog.error("The Torrent chosen had errorred...reverification failed")
    client.auth_log_out()
    return tortkFile(hashid)

if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=True,port=8081)
