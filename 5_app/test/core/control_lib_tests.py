
import importlib

importlib.reload(importlib.import_module("src.core.control_lib"))
importlib.reload(importlib.import_module("src.utility.decorators"))
importlib.reload(importlib.import_module("src.utility.transform_utils"))
importlib.reload(importlib.import_module("src.utility.attribute_utils"))

from src.core.control_lib import *
import pymel.core as pm



locator = pm.spaceLocator(n="my_locator")
locator.t.set([5,5,5])

# Test lazy instance.
name = locator.name() + "_ctrl"
control = Circle(name)
print(control.transform)
print(control.name)
print(control.shapes)
print(control.offset)
print(control.color)
print(control.cvs)

# Test control creation and offset chained creation.
control.create()
control.align_to(locator).create_offset()
print(control.transform)
print(control.name)
print(control.shapes)
print(control.offset)
print(control.color)
print(control.cvs)

# Test name and offset assignation.
control.name = "my_circle_control"
print(control.name)
control.offset = "my_circle_offset"
print(control.offset)

# Test shape editing.
control.shape_orient([0, 90, 0])
control.shape_move([0, 0, 2])
control.shape_scale([2, 2, 2])
control.shape_normal([0, 1, 0])
control.shape_line_thick()
control.shape_line_thin()
control.shape_color_index(ColorIndex.GREEN)

# Test reset and lock channels.
control.color = ColorIndex.RED
control.transform.t.set([10, 10, 10])
control.reset()
control.lock_channels(["t", "r", "s"])

# Test copy and mirror.
copy = control.copy()
print(copy.transform)
mirrored = control.mirror()
print(mirrored.transform)


# Test shapes assignation.
arrow_control = Arrow()
arrow_control.points
arrow_control.create()
arrow_control.name = "arrow_ctrl"

cube_control = Cube()
cube_control.create()
cube_control.name = "cube_ctrl"

arrow_control.transform.t.set([-1,-1,-1])
cube_control.transform.t.set([2,2,2])

print(control.shapes)
control.shapes = arrow_control.shapes
control.shapes = cube_control.shapes
pm.delete(arrow_control.transform, cube_control.transform)
del(cube_control, arrow_control)
print(control.shapes)

circle = Circle("my_super_offset")
circle.transform
circle.shapes
circle.shapes = control.shapes
pm.select(cl=True)
pm.select(circle.name)



# Test all control types creation.
circle  = Circle("circle").create()
semi    = SemiCircle("semi").create()
square  = Square("square").create()
cross   = Cross("cross").create()
arrow   = Arrow("arrow").create()
triangle = Triangle("triangle").create()
pin     = Pin("pin").create()
pin_double = PinDouble("pin_double").create()
orient  = Orient("orient").create()
cube    = Cube("cube").create()
cube_fk = CubeFK("cube_fk").create()
gear    = Gear("gear").create()
ring    = Ring("ring").create()
pyramid = Pyramid("pyramid").create()
bar     = Bar("bar").create()
sphere  = Sphere("sphere").create()
button  = Button("button").create()

slider_A = Slider("smile", [0,1]).create()
slider_B = Slider("corner_height", [-1,1]).create()
slider_B.offset.t.set([0,0,1])

osipa = Osipa("osipa").create()

text = Text("text", text="Hello World").create()


# STORE curve into json.
sel = pm.selected()[0]
control = Circle(sel)
control._store_curve_to_json("control_name")

# LOAD curve from json.
control._load_curve_from_json("control_name")