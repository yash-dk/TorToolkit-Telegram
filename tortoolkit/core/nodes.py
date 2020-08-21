from anytree import NodeMixin, RenderTree, PreOrderIter
import qbittorrentapi as qba

class TorNode(NodeMixin):
    def __init__(self,name,is_folder=False,is_file=False,parent=None,progress=None,size=None):
        super().__init__()
        self.name = name
        self.is_folder = is_folder
        self.is_file = is_file
        
        if parent:
            self.parent = parent
        if progress:
            self.progress = progress
        if size:
            self.size = size

def get_folders(path):
    path_seperator = "/"
    folders = path.split(path_seperator)
    return folders

def make_tree(res):
    parent = TorNode("Torrent")
    nodes = dict()

    for i in res:
        folders = get_folders(i.name)
        if len(folders) > 1:
            for i in range(len(folders)-1):
                if not (folders[i] in nodes.keys()):
                    if i != 0:
                        nodes[folders[i]] = TorNode(folders[i],True,parent=nodes[folders[i-1]])
                    else:
                        nodes[folders[i]] = TorNode(folders[i],True,parent=parent)
            TorNode(folders[-1],is_file=True,parent=nodes[folders[-2]])
        else:
            TorNode(folders[-1],is_file=True,parent=parent)
    return parent

def print_tree(parent):
    for pre, _, node in RenderTree(parent):
        treestr = u"%s%s" % (pre, node.name)
        print(treestr.ljust(8), node.is_folder, node.is_file)


def create_list(par,msg):
    if par.name != ".unwanted":
        msg[0] += "<ul>"
    for i in par.children:
        if i.is_folder:
            msg[0] += "<li>"
            if i.name != ".unwanted":
                msg[0] += f"<input type=\"checkbox\" name={i.name}> <label for=\"{i.name}\">{i.name}</label>"
            create_list(i,msg)
            msg[0] += "</li>"
        else:
            msg[0] += "<li>"
            msg[0] += f"<input type=\"checkbox\" name={i.name}> <label for=\"{i.name}\">{i.name}</label>"
            msg[0] += "</li>"
    
    if par.name != ".unwanted":
        msg[0] += "</ul>"

