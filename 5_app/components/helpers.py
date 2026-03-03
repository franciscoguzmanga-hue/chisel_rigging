'''
################################################################################################################
Author: Francisco Guzmán

Content: 
    Collection of functions to create and manipulate templates to use as reference for easy manipulation in viewport.
    This module is made to interact with any other third party auto-rig to simplify the process of placing joints and other rig elements.

Dependency: pymel.core, src.utility.transform_utils, src.utility.constraint_utils
Maya Version tested: 2024

How to:
    - Use: 
        - Execute the create_templates function with a selection of transform nodes to create template locators.
        - Use move_objet_to_locator and move_locator_to_object to transfer positions between original objects and their templates.
        - Use constraint_to_midpoint to position mid-joint templates like elbows and knees.
        - Use aim_to to orient templates like knees, elbows, and finger knuckles.
    - Test: Use the test in src.test.rigging_modules.template_test to see an example of how to use the module and test it interactively in Maya.
    
################################################################################################################
'''

import pymel.core as pm
import core.control_framework as control_lib
import utility.maya_lib as maya_lib


TEMPLATE_SUFFIX = "_template"
ATTR_ID= "original"

# Template creation functions
def create_template_group() -> pm.nt.Transform:
    """Create the base group to store every template locator created to keep outliner clean.

    Returns:
        pm.nt.Transform: The template group transform node.
    """
    group_name = "template_group"
    if pm.objExists(group_name):
        return pm.nt.Transform(group_name)
    
    return pm.group(n=group_name, em=True)

def create_template_locator(name: str) -> pm.nt.Transform:
    """Create locator with a sphere-like curves to have as reference when placing joints or any other rig teamplate or mesh.
    Useful to use as reference and work in conjunction with any template from any auto-rig.

    Returns:
        pm.nt.Transform: The template locator transform node.
    """
    if pm.objExists(name):
        return pm.nt.Transform(name)

    locator = pm.spaceLocator(name= name)
    locator.getShape().localScale.set(.2, .2, .2)

    sphere = control_lib.Sphere("temp_name")
    sphere.create()
    pm.parent(sphere.shapes, locator, s=True, r=True)
    [shape.rename(f"{name}Shape") for shape in sphere.shapes]
    pm.delete(sphere.transform)

    return locator

def create_templates(selection: list[pm.nt.Transform]) -> list[pm.nt.Transform]:
    """Creates template locators on the same location of every transform node from the selection given, 
       and associate the original transform to each locator via attribute.

    Returns:
        list: List of template locator transform nodes.
    """
    locators = []
    template_group = create_template_group()

    for obj in selection:
        name = f"{obj.name()}{TEMPLATE_SUFFIX}"
        locator = create_template_locator(name)

        if not locator.hasAttr(ATTR_ID):
            pm.addAttr(locator, ln=ATTR_ID, dt="string", keyable=True)

        locator.attr(ATTR_ID).set(obj.name(long=True))
        move_locator_to_object([locator])
        #pm.delete(pm.parentConstraint(obj, locator))

        pm.parent(locator, template_group)
        locators.append(locator)

    return locators

def get_original_transform(locator: pm.nt.Transform) -> pm.nt.Transform:
    """Get the original transform from the given locator using it's ID.
       If the original transform doesn't exist or the transform has no ATTR_ID attribute, return None.

    Args:
        locator (pm.nt.Transform): Template locator transform node.

    Returns:
        pm.nt.Transform: The original transform node associated with the locator.
    """
    if not locator.hasAttr(ATTR_ID): return None

    object_name = locator.attr(ATTR_ID).get()
    if not pm.objExists(object_name): return None

    return pm.nt.Transform(object_name)

def move_objet_to_locator(locators: list[pm.nt.Transform]) -> list[pm.nt.Transform]:
    """Move original objects to the location of the given locators.

    Args:
        locators (list[pm.nt.Transform]): List of template locator transform nodes.

    Returns:
        list[pm.nt.Transform]: List of original transform nodes moved to the locators' positions.
    """
    original_objects = []
    locators = sorted(locators, key=lambda loc: loc.attr(ATTR_ID).get())
    for template in locators:
        original_object = get_original_transform(template)
        if not original_object: continue
        
        maya_lib.align_transform(template, original_object)
        original_objects.append(original_object)

    return original_objects

def move_locator_to_object(locators: list[pm.nt.Transform]) -> list[pm.nt.Transform]:
    """Move locators to the position of the original transforms.

    Args:
        locators (list[pm.nt.Transform]): List of template locator transform nodes.

    Returns:
        list[pm.nt.Transform]: List of original transform nodes moved to the locators' positions.
    """
    original_objects = []
    for locator in locators:
        original_object = get_original_transform(locator)
        if not original_object: continue

        maya_lib.align_transform(original_object, locator)
        original_objects.append(original_object)
    return original_objects


# Template adjustments functions
def constraint_to_midpoint(locator_A: pm.nt.Transform, locator_B: pm.nt.Transform, locator_mid: pm.nt.Transform) -> pm.nt.PointConstraint:
    """Using point constraint, moves the locator_mid to the exact middle position.
       Useful to find the correct position of knees and elbows.

    Args:
        locator_A (pm.nt.Transform): start position. Could be shoulder or Hip, etc.
        locator_B (pm.nt.Transform): end position. Could be wrist or ankle, etc.
        locator_mid (pm.nt.Transform): mid position. Could be elbow or knee, etc.

    Returns:
        pm.nt.PointConstraint: The created point constraint node.
    """
    locator_mid_offset = maya_lib.create_offset(locator_mid)
    point_constraint = maya_lib.pointConstraint_many_to_one(locator_A, locator_B, slave=locator_mid_offset, maintain_offset=False)
    return point_constraint

def aim_to(master_locator: pm.nt.Transform, slave_locator: pm.nt.Transform) -> pm.nt.AimConstraint:
    """Predefined aimConstraint to setup the orientation of the slave_locator.
       By default uses X axis a aim vector and master_locator's Z axis as up vector.
       Useful to orient points like knees, elbows, finger knuckles, etc.

    Args:
        master_locator (pm.nt.Transform): Driver locator.
        slave_locator (pm.nt.Transform): Locator that will aim to the master_locator.

    Returns:
        pm.nt.AimConstraint: The created aim constraint node.
    """
    aim_constraint = maya_lib.aimConstraint_many_to_one(master_locator, slave_locator, 
                                               maintain_offset=False, 
                                               aim_vector=maya_lib.Vector.X_POS, 
                                               up_vector=maya_lib.Vector.Z_POS, 
                                               world_up_type=maya_lib.WorldUpType.OBJECT_ROTATE_AXIS, 
                                               worldUpObject=master_locator)
    return aim_constraint











############################################################################################################
'''
Content: Rigging module to build a zipper.
Dependency: List dependencies or requirements
Maya Version tested: 2024

Author: Francisco Guzmán
Email: francisco.guzmanga@gmail.com
How to:
    - Use: Instructions to use the module
    - Test: Instructions to test the module

TODO: Refactor code.
'''


import pymel.core as pm


class Sticky:
    def __init__(self, start, end, name):
        self.name = name
        self.start = start
        self.end = end
        self.mid = None

        self.sticky_attr_name = "stick"
        self.create_mid_space(start, end)
        self.start_sticky   = self.create_sticky(self.start, self.mid, f"{self.name}_A")
        self.end_sticky     = self.create_sticky(self.end,   self.mid, f"{self.name}_B")
        
    def create_mid_space(self, point_A, point_B):
        mid_name = f"{self.name}_mid"
        mid = pm.nt.Transform(mid_name) if pm.objExists(mid_name) else pm.spaceLocator(n= mid_name)
            
        blend = pm.nt.BlendMatrix(n= f"{self.name}_blend")
        point_A.worldMatrix >> blend.inputMatrix
        point_B.worldMatrix >> blend.target[0].targetMatrix
        blend.target[0].weight.set(0.5)
        blend.outputMatrix >> mid.offsetParentMatrix
        self.mid = mid

    def create_sticky(self, point_A, point_B, name):
        mid_name = f"{name}_sticky"
        mid = pm.nt.Transform(mid_name) if pm.objExists(mid_name) else pm.spaceLocator(n=mid_name)

        blend_name = f"{name}_blendSticky"
        blend = pm.nt.BlendMatrix(n=blend_name)
        point_A.worldMatrix >> blend.inputMatrix
        point_B.worldMatrix >> blend.target[0].targetMatrix
        blend.outputMatrix >> mid.offsetParentMatrix

        if not point_B.hasAttr(self.sticky_attr_name):
            pm.addAttr(point_B, ln=self.sticky_attr_name, max=1, min=0, dv=0, k=True)
        point_B.attr(self.sticky_attr_name) >> blend.target[0].weight
        return mid
        #blend.target[0].weight.set(0.5)


class Zipper:
    def __init__(self, zipper_control, *points):
        self.points = points
        self.n_joints = len(points[0])
        self.horizontal_delta = 10/(self.n_joints+1)
        self.slope = self.calculate_slope()
        self.zipper_control = zipper_control

    def calculate_slope(self):
        """
        slope = (Y0-Y1)/X0-X1
        """
        return 1/self.horizontal_delta

    def calculate_intercept(self, x_pos):
        """
        Y= slope*X + intercept
        intercept = Y - slope * X
        """
        return 1 - self.slope * x_pos

    def set_zipper_behavior(self, x_position, sticky_attr, zipper_attr, zipper_spread_attr, name):
        """
            variable: float. Value when Y=1.
            Y = mX + b
        """
        object_set = pm.nt.ObjectSet("test_set")
        slope_mult_X = pm.nt.Multiply(n=f"{name}_slope_X")
        zipper_attr >> slope_mult_X.input[0]
        slope_mult_X.input[1].set(x_position)
        
        add_intersect = pm.nt.Multiply(n=f"{name}_add_intersect")
        slope_mult_X.output >> add_intersect.input[0]
        zipper_spread_attr >> add_intersect.input[1]
        #add_intersect.input[1].set(1)

        clamp_node = pm.nt.Clamp(n=f"{name}_clamp_sdk")
        add_intersect.output >> clamp_node.inputR
        clamp_node.minR.set(0)
        clamp_node.maxR.set(1)

        if "012" in name:
            object_set.addMember(slope_mult_X)
            object_set.addMember(add_intersect)
            object_set.addMember(clamp_node)

        inputs = sticky_attr.inputs(plugs=True)
        if len(inputs)==0:
            clamp_node.outputR >> sticky_attr

        else:
            print(f"ASDF: {sticky_attr.inputs(plugs=True)} >> {sticky_attr}")
            equalize_mult = pm.nt.Sum(n=f"{name}_equalize")
            equalize_mult.output >> sticky_attr

            if "012" in name:
                object_set.addMember(equalize_mult)

            for index, input in enumerate(inputs):
                input >> equalize_mult.input[index]
            clamp_node.outputR >> equalize_mult.input[len(inputs)]


        #add_intersect.output >> sticky_attr

    def set_zipper_behavior_SDK(self, driver_attr, driven_attr, driver_value, driven_value, step):
        pm.setDrivenKeyframe(driven_attr, currentDriver= driver_attr, dv= driver_value,      v= 0)
        pm.setDrivenKeyframe(driven_attr, currentDriver= driver_attr, dv= driver_value+step*4, v= 1)


    def build_zipper(self, array_A, array_B, zipper_attr, zipper_spread_attr):
        for start, end in zip(array_A, array_B):
            index = self.points[0].index(start)
            name = f"{start.name()}"
            sticky = Sticky(start, end, name)

            sticky_attr = sticky.mid.attr(sticky.sticky_attr_name)
            self.set_zipper_behavior_SDK(driver_attr  = zipper_attr,
                                         driven_attr  = sticky_attr,
                                         driver_value = index * self.horizontal_delta,
                                         driven_value = 0,
                                         step         = self.horizontal_delta)
            """self.set_zipper_behavior(x_position=index * self.horizontal_delta,
                                     sticky_attr=sticky_attr,
                                     zipper_attr=zipper_attr,
                                     zipper_spread_attr=zipper_spread_attr,
                                     name=name)"""


    def build(self):
        attr_A = "zipper_A"
        attr_B = "zipper_B"
        attr_zipper_spread = "zipper_spread"
        if not self.zipper_control.hasAttr(attr_A):
            pm.addAttr(self.zipper_control, ln=attr_A, min=0, dv=0, k=True)
        if not self.zipper_control.hasAttr(attr_B):
            pm.addAttr(self.zipper_control, ln=attr_B, min=0, dv=0, k=True)
        if not self.zipper_control.hasAttr(attr_zipper_spread):
            pm.addAttr(self.zipper_control, ln=attr_zipper_spread, min=0, dv=1, k=True)


        upp_joints = self.points[0]
        dwn_joints = self.points[1]

        self.build_zipper(upp_joints, dwn_joints, self.zipper_control.zipper_A, self.zipper_control.zipper_spread)

        upp_joints.reverse()
        dwn_joints.reverse()

        self.build_zipper(upp_joints, dwn_joints, self.zipper_control.zipper_B, self.zipper_control.zipper_spread)



        """stickys = []
        for start, end in zip(upp_joints, dwn_joints):
            index = self.points[0].index(start)
            name = f"{start.name()}_{str(index).zfill(3)}"
            sticky = Sticky(start, end, name)
            stickys.append(sticky)


            print(sticky.sticky_attr_name)
            attr_name = sticky.sticky_attr_name
            sticky_attr = sticky.mid.attr("stick")

            self.set_zipper_behavior(index*self.horizontal_delta, sticky_attr, transform.zipper_spread)"""

        

        



