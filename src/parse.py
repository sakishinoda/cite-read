# How to handle bibliography? BBL, BIB, in-line?
import re
from tex2py import tex2py
from TexSoup import TexSoup

class Section(object):
    def __init__(self, title, span):
        self.start = span[0]
        self.end = span[1]
        self.title = title
        self.content = None
        self.cites = None

def partition_by_cmd(cmd, soup):
    cmds = [el for el in soup.descendants if hasattr(el, 'name') and el.name == cmd]
    text = str(soup)
    contents = []
    start_idxs = [text.find(str(cmd)) for cmd in cmds]
    for i in range(len(start_idxs)-1):
        contents.append(
            (
                cmds[i],
                text[start_idxs[i]: start_idxs[i+1]].lstrip(str(cmds[i]))
            )
        )
    return contents