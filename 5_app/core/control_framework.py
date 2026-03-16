'''
################################################################################################################
Content: Centralized control creation.

Dependency: abc, os, json, pymel.core, utility.maya_lib, utility.common
Maya Version tested: 2024

How to:
    - Use: 
        - Import the module and create control instances using the provided classes (e.g., Circle, Square, Text).
            e.g: my_control = Circle(control_name="myCircle")
        - Call create() method to generate the control shape and transform.
            e.g: my_control.create(normal=common.Vector.Y_POS)
        
        - Optional: 
            Manipulate control properties using method chaining.
                e.g: my_control.align_to(parent=some_transform_node).create_offset()
            Cast existing transform node to control instance.
                e.g: my_control = Control(control_name=existing_transform_name)
            Use setters and getters to create offsets, change colors, add shapes and rename the control.
                e.g: my_control.name = "new_name"
                     my_control.offset = "new_offset_transform"
                     my_control.color = ColorIndex.RED
                     my_control.shapes = [new_shape1, new_shape2]
        
        - Extend:
            - Create a new class inheriting from Control and implement the create() method and define the shape creation logic.
            - To add more control shape points to the library:
                - Select the curve transform, and use the _store_curve_to_json() method to save its CV positions to the JSON file.
        
            
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

import utility.maya_lib as maya_lib
import utility.common as common


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


class Control():
    suffix = "_ctrl"

    def __init__(self, control_name= "_"):
        if pm.objExists(control_name):
            self.transform = pm.nt.Transform(control_name)
            self._name = self.transform.name()
        else:
            self.transform = None
            self._name = control_name or "control"
            

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
        if not self.transform:
            self._name = name

    @property
    def shapes(self) -> list[pm.nt.NurbsCurve]:
        if self.transform:
            return self.transform.getShapes()
        return []

    @shapes.setter
    def shapes(self, shapes: list[pm.nt.NurbsCurve]):
        new_shapes = shapes if isinstance(shapes, (list, tuple)) else [shapes]
        
        for shape in new_shapes:
            cvs = pm.ls(shape + ".cv[*]", fl=True)
            matrixes = [pm.xform(cv, q=True, matrix=True, ws=True) for cv in cvs]
            pm.parent(shape, self.transform, s=True, r=True)
            [pm.xform(cv, matrix=matrix, ws=True) for cv, matrix in zip(cvs, matrixes)]
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
            offset = maya_lib.create_offset(self.transform, offset_name_suffix="_root")
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
    def create(self, normal=maya_lib.Vector.X_POS) -> 'Control':
        """ abstraction of control creation. 
        
        Args:
            name: Name of the control to create. Defaults to "control".
            normal: Normal vector for the control shape orientation. Defaults to maya_lib.Vector.X_POS.
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
        self.shape_combine(*new_curves)
        pm.delete(old_shapes)
        return self

    def shape_combine(self, *new_curves: pm.nt.Transform) -> 'Control':
        for curve in new_curves:
            if isinstance(curve, (list, tuple)):
                self.shape_combine(*curve)
                continue
            self.shapes = curve.getShapes()

        return self
    
    def shape_color_index(self, color: ColorIndex) -> 'Control':
        """
        Summary:
            Change control color according to the value in color index.

        Args:
            color: Color index to apply to the control.

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
    def parent_to(self, parent: pm.nt.Transform) -> 'Control':
        if not isinstance(parent, pm.nt.Transform):
            pm.warning(f"Parent object must be a transform node. Given: {parent}")
            return self
        
        if self.offset:
            pm.parent(self.offset, parent)
        else:
            pm.parent(self.transform, parent)
        return self

    def copy(self):
        copy_name = f"{self.name}_copy"
        copy = self.transform.duplicate(n=copy_name)[0]
        pm.parent(copy, w=True)

        if maya_lib.has_children(copy):
            pm.delete(copy.getChildren(type="transform"))
        
        return self.__class__(copy)

    def mirror(self):
        copy = self.copy()
        maya_lib.flip_transform(copy.transform)
        return self.__class__(copy)

    def align_to(self, parent: pm.nt.Transform) -> 'Control':
        """Move control transform to the given transform's node location

        Args:
            parent: Transform node to align the control to.

        Returns:
            Control: Self control instance.
        """
        if not isinstance(parent, pm.nt.Transform):
            pm.warning(f"Reference object must be a transform node. Given: {parent}")
            return self
        
        if self.offset:
            maya_lib.align_transform(parent, self.offset)
        else:
            maya_lib.align_transform(parent, self.transform)
        return self

    def create_offset(self, suffix="_offset") -> 'Control':
        self.offset = f"{self.transform.name()}{suffix}"
        return self

    def reset(self) -> 'Control':
        """Restore default values on every keyable attribute on control."""
        attributes = self.transform.listAttr(keyable=True)
        [maya_lib.reset_attribute(attr) for attr in attributes]
        return self

    def lock_channels(self, *channels: str) -> 'Control':
        """Lock and hide the given channels on the control transform.

        Args:
            channels: Name of channels to lock on control. E.g: "t", "rx", etc.
        """
        for attr in channels:
            if not self.transform.hasAttr(attr): continue
            attribute_node = self.transform.attr(attr)
            maya_lib.lock_and_hide_attribute(attribute_node)
        return self


class Slider(Control):
    def __init__(self, control_name="_", limits=(0, 1)):
        super().__init__(control_name)
        self.limits = limits

    @property
    def name(self):
        return super().name
    
    @name.setter
    def name(self, value):
        if self.offset:
            self.offset.rename(f"{value}_bar")
        value = f"{value}_slider" if not value.endswith("_slider") else value
        Control.name.fset(self, value)

    def create(self, normal= [1,0,0])-> 'Control':
        bar_curve = pm.curve(p=[(0, self.limits[0], 0), (0, self.limits[1], 0)], d=1)
        bar = Control(control_name= bar_curve)
        #bar = create_control(Shapes.BAR, f"{self._name}_bar", normal)
        bar.shape_normal(normal)
        bar.name = f"{self._name}_bar"
        bar.shape_line_thick()
        bar.shapes[0].overrideEnabled.set(1)
        bar.shapes[0].overrideDisplayType.set(2)

        circle = create_control(Shapes.CIRCLE, f"{self._name}", normal)
        circle.name = f"{self._name}_slider"
        circle.shape_normal(normal)
        circle.shape_scale([.2, .2, .2])
        circle.lock_channels("tx", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v")
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
    @property
    def name(self):
        return super().name
    
    @name.setter
    def name(self, value):
        if self.offset:
            self.offset.rename(f"{value}_frame")
        value = f"{value}_slider" if not value.endswith("_slider") else value
        Control.name.fset(self, value)

    def create(self, normal=[1,0,0]) -> 'Control':
        frame  = create_control(Shapes.SQUARE, f"{self._name}_frame")
        frame.shape_normal(normal)
        frame.shapes[0].overrideEnabled.set(1)
        frame.shapes[0].overrideDisplayType.set(2)
        
        slider = create_control(Shapes.SQUARE, f"{self._name}_slider")
        slider.shape_normal(normal)
        slider.shape_scale([.3,.3,.3])
        slider.shape_orient([45, 0, 0])
        slider.lock_channels("tx", "rx", "ry", "rz", "sx", "sy", "sz", "v")

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
    def __init__(self, control_name="_", text="curve"):
        super().__init__(control_name= control_name)
        self.text = text



    def create(self, normal=[1,0,0]) -> 'Control':
        text_curve = pm.nt.Transform(pm.textCurves(f='Times-Roman', t= self.text, ch=False, name=self.name)[0])
        self.transform = pm.nt.Transform(n=self.name)
        
        text_characters = [character for character in text_curve.getChildren(ad=True, type="nurbsCurve")]
        self.shapes = text_characters
        
        self.shape_orient([0, 90, 0])
        pivot_vector = maya_lib.get_center_pivot(self.transform)
        pos_vector   = self.transform.getTranslation(space="world")
        new_pos = pos_vector - pivot_vector
        self.shape_move(new_pos)
        
        pm.delete(text_curve)

        self.shape_normal(normal)
        return self


class Shapes(Enum):
    CIRCLE      = "circle"
    SEMI_CIRCLE = "semi_circle"
    SQUARE      = "square"
    CROSS       = "cross"
    ARROW       = "arrow"
    TRIANGLE    = "triangle"
    PIN         = "pin"
    PIN_DOUBLE  = "pin_double"
    SPHERE      = "sphere"
    BUTTON      = "button"
    ORIENT_3D   = "orient_3d"
    CUBE_CN     = "cube_center"
    CUBE_FK     = "cube_fk"
    GEAR        = "gear"
    RING        = "ring"
    PYRAMID     = "pyramid"
    BAR         = "bar"

    OSIPA  = "osipa"
    SLIDER = "slider"
    TEXT   = "text"



def create_control(control_type: Shapes, control_name:str="", normal=[1,0,0], text="") -> Control:
    print("####   ", control_type, control_name)
    if not isinstance(control_type, Shapes):
        pm.warning(f"Control type '{control_type}' not recognized.")
        return None
    
    control = None
    if control_type == Shapes.TEXT:
        text = text if text else control_name
        control = Text(text=text).create(normal)
    
    elif control_type == Shapes.OSIPA:
        control = Osipa().create(normal)
    
    elif control_type == Shapes.SLIDER:
        control = Slider().create(normal)
    
    else:
        control = Control()
        control._create_curve_from_json(control_type.value)
        control.shape_normal(normal)
    
    control.name = control_name
    return control

