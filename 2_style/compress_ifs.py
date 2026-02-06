"""
content = assignment
course  = Python Advanced
 
date    = 14.11.2025
email   = contact@alexanderrichtertd.com
"""



# COMMENT --------------------------------------------------
# Option A: I used a Dictionary to set the options and use it like a switch case. 
# Assuming the function is already being used and I can't change the parameters type or the way it's called.
# Although, for clarity I changed the parameter's name to be more descriptive.

from maya import mel as mc

def set_color(control_list: list[str], color_index:int) -> None:
    """Function to set colors of controls based in an index number.

    Args:
        control_list (list[str]): List of control names to set the color on.
        color_index (int): Index number representing the color to set.
                            Red: 1
                            Green: 2
                            Blue: 3
                            Yellow: 4
                            Magenta: 6
                            Cyan: 7
                            Orange: 8
    """    
    color = {
            1: 4,   # Red
            2: 13,  # Green
            3: 25,  # Blue
            4: 17,  # Yellow
            6: 15,  # Magenta
            7: 6,   # Cyan
            8: 16   # Orange
        }
    
    if not color_index in color:
            print(f"Color index {color_index} is not valid. Please choose from {list(color.keys())}.")
            return

    for control_name in control_list:
        mc.setAttr(control_name + 'Shape.overrideEnabled', 1)
        mc.setAttr(control_name + 'Shape.overrideColor', color[color_index])
            

# EXAMPLE
# controls = mc.ls(selection=True)
# set_color(controls, 8)

# Option B: I use a class to set the options as attributes and make it more readable, easier to use and extend.
# With this approach, I think it's more clear when choosing colors, because they have a human readable name.

from enum import Enum

import pymel.core as pm
class ColorIndex(Enum):
    RED = 4
    GREEN = 13
    BLUE = 25
    YELLOW = 17
    MAGENTA = 15
    CYAN = 6
    ORANGE = 16

def set_color(control_list: list[pm.nt.Transform], color_index:ColorIndex) -> None:
    """Change the color of nurbs control in control_list.

    Args:
        control_list (list[pm.nt.Transform]): List of control objects to set the color on.
        color_index (ColorIndex): ColorIndex enum member representing the color to set.
    """
    for control in control_list:
        shape = control.getShape()
        if not shape: continue
        
        shape.drawOverrideEnabled.set(1)
        shape.drawOverrideColor.set(color_index.value)

#EXAMPLE
# controls = pm.selected()
# set_color(controls, ColorIndex.ORANGE)