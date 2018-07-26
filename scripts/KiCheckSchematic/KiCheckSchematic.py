#!/usr/bin/env python

import os
import argparse
import sys

common = os.path.abspath(os.path.join(sys.path[0], 'common'))
if not common in sys.path:
    sys.path.append(common)
from print_color import *

import render_lib
import file_util
import sch
from str_utils import *

errors = 0
warnings = 0

def Info (m):
    if args.verbose:
        printer.regular(m)

def Status (m):
    printer.regular(m)

def Warning (m):
    global warnings
    printer.yellow ("warning: " + m)
    warnings +=1

def Error (m):
    global errors
    printer.red ("error: " + m)
    errors +=1

class CheckSchema:
    def __init__ (self):
        pass

    def Load (self, filename):
        self.filename = filename
        self.schema = sch.Schematic (filename)

    def Check(self, project):
        printer.blue ("Checking sheet %s" % (self.schema.filename) )

        for comp in self.schema.components:
            print "%s, %s" % ( comp.labels['ref'], comp.labels ['name'])

            name = comp.labels ['name']
            found = False
            # find comp in list
            for lib in  project.loaded_libs:
                if lib.find_name (name):
                    Status ("%s found in %s (%s)" % (name, lib.name, lib.filename))
                    if found:
                        Warning ("%s found in multiple libs" % name)
                    found = True

            if not found:
                Error("%s not found" % (name))

    def check_pos (self, gridsize, desc, x, y):
        x = int(x)
        y = int(y)
        if x % gridsize == 0 and y % gridsize == 0:
            return
        else:
            Error ("%s is not on grid (%d, %d)" % (desc, x, y))

    def CheckGrid (self, gridsize):
        # todo component items?
        for item in self.schema.components:
            print "comp %s: %s,%s" % ( item.labels['ref'], item.posx, item.posy )

            self.check_pos (gridsize, "comp %s" % item.labels['ref'], item.posx, item.posy)

        for item in self.schema.texts:
            print "text %s: %s,%s" % ( item.data, item.posx, item.posy )

            self.check_pos (gridsize, "text %s" % item.data, item.posx, item.posy)

        for item in self.schema.wires:
            print "wire %s: %s,%s %s,%s" % ( item.type1, item.startx, item.starty, item.endx, item.endy  )

            self.check_pos (gridsize, "wire %s" % item.type1, item.startx, item.starty)
            self.check_pos (gridsize, "wire %s" % item.type1, item.endx, item.endy)

        for item in self.schema.entries:
            print "entry: %s,%s %s,%s" % ( item.startx, item.starty, item.endx, item.endy )

            self.check_pos (gridsize, "entry %s" % item.type1, item.startx, item.starty)
            self.check_pos (gridsize, "entry %s" % item.type1, item.endx, item.endy)

        for item in self.schema.conns:
            print "conn: %s,%s" % ( item.posx, item.posy )

            self.check_pos (gridsize, "junction", item.posx, item.posy)

        for item in self.schema.noconns:
            print "noconn: %s,%s" % ( item.posx, item.posy )

            self.check_pos (gridsize, "noconn", item.posx, item.posy)

        for item in self.schema.bitmaps:
            print "bitmap: %s,%s" % ( item.posx, item.posy )

            self.check_pos (gridsize, "bitmap", item.posx, item.posy)

        for item in self.schema.sheets:
            print "sheet: %s,%s %s,%s" % ( item.posx, item.posy, item.width, item.height )
            self.check_pos (gridsize, "sheet", item.posx, item.posy)

            for f in item.fields:
                if not f['id'] in ["F0", "F1"]:
                    print " field: %s %s,%s" % ( f['id'], f['posx'],  f['posy'])

    def adjust (self, p, offset):
        return str(int(p) + offset)

    def adjust_pos (self, offset):
        # shift by specified offset
        for item in self.schema.components:
            item.posx = self.adjust (item.posx, offset[0])
            item.posy = self.adjust (item.posy, offset[1])

        for item in self.schema.texts:
            item.posx = self.adjust (item.posx, offset[0])
            item.posy = self.adjust (item.posy, offset[1])

        for item in self.schema.wires:
            item.startx = self.adjust (item.startx, offset[0])
            item.starty = self.adjust (item.starty, offset[1])
            item.endx = self.adjust (item.endx, offset[0])
            item.endy = self.adjust (item.endy, offset[1])

        for item in self.schema.entries:
            item.startx = self.adjust (item.startx, offset[0])
            item.starty = self.adjust (item.starty, offset[1])
            item.endx = self.adjust (item.endx, offset[0])
            item.endy = self.adjust (item.endy, offset[1])

        for item in self.schema.conns:
            item.posx = self.adjust (item.posx, offset[0])
            item.posy = self.adjust (item.posy, offset[1])

        for item in self.schema.noconns:
            item.posx = self.adjust (item.posx, offset[0])
            item.posy = self.adjust (item.posy, offset[1])

        for item in self.schema.bitmaps:
            item.posx = self.adjust (item.posx, offset[0])
            item.posy = self.adjust (item.posy, offset[1])

        # todo hierarchical pins
        for item in self.schema.sheets:
            item.posx = self.adjust (item.posx, offset[0])
            item.posy = self.adjust (item.posy, offset[1])

    def align (self, p, gridsize):
        p=int(p)
        p=p - p % gridsize
        return str(p)

    def align_to_grid (self, gridsize):
        # shift by specified offset
        for item in self.schema.components:
            item.posx = self.align (item.posx, gridsize)
            item.posy = self.align (item.posy, gridsize)

        for item in self.schema.texts:
            item.posx = self.align (item.posx, gridsize)
            item.posy = self.align (item.posy, gridsize)

        for item in self.schema.wires:
            item.startx = self.align (item.startx, gridsize)
            item.starty = self.align (item.starty, gridsize)
            item.endx = self.align (item.endx, gridsize)
            item.endy = self.align (item.endy, gridsize)

        for item in self.schema.entries:
            item.startx = self.align (item.startx, gridsize)
            item.starty = self.align (item.starty, gridsize)
            item.endx = self.align (item.endx, gridsize)
            item.endy = self.align (item.endy, gridsize)

        for item in self.schema.conns:
            item.posx = self.align (item.posx, gridsize)
            item.posy = self.align (item.posy, gridsize)

        for item in self.schema.noconns:
            item.posx = self.align (item.posx, gridsize)
            item.posy = self.align (item.posy, gridsize)

        for item in self.schema.bitmaps:
            item.posx = self.align (item.posx, gridsize)
            item.posy = self.align (item.posy, gridsize)

        for item in self.schema.sheets:
            item.posx = self.align (item.posx, gridsize)
            item.posy = self.align (item.posy, gridsize)

            for f in item.fields:
                if not f['id'] in ["F0", "F1"]:
                    f['posx'] = self.align (f['posx'], gridsize)
                    f['posy'] = self.align (f['posy'], gridsize)
                    
class Project:
    def __init__ (self):
        self.lib_paths = []
        # add installation defaults
        self.lib_paths.append ("c:\programs\kicad\share\kicad\\template")
        self.lib_paths.append ("c:\programs\kicad\share\kicad\library")

    def Load (self, filename):
        in_libs = False
        self.libs = []

        # add project defined paths
        for line in open (filename, "r"):
            line = line.strip()
            if line.startswith ("[eeschema/libraries]"):
                in_libs = True
            elif in_libs:
                if line.startswith ("["):
                    in_libs = False
                else:
                    self.libs.append (after(line,"="))
            elif line.startswith ("LibDir"):
                line = after (line, "=")
                if line:
                    self.lib_paths.extend(line.split (";"))

        # add project path (default)
        self.lib_paths.append (os.path.split(filename)[0])
        
        # add project cache
        self.libs.append (os.path.join (file_util.get_path(filename), 
                                        file_util.get_filename_without_extension (filename) + "-cache"))

        #print self.lib_paths
        #print self.libs

    def Check (self):
        # TODO: check for unique lib names
        # todo: relative paths

        printer.blue ("Checking library search paths")

        for path in self.lib_paths:
            if os.path.exists (path):
                Info ("found %s" % (path))
            else:
                Error ("%s not found" % (path))

        printer.blue ("Checking libraries")
        self.unique_libs = {}
        self.loaded_libs = []
        for lib in self.libs:
            found = False

            libname = os.path.basename (lib)

            if libname in self.unique_libs:
                Warning ("%s is already defined" % (lib))
            else:
                self.unique_libs [libname] = 1

            if "\\" in lib or "/" in lib:
                full_path = lib + ".lib"
                if os.path.exists (full_path):
                    Info ("found %s" % (full_path))
                    found = True

                    Info ("loading %s" % full_path)
                    Lib = render_lib.SymbolLibrary ()
                    Lib.Load (full_path)
                    self.loaded_libs.append (Lib)

            else:
                for path in self.lib_paths:
                    full_path = os.path.join (path, lib+".lib")
                    if os.path.exists (full_path):
                        Info ("found %s" % (full_path))
                        if found:
                            Warning ("lib found on multiple paths %s" % (full_path))
                        else:
                            found = True

                        Info ("loading %s" % full_path)
                        Lib = render_lib.SymbolLibrary ()
                        Lib.Load (full_path)
                        self.loaded_libs.append (Lib)

            if not found:
                Error ( "%s not found" % (lib))

        #


def ExitError( msg ):
    print(msg)
    sys.exit(-1)

#
# main
#
parser = argparse.ArgumentParser(description="Check schematic libraries")

parser.add_argument("--project", help="KiCad project file")
parser.add_argument('--nocolor', help='does not use colors to show the output', action='store_true')
parser.add_argument("-v", "--verbose", help="Enable verbose output", action="store_true")

parser.add_argument("--check_grid",   help="check for grid alignment", action='store_true')
parser.add_argument("--fix_grid",     help="fix grid alignment", action='store_true')
parser.add_argument("--grid",         help="grid size (mils) [100]", default=100)

args = parser.parse_args()

if not args.project:
    ExitError("error: project name not supplied (need --project)")

printer = PrintColor(use_color = not args.nocolor)

if args.check_grid or args.fix_grid:
    if not args.check_grid and not args.fix_grid:
        args.check_grid = True

    file = file_util.change_extension (args.project, ".sch")
    checker = CheckSchema()
    checker.Load (file)

    if args.check_grid:
        checker.CheckGrid(args.grid)

    #checker.adjust_pos ([50,0])
    if args.fix_grid:
        checker.align_to_grid(100)
        checker.schema.save()

else:

    # get library list from .pro
    # for each sch file
    #file = "C:\Python_progs\component_demo\demo\demo_STM32_new\demo_STM32.pro"

    file = args.project
    project = Project ()
    project.Load(file)
    project.Check()

    file = file_util.change_extension (args.project, ".sch")

    checker = CheckSchema()
    checker.Load (file)
    checker.Check(project)

    printer.blue ("Warnings : %s" % warnings)
    printer.blue ("Errors   : %s" % errors)



