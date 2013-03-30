import re
import bml
import xml.etree.ElementTree as ET

def html_bidtable(et_element, children):
    if len(children) > 0:
        ul = ET.SubElement(et_element, 'ul')
        for c in children:
            li = ET.SubElement(ul, 'li')
            div = ET.SubElement(li, 'div')
            div.attrib['class'] = 'start'
            div.text = c.bid
            div.tail = c.desc
            html_bidtable(li, c.children)

def html_replace_suits(matchobj):
    text = matchobj.group(0)
    text = text.replace('C', '<span class="ccolor">&clubs;</span>')
    text = text.replace('D', '<span class="dcolor">&diams;</span>')
    text = text.replace('H', '<span class="hcolor">&hearts;</span>')
    text = text.replace('S', '<span class="scolor">&spades;</span>')
    text = text.replace('N', 'NT')
    return text

def to_html(content):
    html = ET.Element('html')
    head = ET.SubElement(html, 'head')
    link = ET.SubElement(head, 'link')
    link.attrib['rel'] = 'stylesheet'
    link.attrib['type'] = 'text/css'
    link.attrib['href'] = 'bml.css'
    body = ET.SubElement(html, 'body')

    for c in content:
        content_type, text = c
        if content_type == bml.ContentType.PARAGRAPH:
            element = ET.SubElement(body, 'p')
            element.text = text
        elif content_type == bml.ContentType.BIDTABLE:
            element = ET.SubElement(body, 'div')
            element.attrib['class'] = 'bidtable'
            html_bidtable(element, text.children)
        elif content_type == bml.ContentType.H1:
            element = ET.SubElement(body, 'h1')
            element.text = text
        elif content_type == bml.ContentType.H2:
            element = ET.SubElement(body, 'h2')
            element.text = text
        elif content_type == bml.ContentType.H3:
            element = ET.SubElement(body, 'h3')
            element.text = text
        elif content_type == bml.ContentType.H4:
            element = ET.SubElement(body, 'h4')
            element.text = text
        elif content_type == bml.ContentType.LIST:
            element = ET.SubElement(body, 'ul')
            for l in text:
                li = ET.SubElement(element, 'li')
                li.text = l
        elif content_type == bml.ContentType.ENUM:
            element = ET.SubElement(body, 'ol')
            for l in text:
                li = ET.SubElement(element, 'li')
                li.text = l

    title = ET.SubElement(head, 'title')
    title.text = bml.meta['TITLE']
    htmlstring = str(ET.tostring(html), 'UTF8')

    # Replaces !c!d!h!s with suit symbols
    htmlstring = htmlstring.replace('!c', '<span class="ccolor">&clubs;</span>')
    htmlstring = htmlstring.replace('!d', '<span class="dcolor">&diams;</span>')
    htmlstring = htmlstring.replace('!h', '<span class="hcolor">&hearts;</span>')
    htmlstring = htmlstring.replace('!s', '<span class="scolor">&spades;</span>')

    # Replace "long dashes"
    htmlstring = htmlstring.replace('---', '&mdash;')
    htmlstring = htmlstring.replace('--', '&ndash;')

    htmlstring = re.sub(r'\d([CDHS]|N(?!T))+', html_replace_suits, htmlstring)

    return htmlstring

if __name__ == '__main__':
    import sys
    import os
    
    outputfile = ''
    if len(sys.argv) < 2:
        print("What's the name of the file you want to convert?")
        outputfile = input()
        if not os.path.exists(outputfile):
            sys.exit('ERROR: File %s was not found!' % outputfile)
        bml.content_from_file(outputfile)
        outputfile = outputfile.split('.')[0]
    else:
        if not os.path.exists(sys.argv[1]):
            sys.exit('ERROR: File %s was not found!' % sys.argv[1])

        bml.content_from_file(sys.argv[1])
        outputfile = os.path.basename(sys.argv[1]).split('.')[0]
        
    h = to_html(bml.content)
    f = open(outputfile + '.htm', 'w')
    f.write(h)
    f.close()
