import re
import bml

def latex_replace_suits_bid(matchobj):
    text = matchobj.group(0)
    text = text.replace('C', '\c')
    text = text.replace('D', '\d')
    text = text.replace('H', '\h')
    text = text.replace('S', '\s')
    text = text.replace('N', 'NT')
    return text

def latex_replace_suits_desc(matchobj):
    text = matchobj.group(1)
    text = text.replace('!c', '\c')
    text = text.replace('!d', '\d')
    text = text.replace('!h', '\h')
    text = text.replace('!s', '\s')
    if matchobj.group(2) == ' ':
        text += '\\ '
    elif matchobj.group(2) == '\n':
        text += '\\ \n'
    else:
        text += ' ' + matchobj.group(2)
    return text

def latex_replace_suits_header(matchobj):
    text = matchobj.group(1)
    text = text.replace('!c', '\pdfc')
    text = text.replace('!d', '\pdfd')
    text = text.replace('!h', '\pdfh')
    text = text.replace('!s', '\pdfs')
    if matchobj.group(2) == ' ':
        text += '\\ '
    return text

def latex_bidtable(children, file):
    for i in range(len(children)):
        c = children[i]
        if i > 0 or c.parent.bid != 'root':
            file.write('\\\\\n')
        bid = re.sub(r'\d([CDHS]|N(?!T))+', latex_replace_suits_bid, c.bid)
        bid = re.sub(r'^P$', 'Pass', bid)
        bid = re.sub(r'^R$', 'Rdbl', bid)
        bid = re.sub(r'^D$', 'Dbl', bid)
        bid = re.sub(r';(?=\S)', '; ', bid)
        bid = bid.replace('->', '$\\rightarrow$')
        file.write(bid)
        c.desc = latex_replace_characters(c.desc)
        
        if c.desc:
            desc = re.sub(r'(![cdhs])([^!]?)', latex_replace_suits_desc, c.desc)
            desc = desc.replace('\\n', '\\\\\n\\>')
            file.write(' \\> ' + desc)
        if len(c.children) > 0:
            file.write('\\+') 
            latex_bidtable(c.children, file)
            file.write('\\-')
            
def latex_diagram(diagram, file):
    header = []
    suits = {'S':'\\s ',
             'H':'\\h ',
             'D':'\\d ',
             'C':'\\c '}
    players = {'N':'North',
               'E':'East',
               'S':'South',
               'W':'West'}
    if diagram.board:
        header.append('Board %s' % diagram.board)
    if diagram.dealer and diagram.vul:
        header.append('%s / %s' % (players[diagram.dealer], diagram.vul))
    elif diagram.dealer:
        header.append(diagram.dealer)
    elif diagram.vul:
        header.append(diagram.vul)
    if diagram.contract:
        level, suit, double, player = diagram.contract
        if level == 'P':
            header.append("Pass")
        else:
            contract = level + suits[suit]
            if double:
                contract += double
            contract += ' by %s' % players[player]
            header.append(contract)
    if diagram.lead:
        suit, card = diagram.lead
        lead = 'Lead ' + suits[suit.upper()]
        lead += card
        header.append(lead)

    header = '\\\\'.join(header)
    
    def write_hand(hand, handtype):
        if hand:
            handstring = '{\\%s{%s}{%s}{%s}{%s}}\n' % \
                (handtype, hand[0], hand[1], hand[2], hand[3])
            handstring = handstring.replace('-', '\\void')
            file.write(handstring)
        else:
            file.write('{}\n')
    if diagram.south:
        file.write('\\dealdiagram\n')
        handtype = 'hand'
        if(diagram.west or diagram.east):
            handtype = 'vhand'
        write_hand(diagram.west, handtype)
        write_hand(diagram.north, handtype)
        write_hand(diagram.east, handtype)
        write_hand(diagram.south, handtype)
        file.write('{%s}\n\n' % header)
    elif diagram.north:
        file.write('\\dealdiagramenw\n')
        handtype = 'vhand'
        write_hand(diagram.west, handtype)
        write_hand(diagram.north, handtype)
        write_hand(diagram.east, handtype)
        file.write('{%s}\n\n' % header)
    else:
        file.write('\\dealdiagramew\n')
        handtype = 'vhand'
        write_hand(diagram.west, handtype)
        write_hand(diagram.east, handtype)
        
def replace_quotes(matchobj):
    return "``" + matchobj.group(1) + "''"

def replace_strong(matchobj):
    return '\\textbf{' + matchobj.group(1) + '}'

def replace_italics(matchobj):
    return '\\emph{' + matchobj.group(1) + '}'

def replace_truetype(matchobj):
    return '\\texttt{' + matchobj.group(1) + '}'

def latex_replace_characters(text):
    text = text.replace('->', '$\\rightarrow$')
    text = text.replace('#', '\\#')
    text = text.replace('_', '\\_')
    text = re.sub(r'(?<=\s)"(\S[^"]*)"', replace_quotes, text, flags=re.DOTALL)
    text = re.sub(r'(?<=\s)\*(\S[^*]*)\*', replace_strong, text, flags=re.DOTALL)
    text = re.sub(r'(?<=\s)/(\S[^/]*)/', replace_italics, text, flags=re.DOTALL)
    text = re.sub(r'(?<=\s)=(\S[^=]*)=', replace_truetype, text, flags=re.DOTALL)
    return text
            
def to_latex(content, file):
    with open(file, 'w') as f:
        # the preamble
        # TODO: Config file for the preamble?
        preamble = r"""\documentclass[a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{newcent}
\usepackage{helvet}
\usepackage{graphicx}
\usepackage[pdftex, pdfborder={0 0 0}]{hyperref}
\frenchspacing

\include{bml}
"""

        f.write(preamble)
        if 'TITLE' in bml.meta:
            f.write('\\title{%s}\n' % bml.meta['TITLE'])
        if 'AUTHOR' in bml.meta:
            f.write('\\author{%s}\n' % bml.meta['AUTHOR'])

        f.write('\\begin{document}\n')
        f.write('\\maketitle\n')
        f.write('\\tableofcontents\n\n')
            
        # then start the document
        for c in content:
            content_type, text = c
            if content_type == bml.ContentType.PARAGRAPH:
                text = re.sub(r'(![cdhs])([^!]?)', latex_replace_suits_desc, text)
                text = latex_replace_characters(text)
                f.write(text + '\n\n')
            elif content_type == bml.ContentType.BIDTABLE:
                if not text.export:
                    continue
                f.write('\\begin{bidtable}\n')
                latex_bidtable(text.children, f)
                f.write('\n\\end{bidtable}\n\n')
            elif content_type == bml.ContentType.DIAGRAM:
                latex_diagram(text, f)
            elif content_type == bml.ContentType.H1:
                text = latex_replace_characters(text)
                text = re.sub(r'(![cdhs])( ?)', latex_replace_suits_header, text)
                f.write('\\section{%s}' % text +'\n\n')
            elif content_type == bml.ContentType.H2:
                text = latex_replace_characters(text)
                text = re.sub(r'(![cdhs])( ?)', latex_replace_suits_header, text)
                f.write('\\subsection{%s}' % text +'\n\n')
            elif content_type == bml.ContentType.H3:
                text = latex_replace_characters(text)
                text = re.sub(r'(![cdhs])( ?)', latex_replace_suits_header, text)
                f.write('\\subsubsection{%s}' % text +'\n\n')
            elif content_type == bml.ContentType.H4:
                text = latex_replace_characters(text)
                text = re.sub(r'(![cdhs])( ?)', latex_replace_suits_header, text)
                f.write('\\paragraph{%s}' % text +'\n\n')
            elif content_type == bml.ContentType.LIST:
                f.write('\\begin{itemize}\n')
                for i in text:
                    i = latex_replace_characters(i)
                    i = re.sub(r'(![cdhs])([^!]?)', latex_replace_suits_desc, i)
                    f.write('\\item %s\n' % i)
                f.write('\n\\end{itemize}\n\n')
            elif content_type == bml.ContentType.DESCRIPTION:
                f.write('\\begin{description}\n')
                for i in text:
                    i = latex_replace_characters(i)
                    i = re.sub(r'(![cdhs])([^!]?)', latex_replace_suits_desc, i)
                    i = i.split(' :: ')
                    f.write('\\item[%s] %s\n' % (i[0], i[1]))
                f.write('\n\\end{description}\n\n')
            elif content_type == bml.ContentType.ENUM:
                f.write('\\begin{enumerate}\n')
                for i in text:
                    i = latex_replace_characters(i)
                    i = re.sub(r'(![cdhs])([^!]?)', latex_replace_suits_desc, i)
                    f.write('\\item %s\n' % i)
                f.write('\n\\end{enumerate}\n\n')
            elif content_type == bml.ContentType.TABLE:
                f.write('\\begin{tabular}{')
                columns = 0
                for i in text:
                    if len(i) > columns:
                        columns = len(i)
                f.write('l' * columns)
                f.write('}\n')
                for i in text:
                    if re.match(r'[+-]+$', i[0]):
                        f.write('\\hline\n')
                    else:
                        f.write(' & '.join(i))
                        f.write(' \\\\\n')
                f.write('\\end{tabular}\n\n')
                
        f.write('\\end{document}\n')

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
        
    to_latex(bml.content, outputfile + '.tex')
