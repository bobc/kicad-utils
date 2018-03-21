#-------------------------------------------------------------------------------
# Name:     get_pos
# Purpose:  A script to output a pos file, similar to KiCad output. This script also outputs PTH components.
#           Note : this version works with KiCad 4.0.7
#
# Author:   Bob Cousins
# License:  Creative Commons CC0  Copyright Bob Cousins 2018
# Credits:  Based on KiCad function https://github.com/KiCad/kicad-source-mirror/blob/master/pcbnew/exporters/gen_footprints_placefile.cpp#L423
#           
# Usage:
#  1. Save the file "get_pos.py" somewhere
#  2. Open the Python console in pcbnew
#  3. Copy and paste (use Paste Plus) the following lines in to the console:
#     execfile ("c:/python_progs/test_pcb/get_pos.py")
#
#     * change the path to get_pos.py accordingly.
#-------------------------------------------------------------------------------

import os
import sys
import pcbnew
import datetime

"""
A script to output a pos file, similar to KiCad output.
Note : this version works with KiCad 4.0.7
"""

def change_extension (filename, ext):
    path, filename = os.path.split (filename)
    basename = os.path.splitext (filename)[0]
    return os.path.join (path, basename + ext)

def get_class (attributes):
    if attributes == 0:
        return "PTH"
    elif attributes & 1:
        return "SMD"
    else:
        return "VIRT"

def pcbfunc(Filename = None):
    if Filename: 
        my_board = pcbnew.LoadBoard (Filename)
    else:
        my_board = pcbnew.GetBoard()

    filename = change_extension (my_board.GetFileName(), ".pos")

    f = open (filename, "w")

    f.write ("### Module positions - created on %s ###" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    f.write ("### Printed by get_pos v1")
    f.write ("## Unit = mm, Angle = deg.")
    f.write ("## Side : All")
    f.write ("# Ref     Val        Package                PosX       PosY       Rot  Side  Type")

    origin = my_board.GetAuxOrigin()

    # for v5 use GetLibItemName() instead of GetFootprintName()
    for module in my_board.GetModules():
        f.write ("%s \"%s\" %s %1.3f %1.3f %1.3f %s %s" % ( module.GetReference(), 
                                    module.GetValue(),
                                    module.GetFPID().GetLibItemName(),
                                    pcbnew.ToMM(module.GetPosition().x - origin.x),
                                    pcbnew.ToMM(-module.GetPosition().y + origin.y),
                                    module.GetOrientation() / 10.0,
                                    "top" if module.GetLayer() == 0 else "bottom",
                                    get_class ( module.GetAttributes() )
                                    ))

    f.write ("## End")

    f.close ()

    print ("Written to %s" % filename)

# pcbfunc("C:\\git_bobc\\bobc_hardware_live\\Smart_RGB_LED_AT85\\rgb_led.kicad_pcb")
pcbfunc()
