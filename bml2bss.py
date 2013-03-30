import re
import bml

class Bid:
    """Numeric representation of a bid"""
    def __init__(self, stringrep):
        """Stringrep should be <denomination><kind>"""
        stringrep = stringrep[-2:] # only the last two characters
        denomination = int(stringrep[0])
        assert denomination >0 and denomination <8, 'denomination must be 1--7'
        kind = stringrep[1]
        assert kind in ['C', 'D', 'H', 'S', 'N'], 'kind must be one of CDHSN'

        self.value = self.value(kind, denomination)

    def __str__(self):
        bids = ['C', 'D', 'H', 'S', 'N']
        kind = bids[(self.value) % 5]
        denomination = str((self.value) // 5 + 1)
        return denomination + kind

    def __repr__(self):
        return str(self.value)

    def __cmp__(self, other):
        return self.value - other.value

    def __iadd__(self, other):
        self.value += other
        return self

    def __isub__(self, other):
        self.value -= other
        return self

    def __imul__(self, other):
        # raises the bid by a level. so 2C*2 == 3C, 2C*-1 == 1C
        if other > 0:
            self.value += (other-1)*5
        elif other < 0:
            self.value += other*5
        return self
    
    def value(self, kind, denomination):
        bids = ['C', 'D', 'H', 'S', 'N']
        val = bids.index(kind)
        return val + (denomination-1)* 5

class Sequence:    
    sequence = []
    desc = ''
    vul = ''
    seat = ''
    contested = False
    we_open = False
    #art
    #type

    def __init__(self, sequence, desc=''):
        self.sequence = sequence
        self.desc = desc
        # if the first letter of the sequence is (, then they make the first bid
        self.we_open = sequence[0][0] != '('
    def __str__(self):
        seq=''
        if not self.contested:
            seq = 'P'.join(self.sequence)
        else:
            seq = ''.join(self.sequence)
        seq = seq.replace('(', '')
        return seq.replace(')', '')

    def __repr__(self):
        if not self.contested:
            return self.vul + self.seat + 'P'.join(self.sequence)
        return self.vul + self.seat + ''.join(self.sequence)

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __ne__(self, other):
        return repr(self) != repr(other)

rootsequence = ''
systemdata = []

def systemdata_normal(child):
    # Matches <digit>[CDHSN], P, D and R, all possibly surrounded by ()
    return re.match(r'^((\(?\d[CDHSN]\)?)|(\(?P\)?)|(\(?D\)?)|(\(?R\)?))+\Z', child.bidrepr)

def systemdata_bidtable(children):
    global rootsequence
    children_special = [x for x in children if not systemdata_normal(x)]
    children[:] = [x for x in children if systemdata_normal(x)]
    
    for i in children_special:
        bids_to_add = []

        # special bids of the form <digit><kind>
        # for instance 1HS, 2M, 3m etc
        bid = re.search(r'(\d+)(\w+)', i.bidrepr)
        if(bid):
            denomination = bid.group(1)
            kind = bid.group(2)
            if(re.match(r'[CDHS]+\Z', kind)):
                for k in kind:
                    bids_to_add.append(denomination + k)
            elif(kind == 'M'):
                bids_to_add.append(denomination + 'H')
                bids_to_add.append(denomination + 'S')
            elif(kind == 'm'):
                bids_to_add.append(denomination + 'C')
                bids_to_add.append(denomination + 'D')
            elif(kind.upper() == 'RED'):
                bids_to_add.append(denomination + 'D')
                bids_to_add.append(denomination + 'H')
            elif(kind.upper() == 'X'):
                bids_to_add.append(denomination + 'C')
                bids_to_add.append(denomination + 'D')
                bids_to_add.append(denomination + 'H')
                bids_to_add.append(denomination + 'S')
            elif(kind.upper() in ['STEP', 'STEPS']):
                parentbid = Bid(i.parent.bidrepr[-2:])
                parentbid += int(denomination)
                bids_to_add.append(str(parentbid))
                
        for add in bids_to_add:
            h = bml.Node(add, i.desc, i.indentation, i.parent)
            h.set_children(i.children)
            children.append(h)

    for r in children:
        bid = re.sub(r'[-;]', '', r.bid)
        sequence = r.get_sequence()
        if len(bid) < len(r.bid):
            rootsequence = ''
        if rootsequence:
            sequence.reverse()
            sequence.append(rootsequence)
            sequence.reverse()
        contested = '(' in ''.join(sequence)
        seq = Sequence(sequence, r.desc)
        seq.contested = contested
        if not seq in systemdata:
            systemdata.append(seq)
        else:
            si = systemdata.index(seq)
            if not systemdata[si].desc:
                systemdata[si].desc = r.desc

        if len(bid) < len(r.bid):
            rootsequence = r.bidrepr
                
        systemdata_bidtable(r.children)

def to_systemdata(contents):
    for c in contents:
        rootsequence = ''
        contested = False
        content_type, content = c
        if content_type == bml.ContentType.BIDTABLE:
            systemdata_bidtable(content.children)

def systemdata_to_bss(filename):
    global systemdata
    with open(filename, 'w') as f:
        f.write('*00{'+ bml.meta['TITLE'] +'}=NYYYYYY' + bml.meta['DESCRIPTION'] + '\n')
        for i in systemdata:
            kind = str(i)[-2:]
            if not i.we_open:
                f.write('*')
            # Seat
            f.write('0')
            # Vulnerability
            f.write('0')
            f.write(str(i)+'=')
            # artificial?
            f.write('N')
            # result: clubs, diamonds, hearts, spades, NT, opponents undoubled
            f.write('YYYYYY')
            if re.match(r'\d[CDHSN]', kind):
                # characteristics (signoff, control bid etc)
                f.write('0')
                if kind[1] != 'N':
                    # least/most ammount of cards in suit
                    f.write('08')
            f.write(i.desc+'\n')

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
    
    to_systemdata(bml.content)
    systemdata_to_bss(outputfile + '.bss')
