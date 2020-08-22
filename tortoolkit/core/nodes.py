from anytree import NodeMixin, RenderTree, PreOrderIter
import qbittorrentapi as qba
#from ..functions.Human_Format import human_readable_bytes

class TorNode(NodeMixin):
    def __init__(self,name,is_folder=False,is_file=False,parent=None,progress=None,size=None,priority=None,file_id=None):
        super().__init__()
        self.name = name
        self.is_folder = is_folder
        self.is_file = is_file
        
        if parent is not None:
            self.parent = parent
        if progress is not None:
            self.progress = progress
        if size is not None:
            #self.size = human_readable_bytes(size)
            self.size = size
        if priority is not None:
            self.priority = priority
        if file_id is not None:
            self.file_id = file_id
        

def get_folders(path):
    path_seperator = "/"
    folders = path.split(path_seperator)
    return folders

def make_tree(res):
    parent = TorNode("Torrent")
    #nodes = dict()
    l = 0
    
    for i in res:
        folders = get_folders(i.name)
        if len(folders) > 1:
            previous_node = parent
            for j in range(len(folders)-1):
                current_node = None
                if previous_node is not None:
                    for k in previous_node.children:
                        if k.name == folders[j]:
                            current_node = k 
                            break
                else:
                    for k in parent.children:
                        if k.name == folders[j]:
                            current_node = k
                            break

                if current_node is None:
                    previous_node = TorNode(folders[j],parent=previous_node,is_folder=True)
                else:
                    previous_node = current_node
            TorNode(folders[-1],is_file=True,parent=previous_node,progress=i.progress,size=i.size,priority=i.priority,file_id=l)
            l += 1
        else:
            TorNode(folders[-1],is_file=True,parent=parent,progress=i.progress,size=i.size,priority=i.priority,file_id=l)
            l += 1


    return parent

    # Will be depricated after testing 
    #for i in res:
    #    folders = get_folders(i.name)
    #    if len(folders) > 1:
    #        for j in range(len(folders)-1):
    #            if not (folders[j] in nodes.keys()):
    #                if j != 0:
    #                    nodes[folders[j]] = TorNode(folders[j],True,parent=nodes[folders[j-1]])
    #                else:
    #                    nodes[folders[j]] = TorNode(folders[j],True,parent=parent)
    #        TorNode(folders[-1],is_file=True,parent=nodes[folders[-2]],progress=i.progress,size=i.size,priority=i.priority,file_id=k)
    #        k += 1
    #    else:
    #        TorNode(folders[-1],is_file=True,parent=parent,progress=i.progress,size=i.size,priority=i.priority,file_id=k)
    #        k += 1
    #return parent

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
                msg[0] += f"<input type=\"checkbox\" name=\"foldernode_{msg[1]}\"> <label for=\"{i.name}\">{i.name}</label>"
            create_list(i,msg)
            msg[0] += "</li>"
            msg[1] += 1
        else:
            msg[0] += "<li>"
            if i.priority == 0:
                msg[0] += f"<input type=\"checkbox\" name=\"filenode_{i.file_id}\"> <label for=\"filenode_{i.file_id}\">{i.name}</label>"
                msg[0] += f"<input type=\"hidden\" value=\"off\" name=\"filenode_{i.file_id}\">"
                
            else:
                msg[0] += f"<input type=\"checkbox\" checked name=\"filenode_{i.file_id}\"> <label for=\"filenode_{i.file_id}\">{i.name}</label>"
                msg[0] += f"<input type=\"hidden\" value=\"off\" name=\"filenode_{i.file_id}\">"
            

            msg[0] += "</li>"
    
    if par.name != ".unwanted":
        msg[0] += "</ul>"

