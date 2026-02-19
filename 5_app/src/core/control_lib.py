'''
################################################################################################################
Content: Centralized control creation.

Dependency:
    abc
    os 
    json
    pymel.core
    src.utility.transform_utils
    src.utility.attribute_utils

Maya Version tested: 2024

How to:
    - Use: 
        - Import the module and create control instances using the provided classes (e.g., Circle, Square, Text).
        
            e.g 01: Manipulate control properties after creation.
                my_control = Circle(control_name="myCircle")
                my_control.create(normal=Vector.Y_POS)
                my_control.align_to(parent=some_transform_node)
                my_control.create_offset()
                my_control.lock_channels("s", "v")
                my_control.set_line_thick()
                my_control.set_color_index(ColorIndex.BLUE)

            e.g 02: Manipulate control properties using method chaining.
                # Create control.
                my_control = Circle(control_name="myCircle").create(normal=Vector.Z_POS)
                # Manipulate control properties.
                my_control.align_to(parent=some_transform_node).create_offset()
                my_control.lock_channels("s", "v")
                my_control.set_line_thick()

            e.g 03: Cast existing transform node to control instance.
                existing_transform = pm.PyNode("existing_ctrl")
                my_control = Control(control_name=existing_transform)   # Cast existing transform.
                my_control.set_color_rgb([1, 0, 0])                     # Set color to red

            e.g 04: Store new control shape into json library.
                sel = pm.selected()[0]                      # Store selected curve.
                control = Circle(control_name=sel)         # Could be any control class instance.
                control._store_curve_to_json("shape_name")  # Could be a curve with multiple shapes.

            e.g 05: Renaming, offset and shapes assignation.
                my_control = Circle(control_name="my_circle").create()
                my_control.name = "my_circle_control"   # Renames the control transform and its shapes.
                my_control.offset = "my_circle_offset"  # Allows to reassign or move from offset group.
                my_control.shapes = [new_shape1, new_shape2] # Adds new shapes to the control.
        
            
        - WARNING: the Control class is a base class and cannot create controls directly. Use one of its subclasses.

    - Test: Use file in src/test/core/control_lib_tests.py

Author: Francisco Guzmán
Email: francisco.guzmanga@gmail.com    
################################################################################################################
'''

from abc import ABC, abstractmethod
from enum import Enum
import json
import os

import pymel.core as pm

from src.utility import transform_utils as tutils
from src.utility import attribute_utils as autils

from src.utility.attribute_utils import Vector

# I talk about this data file in the class docstring.
JSON_PATH = os.path.join(os.path.dirname(__file__), "shape_points.json")

def get_shape_library():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            return json.load(f)
    return {}

SHAPE_LIBRARY = get_shape_library()

class ColorIndex(Enum):
    RED     = 13
    BLUE    = 6
    YELLOW  = 22
    GREEN   = 14
    PURPLE  = 9
    CYAN    = 18
    MAGENTA = 31
    WHITE   = 16
    BLACK   = 1


class Control(ABC):
    """
    Base class for control creation. I used ABC and @abstractmethod to avoid another developer to 
    instantiate this class and the risk to have an empty create() method or adding a generic circle creation, 
    which would create a confusion of purpose with the Circle class.

    WHY CLASSES
        I chose to use a class for control creation because it allows to 
        encapsulate the management into a single object and simplify its use.

        A FUNCTIONAL approach would look like this:
            import control_lib as lib

            my_control = pm.nt.Transform("existing_control")
            my_shape = my_control.getShape()
            lib.shape_color_index(my_shape, lib.ColorIndex.RED)
            lib.shape_line_thick(my_shape)
            lib.shape_move(my_shape, [0, 1, 0])
            etc...
        
        Instead of this, with the CLASS approach, we can do:
            from control_lib import Control, ColorIndex

            my_control = Circle("existing_control")
            my_control.shape_color_index(ColorIndex.RED)
            my_control.shape_line_thick()
            my_control.shape_move([0, 1, 0])

        I see this approach more intuitive, easier to use and read, and also more maintainable and scalable.

    PARENTING & INHERITANCE
        Another advantage of this class approach its inheritance and scalability. For example in control creation:

        FUNCTIONAL approach of control creation:
            #control = lib.create_control(shape="circle", name="my_circle") # Generic approach, with default normal.
            control = lib.create_circle_control("my_circle")                # Specific approach for circle with default normal.
            lib.shape_move(my_shape, [0, 1, 0])

            # Changing shape on creation may imply changing the logic.
            bar_crv, slider_crv = lib.create_slider_control("my_slider", limits=(0, 10)) 
            lib.shape_move(slider_crv.getShape(), [0, 1, 0])
            
        CLASS approach of control creation:
            control = Circle("my_circle")
            control.create()
            control.shape_normal(Vector.Y_POS)

            # Changing the shape doesn't affect the logic, just the class instantiation:
            slider = Slider("my_slider", limits=(0, 10))
            slider.create()
            slider.shape_normal(Vector.Y_POS)

        As every class has the same create(normal=Vector.X_POS) method, classes can be substituted without affecting the logic.
        
    EXTENSIBILITY & DATA FILE
        In the case of creating more control shapes, the class approach allows to easily create new classes for new shapes,
        inheriting the base functionality and overriding the create() method to create the specific shape or system, just like 
        the Slider, Osipa and Text shapes which required a more complex creation logic.
        
        Also, after the new shape is created, there is no need to memorize the existing shape names from a dictionary,
        only call to the new class, which the IDE itself can autocomplete.

        In parallel, the implementation of a json data file for storing control shape points, allow to easily add more shapes
        to the library without the need of coding or importing template files like another maya file, AND keep the code free
        from hardcoded shape point positions.


    """
    suffix = "_ctrl"

    def __init__(self, control_name= "control"):
        self._name = control_name
        self.transform = None

        if control_name and pm.objExists(control_name):
            self.transform = pm.nt.Transform(control_name)

    def __str__(self):
        return self.transform.name() if self.transform else ""

    @property
    def name(self):
        if self.transform:
            return self.transform.name()
        if self._name.endswith(self.suffix):
            return self._name
        return self._name + self.suffix

    @name.setter
    def name(self, name: str):
        if self.transform and name:
            self.transform.rename(name)

    @property
    def shapes(self) -> list[pm.nt.NurbsCurve]:
        if self.transform:
            return self.transform.getShapes()
        return []

    @shapes.setter
    def shapes(self, shapes: list[pm.nt.NurbsCurve]):
        new_shapes = shapes if isinstance(shapes, (list, tuple)) else [shapes]
        
        for shape in new_shapes:
            cvs = shape.getCVs(space="world")
            pm.parent(shape, self.transform, s=True, r=True)
            shape.setCVs(cvs, space="world")
            shape.updateCurve()

            shape.rename(f"{self.transform.name()}Shape")

    @property
    def offset(self):
        if self.transform:
            return self.transform.getParent()
        return None
    
    @offset.setter
    def offset(self, offset_transform: pm.nt.Transform):
        if pm.objExists(offset_transform):
            pm.parent(self.transform, offset_transform)
        else:
            offset = tutils.create_offset(self.transform, offset_name_suffix="_root")
            offset.rename(offset_transform)

    @property
    def color(self) -> ColorIndex:
        if self.shapes:
            shape = self.shapes[0]
            if shape.ove.get():
                if shape.oveRGB.get():
                    return shape.overrideColorRGB.get()
                else:
                    return ColorIndex(shape.overrideColor.get())
    
    @color.setter
    def color(self, color: ColorIndex):
        for shape in self.shapes:
            shape.overrideEnabled.set(1)
            if isinstance(color, (ColorIndex, int)):
                shape.overrideRGBColors.set(0)
                shape.overrideColor.set(color.value if isinstance(color, ColorIndex) else color)
            else:
                
                shape.overrideRGBColors.set(1)
                shape.overrideColorRGB.set(color)

    @property
    def cvs(self) -> list:
        cvs = []
        for shape in self.shapes:
            cv_group = pm.ls(shape + ".cv[*]", fl=True)
            cvs.append(cv_group)
        return cvs
    
    @abstractmethod            
    def create(self, normal=Vector.X_POS) -> 'Control':
        """ abstraction of control creation. 
        
        Args:
            name (str, optional): Name of the control to create. Defaults to "control".
            normal (Vector, optional): Normal vector for the control shape orientation. Defaults to Vector.X_POS.
        Returns:
            Control: Self control instance.
        """
        pass
    
    # Shape methods
    def _shape_edit(self, 
                    translate:  pm.dt.Vector=None, 
                    rotate:     pm.dt.Vector=None, 
                    scale:      pm.dt.Vector=None,
                    relative    = True,
                    worldSpace  = False) -> 'Control':
        if translate:
            pm.xform(self.cvs, r=relative, ws=worldSpace, t=translate)
        if rotate:
            pm.xform(self.cvs, r=relative, ws=worldSpace, ro=rotate)
        if scale:
            pm.xform(self.cvs, r=relative, ws=worldSpace, s=scale)
        return self

    def _shape_line_width(self, width: int) -> 'Control':
        for shape in self.shapes:
            shape.lineWidth.set(width)
        return self

    def _create_curve_from_json(self, shape_name: str):
        self.transform = pm.nt.Transform(n=self.name)
        pm.delete(self.shapes)

        shape_points = SHAPE_LIBRARY[shape_name]
        for index, points in shape_points.items():
            curve = pm.curve(d=1, p=points, n=f"{self.name}_{shape_name}")
            closed = pm.closeCurve(curve, preserveShape=True, ch=False, rpo=True)[0]
            
            self.shapes = closed.getShape()
            pm.delete(curve)
        
        return self

    def _store_curve_to_json(self, shape_name: str):
        
        SHAPE_LIBRARY[shape_name] = {}
        for index, shape in enumerate(self.shapes):
            cvs = pm.ls(shape + ".cv[*]", fl=True)
            points = [pm.xform(cv, q=True, t=True, ws=True) for cv in cvs]
            SHAPE_LIBRARY[shape_name][str(index)] = points

        with open(JSON_PATH, "w") as f:
            json.dump(SHAPE_LIBRARY, f, indent=4)

    def shape_orient(self, vector:pm.dt.Vector= (0,0,0)) -> 'Control':
        self._shape_edit(rotate=vector)
        return self
   
    def shape_move(self, vector=(0,0,0)) -> 'Control':
        self._shape_edit(translate=vector)
        return self

    def shape_scale(self, scale_vector: pm.dt.Vector, pivot="ws") -> 'Control':
        self._shape_edit(scale=scale_vector, worldSpace= pivot=="ws")
        return self
    
    def shape_normal(self, normal=(1,0,0)) -> 'Control':
        self.shape_orient([0, -90 * normal[2], 90 * normal[1]])
        return self

    def shape_replace(self, *new_curves: pm.nt.Transform) -> 'Control':
        old_shapes = self.shapes
        self.shapes = new_curves if isinstance(new_curves, (list, tuple)) else [new_curves]
        pm.delete(old_shapes)
        return self

    def shape_combine(self, *new_curves: pm.nt.Transform) -> 'Control':
        self.shapes = new_curves if isinstance(new_curves, (list, tuple)) else [new_curves]
        for new_curve in new_curves:
            # delete the new control if it has no hierarchy after shape transfer.
            if not new_curve.getChildren(type="transform"):
                pm.delete(new_curve)

        return self
    
    def shape_color_index(self, color: ColorIndex) -> 'Control':
        """
        Summary:
            Change control color according to the value in color index.

        Args:
            color (ColorIndex): Color index to apply to the control.

        Returns:
            Control: Self control instance.
        """
        self.color = color
        return self

    def shape_color_rgb(self, rgb_color:list) -> 'Control':
        self.color = rgb_color
        return self

    def shape_line_thick(self) -> 'Control':
        self._shape_line_width(2)
        return self
    
    def shape_line_thin(self) -> 'Control':
        self._shape_line_width(1)
        return self
    
    # Transform methods
    def copy(self):
        copy_name = f"{self.name}_copy"
        copy = self.transform.duplicate(n=copy_name)[0]
        pm.parent(copy, w=True)

        if tutils.has_children(copy):
            pm.delete(copy.getChildren(type="transform"))
        
        return self.__class__(copy)

    def mirror(self):
        copy = self.copy()
        tutils.flip_transform(copy.transform)
        return self.__class__(copy)

    def align_to(self, parent: pm.nt.Transform) -> 'Control':
        """Move control transform to the given transform's node location

        Args:
            parent (pm.nt.Transform): Transform node to align the control to.

        Returns:
            Control: Self control instance.
        """
        if self.offset:
            tutils.align_transform(parent, self.offset)
        else:
            tutils.align_transform(parent, self.transform)
        return self

    def create_offset(self, suffix="_offset") -> 'Control':
        self.offset = f"{self.transform.name()}{suffix}"
        return self

    def reset(self) -> 'Control':
        """Restore default values on every keyable attribute on control."""
        attributes = self.transform.listAttr(keyable=True)
        [autils.reset_attribute(attr) for attr in attributes]
        return self

    def lock_channels(self, *channels: str) -> 'Control':
        """Lock and hide the given channels on the control transform.

        Args:
            channels (list[str]): Name of channels to lock on control. E.g: "t", "rx", etc.
        """
        for attr in channels:
            if not self.transform.hasAttr(attr): continue
            attribute_node = self.transform.attr(attr)
            autils.lock_and_hide_attribute(attribute_node)
        return self


class Circle(Control):
    def create(self, normal= [1,0,0]) -> 'Control':
        self._create_curve_from_json("circle")
        self.shape_normal(normal)
        return self


class SemiCircle(Circle):
    def create(self, normal=[1, 0, 0]) -> 'Control':
        self._create_curve_from_json("semi_circle")
        self.shape_normal(normal)
        return self


class Square(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("square")
        self.shape_normal(normal)
        return self


class Cross(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("cross")
        self.shape_normal(normal)
        return self


class Arrow(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("arrow")
        self.shape_normal(normal)
        return self


class Triangle(Control):

    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("triangle")
        self.shape_normal(normal)
        return self


class Pin(Control):
    def create(self, normal=[1,0,0])-> 'Control':
        self._create_curve_from_json("pin")
        self.shape_normal(normal)
        return self


class PinDouble(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("pin_double")
        self.shape_normal(normal)
        return self


class Sphere(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("sphere")        
        self.shape_normal(normal)
        return self


class Button(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("button")
        self.shape_normal(normal)
        return self


class Orient(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("orient_3d")
        self.shape_normal(normal)
        return self


class Cube(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("cube_center")
        self.shape_normal(normal)
        return self


class CubeFK(Control):
    def create(self, normal=[1,0,0])-> 'Control':
        self._create_curve_from_json("cube_fk")
        self.shape_normal(normal)
        return self


class Gear(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("gear")
        self.shape_normal(normal)
        return self


class Ring(Control):
    def create(self, normal=[1,0,0])-> 'Control':
        self._create_curve_from_json("ring")
        self.shape_normal(normal)
        return self


class Pyramid(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("pyramid")
        self.shape_normal(normal)
        return self


class Bar(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        self._create_curve_from_json("bar")
        self.shape_normal(normal)
        return self

class Slider(Control):
    def __init__(self, control_name="control", limits=(0, 1)):
        super().__init__(control_name)
        self.limits = limits

    def create(self, normal= [1,0,0])-> 'Control':
        bar_curve = pm.curve(p=[(0, self.limits[0], 0), (0, self.limits[1], 0)], d=1)
        bar = Bar(bar_curve)
        bar.shape_normal(normal)
        bar.name = f"{self._name}_bar"
        bar.shape_line_thick()
        bar.shapes[0].overrideEnabled.set(1)
        bar.shapes[0].overrideDisplayType.set(2)
        

        circle = Circle(f"{self._name}_slider").create()
        circle.shape_normal(normal)
        circle.shape_scale([.2, .2, .2])
        circle.lock_channels("tx", "tz", "r", "s", "v")
        circle.shape_color_index(ColorIndex.YELLOW)
        
        pm.transformLimits(circle.transform, ety=(True, True), ty=(self.limits[0], self.limits[1]))

        self.transform = circle.transform
        self.offset = bar.transform
        
        return self

    def shape_normal(self, normal=(1,0,0)) -> 'Control':
        normal_vector = [0, -90 * normal[2], 90 * normal[1]]
        pm.xform(self.offset, r=True, ws=False, ro=normal_vector)
        return self

class Osipa(Control):
    def create(self, normal=[1,0,0]) -> 'Control':
        frame  = Square(f"{self._name}_frame").create()
        frame.shape_normal(normal)
        frame.shapes[0].overrideEnabled.set(1)
        frame.shapes[0].overrideDisplayType.set(2)
        
        slider = Square(f"{self._name}_slider").create()
        slider.shape_normal(normal)
        slider.shape_scale([.3,.3,.3])
        slider.shape_orient([45, 0, 0])
        slider.lock_channels("tx", "r", "s", "v")

        pm.transformLimits(slider.transform, tx=(0, 0), etx=(True, True))
        pm.transformLimits(slider.transform, ty=(-1, 1), ety=(True, True))
        pm.transformLimits(slider.transform, tz=(-1, 1), etz=(True, True))

        self.transform = slider.transform
        self.offset = frame.transform
        
        return self

    def shape_normal(self, normal=(1,0,0)) -> 'Control':
        normal_vector = [0, -90 * normal[2], 90 * normal[1]]
        pm.xform(self.offset, r=True, ws=False, ro=normal_vector)
        return self

class Text(Control):
    def __init__(self, control_name="control", text="curve"):
        super().__init__(control_name= control_name)
        self.text = text

    def create(self, normal=[1,0,0]) -> 'Control':
        text_curve = pm.nt.Transform(pm.textCurves(f='Times-Roman', t= self.text, ch=False, name=self.name)[0])
        self.transform = pm.nt.Transform(n=self.name)
        
        text_characters = [character for character in text_curve.getChildren(ad=True, type="nurbsCurve")]
        self.shapes = text_characters
        
        self.shape_orient([0, 90, 0])
        pivot_vector = tutils.get_center_pivot(self.transform)
        pos_vector   = self.transform.getTranslation(space="world")
        new_pos = pos_vector - pivot_vector
        self.shape_move(new_pos)
        
        pm.delete(text_curve)

        self.shape_normal(normal)
        return self

