# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import asyncio,shlex,os,logging,time
from typing import Union,Optional,List,Tuple

# ref https://info.nrao.edu/computing/guide/file-access-and-archiving/7zip/7z-7za-command-line-guide
torlog = logging.getLogger(__name__)

# TODO change the hard coded value of the size from here

async def cli_call(cmd: Union[str,List[str]]) -> Tuple[str,str]:
    if isinstance(cmd,str):
        cmd = shlex.split(cmd)
    elif isinstance(cmd,(list,tuple)):
        pass
    else:
        return None,None
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stderr=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    
    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()
    
    return stdout, stderr

async def split_in_zip(path,size=None):
    if os.path.exists(path):
        if os.path.isfile(path):
            fname = os.path.basename(path)
            bdir = os.path.dirname(path)
            bdir = os.path.join(bdir,str(time.time()).replace(".",""))
            if not os.path.exists(bdir):
                os.mkdir(bdir)

            if size is None:
                size = 1900
            else:
                size = int(size)
                size = int(size/(1024*1024)) - 10 #for safe
            cmd = f"7z a -tzip '{bdir}/{fname}.zip' '{path}' -v{size}m "

            _, err = await cli_call(cmd)
            
            if err:
                torlog.error(f"Error in zip split {err}")
                return None
            else:
                return bdir
                
        else:
            return None
    else:
        return None

async def add_to_zip(path, size = None):
    if os.path.exists(path):
        fname = os.path.basename(path)
        bdir = os.path.dirname(path)
        bdir = os.path.join(bdir,str(time.time()).replace(".",""))
        if not os.path.exists(bdir):
            os.mkdir(bdir)
        
        bdir = os.path.join(bdir,fname)
        if not os.path.exists(bdir):
            os.mkdir(bdir)
        
        if size is None:
            size = 1900
        else:
            size = int(size)
            size = int(size/(1024*1024)) - 10 #for safe

        total_size = get_size(path)
        if total_size > size:
            cmd = f"7z a -tzip '{bdir}/{fname}.zip' '{path}' -v{size}m "
        else:
            cmd = f"7z a -tzip '{bdir}/{fname}.zip' '{path}'"
    
        _, err = await cli_call(cmd)
        
        if err:
            torlog.error(f"Error in zip split {err}")
            return None
        else:
            return bdir
    else:
        return None

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size/(1024*1024)

async def extract_archive(path, password=""):
    if os.path.exists(path):
        if os.path.isfile(path):
            if str(path).endswith((".zip", "7z", "tar", "gzip2", "iso", "wim")):
                # check userdata
                userpath = os.path.join(os.getcwd(), "userdata")
                if not os.path.exists(userpath):
                    os.mkdir(userpath)
                
                extpath = os.path.join(userpath, str(time.time()).replace(".",""))
                os.mkdir(extpath)
                
                extpath = os.path.join(extpath,os.path.basename(path))
                if not os.path.exists(extpath):
                    os.mkdir(extpath)

                cmd = f"7z e -y '{path}' '-o{extpath}' '-p{password}'"
                
                out, err = await cli_call(cmd)
                
                if err:
                    if "Wrong password" in err:
                        return "Wrong Password"
                    else:
                        torlog.error(err)
                        torlog.error(out)
                        return False
                else:
                    return extpath
        else:
            # False means that the stuff can be upload but cant be extracted as its a dir
            return False
    else:
        # None means fetal error and cant be ignored
        return None 

#7z e -y {path} {ext_path}
#/setpassword jobid password