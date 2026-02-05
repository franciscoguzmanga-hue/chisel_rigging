'''
################################################################################################################
Author: Francisco Guzmán

Content: Centralized control creation.
Dependency: pymel.core, src.utility.transform_utils, src.utility.attribute_utils
Maya Version tested: 2024

How to:
    - Use: 
        - Import the module and create control instances using the provided classes (e.g., Circle, Square, Text).
        
            e.g 01: Manipulate control properties after creation.
                my_control = Circle()
                my_control.create(name="myCircleCtrl", normal=Vector.Y_POS)
                my_control.set_color_index(ColorIndex.BLUE)

            e.g 02: Manipulate control properties using method chaining.
                my_control = Text(text="hand_ctrl").create(name="hand_ctrl", normal=Vector.Z_POS)
                my_control.align(parent=some_transform_node).create_offset().lock_channels("s", "v").set_line_thick()
        
        - Cast controls from existing transform nodes giving the transform node to the control class constructor.

            e.g 03: Cast existing transform node to control instance.
                existing_transform = pm.PyNode("existing_ctrl")
                my_control = Control(control=existing_transform)
                my_control.set_color_rgb([1, 0, 0])  # Set color to red
            
        - Warning: the Control class is a base class and cannot create controls directly. Use one of its subclasses.

    - Test: Use pymel.core to create transform nodes and test the functions interactively in Maya.
################################################################################################################
'''


from enum import Enum
from abc import ABC, abstractmethod
from enum import Enum

import pymel.core as pm

from src.utility.transform_utils import align_transform, create_offset
from src.utility.attribute_utils import reset_attribute, lock_and_hide_attribute, Vector


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


class ControlInterface(ABC):
    @abstractmethod
    def create(self, name="control", normal=Vector.X_POS):
        """ abstraction of control creation. """


class Control(ControlInterface):
    suffix = "_ctrl"

    def __init__(self, control= None):
        self.curve = pm.nt.Transform(control) if control and pm.objExists(control) else None
        self.offset = None

    def __str__(self):
        return self.curve.name()

    def create(self, name="control", normal=Vector.X_POS) -> 'Control':
        """ abstraction of control creation. 
        
        Args:
            name (str, optional): Name of the control to create. Defaults to "control".
            normal (Vector, optional): Normal vector for the control shape orientation. Defaults to Vector.X_POS.
        Returns:
            Control: Self control instance.
        """
        pass

    def orient_shape(self, vector = (0,0,0)) -> 'Control':
        """Rotates the control shape according to given vector.

        Args:
            vector (tuple, optional): Rotation vector. Defaults to (0,0,0).

        Returns:
            Control: Self control instance.
        """
        cvs = [shape.cv for shape in self.curve.getShapes()]
        pm.xform(cvs, ro=vector)
        return self

    def normal_shape(self, normal=(1,0,0)) -> 'Control':
        """Change the normal or vector where the curve should aim to.

        Args:
            normal (tuple, optional): Rotation vector. Defaults to (1,0,0).

        Returns:
            Control: Self control instance.
        """
        self.orient_shape([0, -90 * normal[2], 90 * normal[1]])
        return self

    def move_shape(self, vector=(0,0,0)) -> 'Control':
        """Move control shape using the given vector.

        Args:
            vector (tuple, optional): Translation vector. Defaults to (0,0,0).

        Returns:
            Control: Self control instance.
        """
        cvs = [shape.cv for shape in self.curve.getShapes()]
        pm.xform(cvs, t=vector, r=True)
        return self

    def scale_shape(self, scale_vector: pm.dt.Vector, pivot="ws") -> 'Control':
        """Change the control shape size according to the given scale vector.

        Args:
            scale_vector (pm.dt.Vector): Scale vector.
            pivot (str, optional): Pivot point for scaling. Defaults to "ws".

        Returns:
            Control: Self control instance.
        """
        pivot_vector = pivot == "ws"
        cvs = [cv for shape in self.curve.getShapes() for cv in pm.ls(shape + ".cv[*]", fl=True)]
        pm.scale(cvs, scale_vector, r=True, p=self.curve.getTranslation(ws=pivot_vector))
        return self

    def align(self, parent: pm.nt.Transform) -> 'Control':
        """Move control transform to the given transform's node location

        Args:
            parent (pm.nt.Transform): Transform node to align the control to.

        Returns:
            Control: Self control instance.
        """
        if self.offset:
            align_transform(parent, self.offset)
        else:
            align_transform(parent, self.curve)
        return self

    def create_offset(self, suffix="_offset") -> 'Control':
        """Creates offset group over the control transform.

        Args:
            suffix (str, optional): Suffix for the offset group name. Defaults to "_offset".

        Returns:
            Control: Self control instance.
        """
        self.offset = create_offset(self.curve, offset_name_suffix=suffix)
        return self

    def combine_shape(self, new_curves: list[pm.nt.Transform]) -> 'Control':
        """Combine new control shapes to the current control.
        
        Args:
            new_curves (list [pm.nt.Transform]): List of new control transforms to use as shapes.

        Returns:
            Control: Self control instance.
        """
        for new_curve in new_curves:
            new_shapes = new_curve.getShapes()

            # combine shapes with world space cvs positions preserved.
            for shape in new_shapes:
                cvs = pm.ls(f"{shape}.cv[*]", fl=True)
                matrixes = [pm.xform(cv, q=True, ws=True, matrix=True) for cv in cvs]
                pm.parent(shape, self.curve, s=True, r=True)
                [pm.xform(cv, ws=True, matrix=matrix) for cv, matrix in zip(cvs, matrixes)]
                shape.rename(f"{self.curve.name()}Shape")

            # delete the new control if it has no hierarchy after shape transfer.
            if not new_curve.getChildren(type="transform"):
                pm.delete(new_curve)

        return self
    
    def replace_shape(self, new_controls: list[pm.nt.Transform]) -> 'Control':
        """Replace the current control shape with new control shapes.

        Args:
            new_controls (list[pm.nt.Transform]): List of new control transforms to use as shapes.

        Returns:
            Control: Self control instance.
        """
        shape = self.curve.getShapes()
        [ self.combine_shape(curve) for curve in new_controls ]
        pm.delete(shape)
        return self

    def set_color_index(self, color: ColorIndex) -> 'Control':
        """
        Summary:
            Change control color according to the value in color index.

        Args:
            color (ColorIndex): Color index to apply to the control.

        Returns:
            Control: Self control instance.
        """
        shapes = self.curve.getShapes()
        for shape in shapes:
            shape.overrideEnabled.set(1)
            shape.overrideRGBColors.set(0)
            shape.overrideColor.set(color.value if isinstance(color, ColorIndex) else color)
        return self

    def set_color_rgb(self, rgb_color:list) -> 'Control':
        """
        Summary:
            Change control color according to the given RGB color.

        Args:
            rgb_color (list): RGB color to apply to the control.

        Returns:
            Control: Self control instance.
        """
        shapes = self.curve.getShapes()
        for shape in shapes:
            shape.overrideEnabled.set(1)
            shape.overrideRGBColors.set(1)
            shape.overrideColorRGB.set(rgb_color)
        return self

    def reset(self) -> Control:
        """Restore default values on every keyable attribute on control.

        Returns:
            Control: Self control instance.
        """
        attributes = self.curve.listAttr(keyable=True)
        [reset_attribute(attr) for attr in attributes]
        return self

    def lock_channels(self, *channels: str) -> 'Control':
        """
        Summary:
            Locks & Hide channels on current control.

        Args:
            channels (list[str]): Name of channels to lock on control.
        
        Returns:
            Control: Self control instance.
        """
        for attr in channels:
            if not self.curve.hasAttr(attr): continue
            attribute_node = self.curve.attr(attr)
            lock_and_hide_attribute(attribute_node)
        return self

    def set_line_thick(self) -> 'Control':
        """Makes control thick.

        Returns:
            Control: Self control instance.
        """
        shapes = self.curve.getShapes()
        for shape in shapes:
            shape.lineWidth.set(2)
        return self
    
    def set_line_thin(self) -> 'Control':
        """Makes control Thin.

        Returns:
            Control: Self control instance.
        """
        shapes = self.curve.getShapes()
        for shape in shapes:
            shape.lineWidth.set(1)
        return self
    

class Circle(Control):
    def create(self, name= "curve", normal= [1,0,0]) -> 'Control':
        self.curve = pm.circle(nr=(1, 0, 0), ch=False, n=name)[0]
        self.normal_shape(normal)
        return self


class Square(Control):
    def create(self, name= "curve", normal=[1,0,0]) -> 'Control':
        self.curve = pm.circle(sections=4, normal=[1, 0, 0], d=1, n=name)[0]
        self.orient_shape([45, 0, 0])
        self.normal_shape(normal)
        return self


class Cross(Control):
    points = [(1, 0, 2), (1, 0, 1), (2, 0, 1), (2, 0, -1), (1, 0, -1), (1, 0, -2), (-1, 0, -2),
              (-1, 0, -1), (-2, 0, -1), (-2, 0, 1), (-1, 0, 1), (-1, 0, 2), (1, 0, 2)]

    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        self.curve = pm.curve(d=1, p= self.points, n=name)
        self.orient_shape([0, 0, 90])
        self.scale_shape([.45, .45, .45])
        self.normal_shape(normal)
        return self


class Arrow(Control):
    points = [(0, -2, -1), (0, 0, -1), (0, 0, -2), (0, 2, 0), (0, 0, 2), (0, 0, 1), (0, -2, 1), (0, -2, -1)]

    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        self.curve = pm.curve(d=1, p=self.points, n=name)
        self.scale_shape([.45, .45, .45])
        self.normal_shape(normal)
        return self


class Triangle(Control):

    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        self.curve = pm.circle(sections=3, normal=[1,0,0], d=1, n=name)[0]
        self.normal_shape(normal)
        return self


class HalfCircle(Control):
    def create(self, name="curve", normal=[1,0,0])-> 'Control':
        self.curve = pm.circle(normal=[1, 0, 0], n=name)[0]
        pm.xform(self.curve.cv[3:7], scale=[1, 0, 1])
        self.normal_shape(normal)
        return self


class Text(Control):
    def __init__(self, control=None, text="curve"):
        self.curve = pm.nt.Transform(control) if control and pm.objExists(control) else None
        self.offset = None
        self.text = text

    def create(self, name="curve", normal=[1,0,0]) -> 'Control':

        if not self.text: self.text = name
        original = pm.nt.Transform(pm.textCurves(f='Times-Roman', t= self.text, ch=False, name=name)[0])
        original.ry.set(90)
        pm.xform(original, cp=True, ws=True)
        loc = pm.spaceLocator()
        pm.delete(pm.pointConstraint(loc, original))

        letters = [ct.getParent() for ct in original.getChildren(ad=True, type="nurbsCurve")]
        self.curve = pm.group(em=True, n=name)
        pm.parent(letters, self.curve)
        pm.makeIdentity(letters, a=True)
        pm.parent([l.getShapes() for l in letters], self.curve, s=True, r=True)

        [pm.rename(shape, f"{name}Shape") for shape in self.curve.getShapes()]
        pm.delete(letters, original, loc)
        self.normal_shape(normal)
        return self


class Pin(Control):
    points = [[0.0, -1.1102230246251565e-15, 0.0], [0.0, 1.199999999999999, 0.0], [0.0, 1.5999999999999992, -0.4],
              [0.0, 1.9999999999999991, 0.0], [0.0, 1.5999999999999992, 0.4], [0.0, 1.199999999999999, 0.0]]

    def create(self, name="curve", normal=[1,0,0])-> 'Control':
        self.curve = pm.curve(d=1, p=self.points, n=name)
        self.normal_shape(normal)
        return self


class PinDouble(Control):
    points = [[0.0, -1.9860073255814468, 0.0], [0.0, -1.489505494186085, 0.4965018313953617],
              [0.0, -0.9930036627907234, 0.0], [0.0, -1.489505494186085, -0.4965018313953617],
              [0.0, -1.9860073255814468, 0.0], [0.0, 1.9860073255814468, 0.0],
              [0.0, 1.489505494186085, -0.4965018313953617], [0.0, 0.9930036627907234, 0.0],
              [0.0, 1.489505494186085, 0.4965018313953617], [0.0, 1.9860073255814468, 0.0]]

    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        self.curve = pm.curve(d=1, p=self.points, n=name)
        self.normal_shape(normal)
        return self


class Sphere(Control):
    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        circulo1 = pm.circle(nr=(1, 0, 0), ch=False, n=name)[0]
        circulo2 = pm.circle(nr=(0, 1, 0), ch=False, n=name)[0]
        circulo3 = pm.circle(nr=(0, 0, 1), ch=False, n=name)[0]
        circles = [circulo1, circulo2, circulo3]

        shapes = [circle.getShape() for circle in circles]
        self.curve = pm.group(em=True, n=name)
        [pm.parent(shape, self.curve, s=True, r=True) for shape in shapes]
        pm.delete(circles)
        self.normal_shape(normal)
        return self


class Button(Control):
    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        c1 = HalfCircle().create(name)
        c2 = HalfCircle().create(name)

        c2.orient_shape([0, 90, 0])
        c1.combineShape(c2.curve)
        c1.orient_shape([0, 0, -90])
        self.curve = c1.curve
        self.normal_shape(normal)
        return self


class Orient(Control):
    points = [[0.0959835, 0.604001, -0.0987656], [0.500783, 0.500458, -0.0987656],
              [0.751175, 0.327886, -0.0987656], [0.751175, 0.327886, -0.0987656],
              [0.751175, 0.327886, -0.336638], [0.751175, 0.327886, -0.336638],
              [1.001567, 0.0, 0.0], [1.001567, 0.0, 0.0], [0.751175, 0.327886, 0.336638],
              [0.751175, 0.327886, 0.336638], [0.751175, 0.327886, 0.0987656],
              [0.751175, 0.327886, 0.0987656], [0.500783, 0.500458, 0.0987656],
              [0.0959835, 0.604001, 0.0987656], [0.0959835, 0.604001, 0.0987656],
              [0.0959835, 0.500458, 0.500783], [0.0959835, 0.327886, 0.751175],
              [0.0959835, 0.327886, 0.751175], [0.336638, 0.327886, 0.751175],
              [0.336638, 0.327886, 0.751175], [0.0, 0.0, 1.001567], [0.0, 0.0, 1.001567],
              [-0.336638, 0.327886, 0.751175], [-0.336638, 0.327886, 0.751175],
              [-0.0959835, 0.327886, 0.751175], [-0.0959835, 0.327886, 0.751175],
              [-0.0959835, 0.500458, 0.500783], [-0.0959835, 0.604001, 0.0987656],
              [-0.0959835, 0.604001, 0.0987656], [-0.500783, 0.500458, 0.0987656],
              [-0.751175, 0.327886, 0.0987656], [-0.751175, 0.327886, 0.0987656],
              [-0.751175, 0.327886, 0.336638], [-0.751175, 0.327886, 0.336638],
              [-1.001567, 0.0, 0.0], [-1.001567, 0.0, 0.0],
              [-0.751175, 0.327886, -0.336638], [-0.751175, 0.327886, -0.336638],
              [-0.751175, 0.327886, -0.0987656], [-0.751175, 0.327886, -0.0987656],
              [-0.500783, 0.500458, -0.0987656], [-0.0959835, 0.604001, -0.0987656],
              [-0.0959835, 0.604001, -0.0987656], [-0.0959835, 0.500458, -0.500783],
              [-0.0959835, 0.327886, -0.751175], [-0.0959835, 0.327886, -0.751175],
              [-0.336638, 0.327886, -0.751175], [-0.336638, 0.327886, -0.751175],
              [0.0, 0.0, -1.001567], [0.0, 0.0, -1.001567],
              [0.336638, 0.327886, -0.751175], [0.336638, 0.327886, -0.751175],
              [0.0959835, 0.327886, -0.751175], [0.0959835, 0.327886, -0.751175],
              [0.0959835, 0.500458, -0.500783], [0.0959835, 0.604001, -0.0987656]]

    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        self.curve = pm.curve(d=1, p=self.points, n=name)
        self.orient_shape([0, 0, -90])
        self.normal_shape(normal)
        return self


class Cube(Control):
    points = [(-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5),
              (-0.5, -0.5, 0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5),
              (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5),
              (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5)]

    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        self.curve = pm.curve(d=1, p=self.points, n=name)
        self.scale_shape([1.4, 1.4, 1.4])
        self.normal_shape(normal)
        return self


class CubeFK(Control):
    def create(self, name="curve", normal=[1,0,0])-> 'Control':
        cube = Cube().create(name)
        cube.move_shape([.7,0,0])
        self.curve = cube.curve
        self.normal_shape(normal)
        return self


class Gear(Control):
    points = [[0.00272859287881, -0.9807839393619999, -0.19508992135700004],
              [0.00272859287881, -0.923878371716, -0.382682859899],
              [0.0435272647635, -0.994432151318, -0.42039453983400005],
              [0.0435272647635, -0.9020224809649999, -0.5932812094700001],
              [0.00272859287881, -0.831468701363, -0.555569529535],
              [0.00272859287881, -0.707106113434, -0.7071059942260001],
              [0.0435272647635, -0.757857561112, -0.7689467668550001],
              [0.0435272647635, -0.606321275235, -0.893309533597],
              [0.00272859287881, -0.555569827557, -0.831468760969],
              [0.00272859287881, -0.38268324732799996, -0.923878729345],
              [0.0435272647635, -0.40590605139799996, -1.00043398142],
              [0.0435272647635, -0.21831315755899997, -1.05733972788],
              [0.00272859287881, -0.19509036839099997, -0.980784535409],
              [0.00272859287881, -2.0861669997387922e-07, -0.99999934435],
              [0.0435272647635, 0.007841132580800027, -1.07961422205],
              [0.0435272647635, 0.20293128490400003, -1.06039959192],
              [0.00272859287881, 0.19508993625600002, -0.9807847142230001],
              [0.00272859287881, 0.382682919502, -0.9238791465770001],
              [0.0435272647635, 0.420394599437, -0.994432926179],
              [0.0435272647635, 0.593281388282, -0.902023196222],
              [0.00272859287881, 0.555569648742, -0.8314694166200001],
              [0.00272859287881, 0.707106173038, -0.707106769086],
              [0.0435272647635, 0.7689469456670001, -0.757858216764],
              [0.0435272647635, 0.8933097720140001, -0.6063218712820001],
              [0.00272859287881, 0.8314689993850001, -0.555570423604],
              [0.00272859287881, 0.9238789677620001, -0.38268378377100004],
              [0.0435272647635, 1.0004341602300002, -0.40590658784000005],
              [0.0435272647635, 1.0573400258999999, -0.21831361949600006],
              [0.00272859287881, 0.980784773826, -0.19509081542600004],
              [0.00272859287881, 0.99999958277, -6.258500900519284e-07],
              [0.0435272647635, 1.0796144008600002, 0.007840688338999948],
              [0.0435272647635, 1.0603998899500002, 0.20293092727499995],
              [0.00272859287881, 0.980785012245, 0.19508960842999995],
              [0.00272859287881, 0.923879384994, 0.38268265127999995],
              [0.0435272647635, 0.99443304539, 0.420394331215], [0.0435272647635, 0.902023255825, 0.593281149863],
              [0.00272859287881, 0.831469595432, 0.555569410323],
              [0.00272859287881, 0.707106888294, 0.707105934619], [0.0435272647635, 0.757858335971, 0.768946707247],
              [0.0435272647635, 0.60632187128, 0.8933095931989999],
              [0.00272859287881, 0.555570423603, 0.8314688205709999],
              [0.00272859287881, 0.382683694362, 0.9238787889469999],
              [0.0435272647635, 0.40590649843200005, 1.0004339814199998],
              [0.0435272647635, 0.21831347048200003, 1.05733984709],
              [0.00272859287881, 0.19509066641300002, 0.9807845950109999],
              [0.00272859287881, 4.3213320002725986e-07, 0.99999940395],
              [0.0435272647635, -0.007840933278669974, 1.07961422205],
              [0.0435272647635, -0.20293121039899997, 1.06039959192],
              [0.00272859287881, -0.19508986175099996, 0.980784773825],
              [0.00272859287881, -0.382682979107, 0.92387908697],
              [0.0435272647635, -0.42039471864699995, 0.9944327473629999],
              [0.0435272647635, -0.593281507493, 0.9020228981959999],
              [0.00272859287881, -0.555569767952, 0.831469237803],
              [0.00272859287881, -0.707106351853, 0.7071064710599999],
              [0.0435272647635, -0.768947124482, 0.7578579187379999],
              [0.0435272647635, -0.8933100104339999, 0.606321394442],
              [0.00272859287881, -0.8314692378049999, 0.5555699467649999],
              [0.00272859287881, -0.923879206181, 0.38268312811699995],
              [0.0435272647635, -1.0004343986520001, 0.40590593218699994],
              [0.0435272647635, -1.05734026432, 0.21831282973199995],
              [0.00272859287881, -0.980785012246, 0.19509002566199996],
              [0.00272859287881, -0.999999761582, -2.9802455005180015e-07],
              [0.0435272647635, -1.0796144008600002, -0.007842143067550052],
              [0.0435272647635, -1.06039857864, -0.20293177664400006],
              [0.00272859287881, -0.9807839393619999, -0.19508992135700004]]

    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        self.curve = pm.curve(d=1, p=self.points, n=name)
        self.scale_shape([.9, .9, .9])
        self.normal_shape(normal)
        return self


class Ring(Control):
    def create(self, name="curve", normal=[1,0,0])-> 'Control':
        c1 = Circle().create(name)
        c2 = Circle().create(name)

        c1.move_shape([ 1, 0, 0])
        c2.move_shape([-1, 0, 0])

        c3 = pm.curve(p=[(1, 0, 1), (-1, 0, 1)], d=1)
        c4 = pm.curve(p=[(1, 0, -1), (-1, 0, -1)], d=1)
        c5 = pm.curve(p=[(1, 1, 0), (-1, 1, 0)], d=1)
        c6 = pm.curve(p=[(1, -1, 0), (-1, -1, 0)], d=1)

        [c1.combineShape(curve) for curve in [c3, c4, c5, c6, c2.curve]]
        c1.scale_shape([.2, 1, 1])

        self.curve = c1.curve
        self.normal_shape(normal)
        return self


class RingSphere(Control):
    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        n = 4
        angle = 360.0 / n
        # coord = [ (0,1,0), (0,-1,0), (0,0,-1), (0,0,1) ]
        control = pm.group(em=True)

        for i in range(n):
            sphere = Sphere().create(name)
            sphere.scale_shape([.2, .2, .2]).move_shape([0, 0, 1])
            cvs = [shape.cv for shape in sphere.curve.getShapes()]
            pm.xform(cvs, ro=[angle * i, 0, 0])

            pm.parent(sphere.curve.getShapes(), control, s=True, r=True)
            pm.delete(sphere.curve)

        self.curve = control
        self.normal_shape(normal)
        return self


class Pyramid(Control):
    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        control = Triangle().create(name)
        t2 = Triangle().create(name)
        sq = Square().create(name)

        t2.orient_shape([0, 90, 0])
        sq.orient_shape([45, 0, 90])
        sq.scale_shape([0.865, 0.865, 0.865])
        sq.move_shape([0, -0.498, 0])

        control.combineShape(t2.curve)
        control.combineShape(sq.curve)
        control.move_shape([0, .5, 0])
        control.scale_shape([.65, .65, .65])
        control.orient_shape([0, 0, -90])
        self.curve = control.curve
        self.normal_shape(normal)
        return self


class Slider(Control):
    def create(self, name="curve", normal= [1,0,0], limits=[0, 1])-> 'Control':
        offset = pm.curve(p=[(0, limits[0], 0), (0, limits[1], 0)], d=1, n= name)
        slider = pm.circle(normal=[0, 0, 1], d=1, s=4, n=f"{name}_slider")[0]
        pm.xform(slider.cv, ro=[90, 45, 90])
        pm.xform(slider.cv, scale=[0, 0.1, 0.25])

        pm.parent(slider, offset)

        offset_shape = offset.getShape()
        offset_shape.ove.set(True)
        offset_shape.overrideDisplayType.set(2)

        pm.transformLimits(slider, ety=(True, True), ty=(limits[0], limits[1]))
        [pm.setAttr("{}.{}".format(slider, at), lock=True, keyable=False, channelBox=False) for at in
         ["sx", "sy", "sz", "rx", "ry", "rz", "v", "tx", "tz"]]

        self.curve = offset
        return self


class Osipa(Control):
    def create(self, name="curve", normal=[1,0,0]) -> 'Control':
        offset = Square().create(name)
        control = Square().create(f"{name}_slider")

        offset.scale_shape([14, 14, 14])
        control.scale_shape([2, 2, 2])
        control.orient_shape([45, 0, 0])

        pm.parent(control.curve, offset.curve)
        pm.scale(offset.curve, .1, .1, .1)

        pm.transformLimits(control.curve, tx=(0, 0), etx=(True, True))
        pm.transformLimits(control.curve, ty=(-10, 10), ety=(True, True))
        pm.transformLimits(control.curve, tz=(-10, 10), etz=(True, True))

        # [pm.setAttr(offset + "." + a, lock=True, k=False, channelBox=False) for a in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]]
        [offset.curve.attr(a).lock() for a in ["v"]]
        [control.curve.attr(a).lock() for a in ["tx", "rx", "ry", "rz", "sx", "sy", "sz", "v"]]
        pm.setAttr(offset.curve.getShapes()[0] + ".overrideEnabled", True)
        pm.setAttr(offset.curve.getShapes()[0] + ".overrideDisplayType", 2)

        self.curve = offset.curve
        return self
