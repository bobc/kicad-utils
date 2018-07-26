# -*- coding: utf-8 -*-

#
# This code was taken without change from https://github.com/KiCad/kicad-library-utils/tree/master/sch.
# It's covered by GPL3.
#

import sys
import re

class Description(object):
    """
    A class to parse description information of KiCad Schematic Files
    TODO: Need to be done, currently just stores the raw data read from file
    """
    def __init__(self, data):
        self.raw_data = data

class SchematicItem (object):
    """
    Base class for schematic objects
    """
    def __init__(self, data):
        pass

    def get_text (self):
        return []

class Component(SchematicItem):
    """
    Component
    """
    _L_KEYS = ['name', 'ref']
    _U_KEYS = ['unit', 'convert', 'time_stamp']
    _P_KEYS = ['posx', 'posy']
    _AR_KEYS = ['path', 'ref', 'part']
    _F_KEYS = ['id', 'ref', 'orient', 'posx', 'posy', 'size', 'attributes', 'hjust', 'props', 'name']

    _KEYS = {'L':_L_KEYS, 'U':_U_KEYS, 'P':_P_KEYS, 'AR':_AR_KEYS, 'F':_F_KEYS}
    def __init__(self, data):
        self.labels = {}
        self.unit = {}
        #self.position = {}
        self.references = []
        self.fields = []
        #self.old_stuff = []
        
        for line in data:
            if line[0] == '\t':
                #self.old_stuff.append(line)
                self.rotation = line.strip()
                continue

            line = line.replace('\n', '')

            # Extract all the non-quoted and quoted text pieces, accounting for escaped quotes. 
            pieces = re.findall(r'[^\s"]+|(?<!\\)".*?(?<!\\)"', line)

            line = []
            for i in range(len(pieces)):
                # Merge a piece ending with equals sign with the next piece.
                if pieces[i] and pieces[i][-1] == '=':
                    pieces[i] = pieces[i] + pieces[i+1]
                    pieces[i+1] = ''  # Empty the next piece because it was merged with this one.
                # Append any non-empty piece.
                if pieces[i]:
                    line.append(pieces[i])

            # select the keys list and default values array
            if line[0] in self._KEYS:
                key_list = self._KEYS[line[0]]
                values = line[1:] + ['' for n in range(len(key_list) - len(line[1:]))]

            if line[0] == 'L':
                self.labels = dict(zip(key_list,values))
            elif line[0] == 'U':
                self.unit = dict(zip(key_list,values))
            elif line[0] == 'P':
                #self.position = dict(zip(key_list,values))
                self.posx = values[0]
                self.posy = values[1]
            elif line[0] == 'AR':
                self.references.append(dict(zip(key_list,values)))
            elif line[0] == 'F':
                self.fields.append(dict(zip(key_list,values)))

    # TODO: error checking
    # * check if field_data is a dictionary
    # * check if at least 'ref' and 'name' were passed
    # * ignore invalid items of field_data on merging
    # TODO: enhancements
    # * 'value' could be used instead of 'ref'
    def addField(self, field_data):
        def_field = {'id':None, 'ref':None, 'orient':'H', 'posx':'0', 'posy':'0', 'size':'50',
                     'attributes':'0001', 'hjust':'C', 'props':'CNN', 'name':'~'}

        # merge dictionaries and set the id value
        field = dict(list(def_field.items()) + list(field_data.items()))
        field['id'] = str(len(self.fields))

        self.fields.append(field)
        return field

    def get_text (self):
        to_write = []
        to_write += ['$Comp\n']
        if self.labels:
            line = 'L '
            for key in self._L_KEYS:
                line += self.labels[key] + ' '
            to_write += [line.rstrip() + '\n']

        if self.unit:
            line = 'U '
            for key in self._U_KEYS:
                line += self.unit[key] + ' '
            to_write += [line.rstrip() + '\n']

        to_write += ["P %s %s\n" % (self.posx, self.posy)]

        for reference in self.references:
            if self.references:
                line = 'AR '
                for key in self._AR_KEYS:
                    line += reference[key] + ' '
                to_write += [line.rstrip() + '\n']

        for field in self.fields:
            line = 'F '
            for key in self._F_KEYS:
                line += field[key] + ' '
            to_write += [line.rstrip() + '\n']

        to_write += ["\t%s %s %s\n" % (self.unit['unit'], self.posx, self.posy)]
        to_write += ["\t%s\n" % (self.rotation)]

        to_write += ['$EndComp\n']
        return to_write

class Sheet(SchematicItem):
    """
    Container for hierarchical Sheet object
    """
    _S_KEYS = ['posx', 'posy','width', 'height']
    _U_KEYS = ['uniqID']
    _F_KEYS = ['id', 'value', 'IOState', 'side', 'posx', 'posy', 'size']

    _KEYS = {'S':_S_KEYS, 'U':_U_KEYS, 'F':_F_KEYS}

    def __init__(self, data):
        #self.shape = {}
        self.unique_id = ""
        self.fields = []
        # F0 is sheet name
        # F1 is sheet file name
        # F2.. are hierarchical pins
        for line in data:

            line = line.replace('\n', '')

            # Extract all the non-quoted and quoted text pieces, accounting for escaped quotes. 
            pieces = re.findall(r'[^\s"]+|(?<!\\)".*?(?<!\\)"', line)

            line = []
            for i in range(len(pieces)):
                # Merge a piece ending with equals sign with the next piece.
                if pieces[i] and pieces[i][-1] == '=':
                    pieces[i] = pieces[i] + pieces[i+1]
                    pieces[i+1] = ''  # Empty the next piece because it was merged with this one.
                # Append any non-empty piece.
                if pieces[i]:
                    line.append(pieces[i])

            # select the keys list and default values array
            if line[0] in self._KEYS:
                key_list = self._KEYS[line[0]]
                values = line[1:] + ['' for n in range(len(key_list) - len(line[1:]))]

            if line[0] == 'S':
                #self.shape = dict(zip(key_list,values))
                self.posx = values[0]
                self.posy = values[1]
                self.width = values[2]
                self.height = values[3]

            elif line[0] == 'U':
                self.unique_id = values[0]

            elif line[0][0] == 'F':
                key_list = self._F_KEYS
                values = line + ['' for n in range(len(key_list) - len(line))]
                self.fields.append(dict(zip(key_list,values)))

    def get_text (self):
        to_write = []
        to_write += ['$Sheet\n']
        line = "S %s %s %s %s\n" % (self.posx, self.posy, self.width, self.height)
        to_write += [line]

        line = 'U '
        line += self.unique_id
        to_write += [line.rstrip() + '\n']

        for field in self.fields:
            line = ''
            for key in self._F_KEYS:
                line += field[key] + ' '
            to_write += [line.rstrip() + '\n']

        to_write += ['$EndSheet\n']
        return to_write

class Bitmap(SchematicItem):
    """
    A container for bitmaps
    TODO: Need to be done, currently just stores the raw data read from file
    """
    def __init__(self, data):

        tokens = data[1].split()
        self.posx = tokens[1]
        self.posy = tokens[2]

        tokens = data[2].split()
        self.scale = tokens[1]

        # Data ... EndData
        self.bitmap_data = data [3:-1]

    def get_text (self):
        to_write = ["$Bitmap\n"]
        to_write += ["Pos %s %s\n" % (self.posx, self.posy)]
        to_write += ["Scale %s\n" % (self.scale)]
        to_write += self.bitmap_data
        to_write += ["$EndBitmap\n"]
        return to_write

class Wire(SchematicItem):
    """
    Wire objects - 
        Wire Wire Line       - regular connecting wires
        Wire Bus Line        - bus lines
        Wire Notes Line      - documentary lines
    """
    def __init__(self, data):
        self.raw_data = data

        tokens = data[0].split()
        self.type1 = tokens[1]
        self.type2 = tokens[2]

        tokens = data[1].split()
        self.startx = tokens[0]
        self.starty = tokens[1]
        self.endx = tokens[2]
        self.endy = tokens[3]

    def get_text (self):
        to_write = []
        to_write += ["Wire %s %s\n" % (self.type1, self.type2),
                         "\t%s %s %s %s\n" % (self.startx, self.starty, self.endx, self.endy)]
        return to_write

class Entry(SchematicItem):
    """
    Entry objects -
        wire-bus entry
        bus-bus entry    
    """
    def __init__(self, data):
        self.raw_data = data

        tokens = data[0].split()
        self.type1 = tokens[1]
        self.type2 = tokens[2]

        tokens = data[1].split()
        self.startx = tokens[0]
        self.starty = tokens[1]
        self.endx = tokens[2]
        self.endy = tokens[3]

    def get_text (self):
        to_write = []
        to_write += ["Entry %s %s\n" % (self.type1, self.type2),
                         "\t%s %s %s %s\n" % (self.startx, self.starty, self.endx, self.endy)]
        return to_write

class Text (SchematicItem):
    """
    Text objects - 
        Notes   documentary text
        Label   local label
        GLabel  global label
        HLabel  hierarchical label
    """
    def __init__(self, data):
        self.raw_data = data

        # type = Label Notes GLabel HLabel

        tokens = data[0].split()
        self.type = tokens[1]
        self.posx = tokens[2]
        self.posy = tokens[3]
        self.orientation = tokens[4]
        self.textsize = tokens[5]

        if self.type in ["GLabel", "HLabel"]:
            self.shape = tokens[6]
            self.italic = True if tokens[7] == "Italic" else False
            self.bold = True if len(tokens)>8 and tokens[8] != "0" else False
        else:
            self.shape = ""
            self.italic = True if tokens[6] == "Italic" else False
            self.bold = True if len(tokens)>7 and tokens[7] != "0" else False

        line = data[1].rstrip()
        self.data = line

    def get_text (self):
        to_write = []
        if self.type in ["GLabel", "HLabel"]:
            to_write += ["Text %s %s %s %s %s %s %s %s\n" % (
                            self.type, self.posx, self.posy, self.orientation, self.textsize, self.shape,
                            "Italic" if self.italic else "~",
                            10 if self.bold else 0),
                            self.data+'\n']
        else:
            to_write += ["Text %s %s %s %s %s %s %s\n" % (
                            self.type, self.posx, self.posy, self.orientation, self.textsize,
                            "Italic" if self.italic else "~",
                            10 if self.bold else 0),
                            self.data+'\n']
        return to_write

class Connection(SchematicItem):
    """
    A connection dot aka junction
    """
    def __init__(self, data):
        self.raw_data = data

        tokens = data.split()
        self.posx = tokens[2]
        self.posy = tokens[3]

    def get_text (self):
        to_write = []
        to_write += ["Connection ~ %s %s\n" % (self.posx, self.posy)]
        return to_write

class NoConnect(SchematicItem):
    """
    A No Connect symbol (cross)
    """
    def __init__(self, data):
        self.raw_data = data

        tokens = data.split()
        self.posx = tokens[2]
        self.posy = tokens[3]

    def get_text (self):
        to_write = []
        to_write += ["NoConn ~ %s %s\n" % (self.posx, self.posy)]
        return to_write

class Schematic(object):
    """
    Container for Schematic sheet
    """
    def __init__(self, filename):
        f = open(filename)
        self.filename = filename
        self.header = f.readline()
        self.libs = []
        self.eelayer = None
        self.description = None

        self.components = []
        self.sheets = []
        self.bitmaps = []
        self.texts = []
        self.wires = []
        self.entries = []
        self.conns = []
        self.noconns = []

        self.objects = []

        if not 'EESchema Schematic File' in self.header:
            self.header = None
            sys.stderr.write('The file is not a KiCad Schematic File\n')
            return

        building_block = False

        while True:
            line = f.readline()
            if not line: break

            if line.startswith('LIBS:'):
                self.libs.append(line)

            elif line.startswith('EELAYER END'):
                pass
            elif line.startswith('EELAYER'):
                self.eelayer = line

            elif not building_block:
                if line.startswith('$'):
                    building_block = True
                    block_data = []
                    block_data.append(line)
                elif line.startswith('Text'):
                    data = Text ([line.rstrip(), f.readline().strip()])
                    self.texts.append(data)
                    self.objects.append(data)

                elif line.startswith('Wire'):
                    data = Wire ([line.rstrip(), f.readline().strip()])
                    self.wires.append(data)
                    self.objects.append(data)

                elif line.startswith('Entry'):
                    data = Entry ([line.rstrip(), f.readline().strip()])
                    self.entries.append(data)
                    self.objects.append(data)

                elif line.startswith('Connection'):
                    data = Connection(line)
                    self.conns.append(data)
                    self.objects.append(data)

                elif line.startswith('NoConn'):
                    data = NoConnect(line)
                    self.noconns.append(data)
                    self.objects.append(data)

            elif building_block:
                block_data.append(line)
                if line.startswith('$End'):
                    building_block = False

                    if line.startswith('$EndDescr'):
                        self.description = Description(block_data)
                    if line.startswith('$EndComp'):
                        data=Component(block_data)
                        self.components.append(data)
                        self.objects.append(data)
                    if line.startswith('$EndSheet'):
                        data=Sheet(block_data)
                        self.sheets.append(data)
                        self.objects.append(data)
                    if line.startswith('$EndBitmap'):
                        data=Bitmap(block_data)
                        self.bitmaps.append(data)
                        self.objects.append(data)

    def save(self, filename=None):
        # check whether it has header, what means that sch file was loaded fine
        if not self.header: return

        if not filename: filename = self.filename

        # insert the header
        to_write = []
        to_write += [self.header]

        # LIBS
        to_write += self.libs

        # EELAYER
        to_write += [self.eelayer, 'EELAYER END\n']

        # Description
        to_write += self.description.raw_data

        # 
        for item in self.objects:
            to_write.extend (item.get_text())

        to_write += ['$EndSCHEMATC\n']

        f = open(filename, 'w')
        f.writelines(to_write)
