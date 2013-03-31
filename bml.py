import re
import copy
from collections import defaultdict

content = []

# where we keep copies
clipboard = {}

# meta information about the BML-file, supported:
# TITLE = the name of the system
# DESCRIPTION = a short summary of the system
# AUTHOR = the system's author(s)
# data in meta is only set once, and isn't overwritten
meta = defaultdict(str)

class Node:
    """A node in a bidding table"""
    def __init__(self, bid, desc, indentation, parent=None):
        self.export = True
        self.bid = bid
        self.desc = desc
        self.indentation = indentation
        self.children = []
        self.parent = parent
        bid = re.sub(r'[-;]', '', bid)
        bid = bid.replace('NT', 'N')
        self.bidrepr = bid
        bids = re.findall(r'\d[A-Za-z]+', self.bidrepr)
        if bids and not '(' in self.bidrepr:
            self.bidrepr = 'P'.join(bids)

    def add_child(self, bid, desc, indentation):
        """appends a new child Node to the node"""
        self.children.append(Node(bid, desc, indentation, self))
        return self.children[-1]

    def get_sequence(self):
        """List with all the parent, and the current, bids"""

        if self.parent.bidrepr == 'root':
            return [self.bidrepr]
        if self.parent:
            ps = self.parent.get_sequence()
            ps.append(self.bidrepr)
            return ps

    def set_children(self, children):
        """Used when copying from another Node"""
        self.children = copy.deepcopy(children)
        for c in self.children:
            c.parent = self

    def __getitem__(self, arg):
        return self.children[arg]

def create_bidtree(text):
    global clipboard
    root = Node('root', 'root', -1)
    lastnode = root

    # breaks when no more CUT in bidtable
    while True:
        cut = re.search(r'^\s*#\s*CUT\s+(\S+)\s*\n(.*)#ENDCUT[ ]*\n?',
                         text, flags=re.DOTALL|re.MULTILINE)
        if not cut:
            break
        clipboard[cut.group(1)] = cut.group(2) # group1=key, group2=value
        text = text[:cut.start()]+text[cut.end():]

    # breaks when no more COPY in bidtable
    while True:
        copy = re.search(r'^\s*#\s*COPY\s+(\S+)\s*\n(.*)#ENDCOPY[ ]*\n?',
                         text, flags=re.DOTALL|re.MULTILINE)
        if not copy:
            break            
        clipboard[copy.group(1)] = copy.group(2) # group1=key, group2=value
        text = text[:copy.end(2)]+text[copy.end():]
        text = text[:copy.start()]+text[copy.start(2):]
        
    # breaks when no more PASTE in bidtable
    while True:
        paste = re.search(r'^(\s*)#\s*PASTE\s+(\S+)\s*\n?', text, flags=re.MULTILINE)
        if not paste:
            break
        indentation = paste.group(1)
        lines = clipboard[paste.group(2)].split('\n')
        for l in range(len(lines)):
            lines[l] = indentation + lines[l]
        text = text[:paste.start()] + '\n'.join(lines) + text[paste.end():]
        
    hide = re.search(r'^\s*#\s*HIDE\s*\n', text, flags=re.MULTILINE)
    if hide:
        root.export = False
        text = text[:hide.start()]+text[hide.end():]
    
    for row in text.split('\n'):
        indentation = len(row) - len(row.lstrip())
        row = row.strip()
        bid = row.split(' ')[0]
        desc = ' '.join(row.split(' ')[1:]).strip()
        while indentation < lastnode.indentation:
            lastnode = lastnode.parent
        if indentation > lastnode.indentation:
            lastnode = lastnode.add_child(bid, desc, indentation)
        elif indentation == lastnode.indentation:
            lastnode = lastnode.parent.add_child(bid, desc, indentation)
    return root

class ContentType:
    BIDTABLE = 1
    PARAGRAPH = 2
    H1 = 3
    H2 = 4
    H3 = 5
    H4 = 6
    LIST = 7
    ENUM = 8

def get_content_type(text):
    global meta
    
    if text.startswith('****'):
        return (ContentType.H4, text[4:].lstrip())
    if text.startswith('***'):
        return (ContentType.H3, text[3:].lstrip())
    if text.startswith('**'):
        return (ContentType.H2, text[2:].lstrip())
    if text.startswith('*'):
        return (ContentType.H1, text[1:].lstrip())

    # The first element is empty, therefore [1:]
    if(re.match(r'^\s*-', text)):
        return (ContentType.LIST, re.split

        (r'^\s*-\s*', text, flags=re.MULTILINE)[1:])
    if(re.match(r'^\s*1\.', text)):
        return (ContentType.ENUM, re.split(r'^\s*\d*\.\s*', text, flags=re.MULTILINE)[1:])

    if(re.match(r'^\s*\(?\d[A-Za-z]+', text)):
        return (ContentType.BIDTABLE, create_bidtree(text))

    metamatch = re.match(r'^\s*#\+(\w+):\s*(.*)', text)
    
    if(metamatch):
        keyword = metamatch.group(1)
        if keyword in meta:
            return None
        value = metamatch.group(2)
        meta[keyword] = value
        return None

    if(re.match(r'^\s*#', text)):
        return (ContentType.BIDTABLE, create_bidtree(text))

    if(re.search(r'\S', text)):
        text = re.sub(r'\n +', '\n', text.strip())
        return (ContentType.PARAGRAPH, text)
    
    return None

# def include_file(matchobj):
#     pass
    
def content_from_file(filename):
    global content
    paragraphs = []
    with open(filename, 'r') as f:
        text = f.read()
        # text = re.sub(r'', include_file, text, flags=re.MULTILINE)
        text = re.sub(r'^//.*\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'//.*', '', text)
        paragraphs = re.split(r'([ ]*\n){2,}', text)

    for c in paragraphs:
        content_type = get_content_type(c)
        if content_type:
            content.append(content_type)
            
if __name__ == '__main__':
    # print('To use BML, use the subprograms bml2html, bml2latex or bml2bss')
    content_from_file('test.txt')
