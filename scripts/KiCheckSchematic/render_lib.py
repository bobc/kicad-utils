#!/usr/bin/env python

"""This code is originally from schlib-render.py"""

import os
import shlex
import sys

from decimal import Decimal


# kicad lib utils
common = os.path.abspath(os.path.join(sys.path[0], 'common'))
if not common in sys.path:
    sys.path.append(common)

#from schlib import *


class BoundingBox(object):
    def __init__(self, minx, maxx, miny, maxy):
        self.minx = minx
        self.maxx = maxx
        self.miny = miny
        self.maxy = maxy

    def __add__(self, other):
        if other == 0:
            return BoundingBox(self.minx, self.maxx, self.miny, self.maxy)
        return BoundingBox(
                min(self.minx, other.minx),
                max(self.maxx, other.maxx),
                min(self.miny, other.miny),
                max(self.maxy, other.maxy))
    __radd__ = __add__

    def __repr__(self):
        return "BoundingBox(%r, %r, %r, %r)" % (
                self.minx, self.maxx, self.miny, self.maxy)

    __str__ = __repr__

    @property
    def width(self):
        return self.maxx - self.minx
    @property
    def height(self):
        return self.maxy - self.miny
    @property
    def centerx(self):
        return (self.maxx + self.minx) / 2
    @property
    def centery(self):
        return (self.maxy + self.miny) / 2


class LineParser(object):
    def __init__(self, f):
        """Initialize a LineParser from a file"""
        self.f = f
        self.stack = []
        self.raw = None
        self.lineno = 0
    def pop(self):
        self.lineno += 1
        if self.stack:
            self.raw = self.stack.pop()
        else:
            self.raw = self.f.readline()
        self.stripped = self.raw.strip()
        try:
            #self.parts = shlex.split(self.stripped)
            #tokens = self.stripped.split()
            #self.parts = []
            #for tok in tokens:
            #    if tok.startswith('"') and tok.endswith('"'):
            #        tok = tok[1:-1]
            #    self.parts.append (tok)
            s = shlex.shlex(self.stripped)
            s.whitespace_split = True
            s.commenters = ''
            s.quotes = '"'
            self.parts = list(s)

        except ValueError:
            self.parts = []
    def push(self):
        self.lineno -= 1
        self.stack.append(self.raw)

    def eof (self):
        if self.raw is None:
            return False
        else:
           return len(self.raw) == 0

    def __bool__(self):
        return self.raw is None or len(self.raw)!=0


    
class KicadObject(object):
    def parse_line_into(self, parser, *values):
        """Parse a shlex-split line into this object's instance variables.
        @param parser - a LineParser positioned at the current line
        @param values - a list of tuples (name, converter); if name is None the
            field will be ignored.
        @return unparsed values
        """
        for field, (name, converter) in zip(parser.parts, values):
            if converter is None:
                value = field
            else:
                try:
                    value = converter(field)
                except (ValueError, TypeError):
                    raise ValueError("could not parse field %r with %s" % (field, converter))
            self.__dict__[name] = value
        return parser.parts[len(values):]

class SchSymbol(KicadObject):
    def __init__(self, stack=None):
        self.fields = []
        self.fplist = []
        self.objects = []
        self.alias = []
        # the following are per name/alias name
        self.description = ""
        self.keywords = ""
        self.datasheet = ""

        self.valid = False
        if stack is not None:
             self.parse_kicad(stack)

    @property
    def name(self):
        return self.fields[1].value

    @property
    def ref(self):
        return self.fields[0].value

    def parse_kicad(self, parser):
        """Parse a KiCad library file into this object.

        @param parser - a LineParser loaded with the file
        """

        state = "root"

        while not parser.eof():
            parser.pop()
            if not parser.raw or parser.raw.startswith("#"):
                continue
            if not parser.parts:
                raise ValueError("shlex could not parse line %d" % parser.lineno)

            if state == "root":
                if parser.parts[0] == "EESchema-LIBRARY":
                    assert parser.parts[1] == "Version"
                    assert Decimal(parser.parts[2]) <= Decimal("2.3")

                elif parser.parts[0] == "DEF":
                    self.parse_line_into(parser,
                            (None, None), # head
                            (None, None), # name
                            (None, None), # ref
                            (None, None), # unused
                            ("text_offset",     int),
                            ("draw_pinnums",    lambda x: x == "Y"),
                            ("draw_pinnames",   lambda x: x == "Y"),
                            ("n_units",         int),
                            ("units_locked",    lambda x: x == "L"),
                            ("flag",            None))


                elif parser.parts[0].startswith("F"):
                    fieldnum = int(parser.parts[0][1:])
                    assert fieldnum == len(self.fields)
                    self.fields.append(Field(self, parser))

                elif parser.parts[0] == "$FPLIST":
                    state = "fplist"

                elif parser.parts[0] == "DRAW":
                    state = "draw"

                elif parser.parts[0] == "ENDDEF":
                    self.fields[0].value = self.fields[0].value.strip ('"')
                    self.fields[1].value = self.fields[1].value.strip ('"')
                    self.valid = True
                    return

                elif parser.parts[0] == "ALIAS":
                    for a in parser.parts[1:]:
                        self.alias.append (a)

                else:
                    #print("Unrecognized line %s" % parser.parts[0], file=sys.stderr)
                    print("Unrecognized line %s" % parser.parts[0])

            elif state == "fplist":
                if parser.parts[0] == "$ENDFPLIST":
                    state = "root"
                else:
                    self.fplist.append (parser.stripped)

            elif state == "draw":
                if parser.parts[0] == "ENDDRAW":
                    state = "root"
                else:
                    objtype = {
                            "X": Pin,
                            "A": Arc,
                            "C": Circle,
                            "P": Polyline,
                            "S": Rectangle,
                            "T": Text }.get(parser.parts[0])
                    if objtype is None:
                        raise ValueError("Unrecognized graphic item %s on line %d" % (parser.parts[0], parser.lineno))
                    self.objects.append(objtype(self, parser))
            else:
                assert False, "invalid state %r" % state

    def __str__(self):
        lines = []
        lines.append(self.name + " : " + self.ref + "?")
        lines.extend(str(i) for i in self.objects)
        return '\n'.join(lines)

    def filter_unit(self, unit):
        self.objects = [i for i in self.objects if (i.unit == unit or i.unit == 0)]

    def filter_convert(self, convert):
        self.objects = [i for i in self.objects if (i.convert == convert or i.convert == 0)]

    def has_convert(self):
        for i in self.objects:
            if i.convert > 1:
                return True
        return False

    def sort_objects(self):
        """Sort the objects into a good drawing order"""

        def sortkey(x):
            if isinstance(x, Pin):
                return 4
            elif isinstance(x, Text):
                return 5
            elif hasattr(x, "fill") and x.fill == "F":
                return 2
            elif hasattr(x, "fill") and x.fill == "f":
                return 0
            else:
                return 1

        self.objects.sort(key=sortkey)

class Field(KicadObject):
    def __init__(self, parent, stack=None):
        self.parent = parent
        if stack is not None:
            self.parse_kicad(stack)

    def assign (self, value, params):
        self.value = value
        self.posx = int (params['posx'])
        self.posy = int (params['posy'])
        self.size = int (params['text_size'])
        self.orient = params['text_orient']
        self.visible = params['visibility'] == "V"
        self.hjust = params['htext_justify']
        self.vjust = params['vtext_justify'][0]

    def parse_kicad(self, parser):
        self.fieldname = "" # Default value
        self.parse_line_into(parser,
                (None, None), # head
                ("value",   None),
                ("posx",    int),
                ("posy",    int),
                ("size",    int),
                ("orient",  None),
                ("visible", lambda x: x == "V"),
                ("hjust",   None),
                ("vjust",   lambda x: x[0]), # CNN -> C
                ("fieldname",   None)) # Optional

    def __str__(self):
        return self.fieldname + ": " + self.value
        
class Pin(KicadObject):
    def __init__(self, parent, parser=None):
        self.parent = parent
        if parser is not None:
            self.parse_kicad(parser)

    def parse_kicad(self, parser):
        self.pin_type = "" # default value
        self.parse_line_into(parser,
                (None, None),   # head
                ("name",    None),
                ("num",     None),
                ("posx",    int),
                ("posy",    int),
                ("length",  int),
                ("dir",     None),
                ("num_size", int),
                ("name_size", int),
                ("unit",    int),
                ("convert", int),
                ("elec_type", None),
                ("pin_type", None))

    def assign(self, parent, params):
        self.parent = parent

        self.name = params['name']
        self.num = params['num']
        self.posx = int(params['posx'])
        self.posy = int(params['posy'])
        self.length = int(params['length'])
        self.dir = params['direction']
        self.name_size = int(params['name_text_size'])
        self.num_size = int(params['num_text_size'])
        self.unit = int(params['unit'])
        self.convert = int(params['convert'])
        self.elec_type = params['electrical_type']
        self.pin_type = params['pin_type']

    def __str__(self):
        return "PIN: %s (%s)" % (self.name, self.num)


class Arc(KicadObject):

    def __init__(self, parent, parser=None):
        self.parent = parent
        if parser is not None:
            self.parse_kicad(parser)

    def assign(self, parent, params):
        self.parent = parent

        self.posx = int (params['posx'])
        self.posy = int (params['posy'])
        self.radius = int (params['radius'])
        self.start_angle = int (params['start_angle'])
        self.end_angle = int (params['end_angle'])
        self.unit = int (params['unit'])
        self.convert = int (params['convert'])
        self.thickness = int (params['thickness'])
        self.fill = params['fill']
        self.startx = int (params['startx'])
        self.starty = int (params['starty'])
        self.endx = int (params['endx'])
        self.endy = int (params['endy'])

    def parse_kicad(self, parser):
        self.parse_line_into(parser,
                (None, None), # head
                ("posx",    int),
                ("posy",    int),
                ("radius",  int),
                ("start_angle", int),
                ("end_angle", int),
                ("unit",    int),
                ("convert", int),
                ("thickness", int),
                ("fill",    None),
                ("startx",  int),
                ("starty",  int),
                ("endx",    int),
                ("endy",    int))

    def __str__(self):
        return "ARC"


class Circle(KicadObject):
    def __init__(self, parent, parser=None):
        self.parent = parent
        if parser is not None:
            self.parse_kicad(parser)

    def parse_kicad(self, parser):
        self.parse_line_into(parser,
                (None, None),   # head
                ("posx",    int),
                ("posy",    int),
                ("radius",  int),
                ("unit",    int),
                ("convert", int),
                ("thickness", int),
                ("fill",    None))

    def __str__(self):
        return "CIRCLE"


class Polyline(KicadObject):

    def __init__(self, parent, parser=None):
        self.parent = parent
        if parser is not None:
            self.parse_kicad(parser)

    def assign(self, parent, params):
        self.parent = parent

        self.unit = int(params['unit'])
        self.convert = int(params['convert'])
        self.thickness = int(params['thickness'])
        self.fill = params['unit']

        self.points = []
        for j in range (0, int(params['point_count'])):

            self.points.append ( [ int(params['points'][j*2]), int(params['points'][j*2+1]) ] )


    def parse_kicad(self, parser):
        rest = self.parse_line_into(parser,
                (None, None),   # head
                (None, None),   # npoints
                ("unit",    int),
                ("convert", int),
                ("thickness", int))

        self.points = [(int(rest[i]), int(rest[i+1])) for i in range(0, len(rest)-1, 2)]
        self.fill = rest[-1]

    def __str__(self):
        return "POLYLINE"


class Rectangle(KicadObject):
    def __init__(self, parent, parser=None):
        self.parent = parent
        if parser is not None:
            self.parse_kicad(parser)

    def parse_kicad(self, parser):
        self.parse_line_into(parser,
                (None, None),   # head
                ("startx",  int),
                ("starty",  int),
                ("endx",    int),
                ("endy",    int),
                ("unit",    int),
                ("convert", int),
                ("thickness",   int),
                ("fill",    None))

    def __str__(self):
        return "RECTANGLE"

    def assign(self, parent, params):
        self.parent = parent

        self.startx = int (params['startx'])
        self.starty = int (params['starty'])
        self.endx = int (params['endx'])
        self.endy = int (params['endy'])
        self.unit = int (params['unit'])
        self.convert = int (params['convert'])
        self.thickness = int (params['thickness'])
        self.fill = params['fill']


class Text(KicadObject):
    def __init__(self, parent, parser=None):
        self.parent = parent
        if parser is not None:
            self.parse_kicad(parser)

    def assign(self, parent, params):
        self.parent = parent

        self.direction = int(params['direction'])
        self.posx = int(params['posx'])
        self.posy = int(params['posy'])
        self.size = int(params['text_size'])

        self.unit    = int (params['unit'])
        self.convert = int (params['convert'])
        self.text    = params['text']
        self.italic  = params['italic'] == "Italic"
        self.bold    = int(params['bold']) == 1
        self.hjust   = params['hjustify']
        self.vjust   = params['vjustify']

    def parse_kicad(self, parser):
        self.parse_line_into(parser,
                (None, None),   # head
                ("direction",   int),
                ("posx",    int),
                ("posy",    int),
                ("size",    int),
                (None, None),   # unused
                ("unit",    int),
                ("convert", int),
                ("text",    lambda x: x.replace("~", " ")),
                ("italic",  lambda x: x == "Italic"),
                ("bold",    lambda x: bool(int(x))),
                ("hjust",   None),
                ("vjust",   None))

    def __str__(self):
        return "TEXT"

#
#
#


def change_ext (filename, ext):
    path, filename = os.path.split (filename)
    basename = os.path.splitext (filename)[0]
    return os.path.join (path, basename + ext)

def get_filename_without_extension (filename):
    path, filename = os.path.split (filename)
    basename = os.path.splitext (filename)[0]
    return basename


class SymbolLibrary:
    def __init__(self):
        self.items = []

    def get_item(self, name):
        for item in self.items:
            if item.name == name:
                return item
        return None

    def find_name (self, name):
        for item in self.items:
            if item.name == name or name in item.alias:
                return item
        return None

    # todo : dcm fields per alias
    def load_dcm(self, f):
        item = None

        for line in f:
            if line.startswith("$CMP "):
                name = line.partition(" ")[2].strip()
                item = self.get_item(name)
            elif line.startswith("D ") and item is not None:
                item.description = line.partition(" ")[2].strip()
            elif line.startswith("K ") and item is not None:
                item.keywords = line.partition(" ")[2].strip()
            elif line.startswith("F ") and item is not None:
                item.datasheet = line.partition(" ")[2].strip()
            elif line.startswith("$ENDCMP"):
                item = None

    def Load (self, libfile):

        self.filename = libfile
        self.name = get_filename_without_extension (libfile)
        self.items = []
        with open(libfile) as f:
            parser = LineParser(f)

            while not parser.eof():
                obj = SchSymbol(parser)
                if obj.valid:
                    self.items.append (obj)

        dcmfile = change_ext (libfile, ".dcm")

        if os.path.exists(dcmfile):
            with open(dcmfile) as fdcm:
                self.load_dcm(fdcm)

        #
        return self.items
