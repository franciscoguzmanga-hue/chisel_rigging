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


from enum import Enum

import pymel.core as pm

from src.core.control_lib import Sphere
from src.utility.transform_utils import align_transform, create_offset
from src.utility.constraint_utils import pointConstraint_many_to_one, aimConstraint_many_to_one, Vector, WorldUpType


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

    sphere = Sphere()
    sphere.create("temp_name")
    shapes = sphere.transform.getShapes()
    pm.parent(shapes, locator, s=True, r=True)
    [shape.rename(f"{name}Shape") for shape in shapes]
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
        
        align_transform(template, original_object)
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

        align_transform(original_object, locator)
        original_objects.append(original_object)
    return original_objects


# Template adjustments functions
def constraint_to_midpoint(locator_A: pm.nt.Transform, locator_B: pm.nt.Transform, locator_mid: pm.nt.Transform, creates_offset=True) -> pm.nt.PointConstraint:
    """Using point constraint, moves the locator_mid to the exact middle position.
       Useful to find the correct position of knees and elbows.

    Args:
        locator_A (pm.nt.Transform): start position. Could be shoulder or Hip, etc.
        locator_B (pm.nt.Transform): end position. Could be wrist or ankle, etc.
        locator_mid (pm.nt.Transform): mid position. Could be elbow or knee, etc.

    Returns:
        pm.nt.PointConstraint: The created point constraint node.
    """
    locator_mid_offset = create_offset(locator_mid)
    point_constraint = pointConstraint_many_to_one(locator_A, locator_B, slave=locator_mid_offset, maintain_offset=False)
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
    aim_constraint = aimConstraint_many_to_one(master_locator, slave_locator, 
                                               maintain_offset=False, 
                                               aim_vector=Vector.X_POS, 
                                               up_vector=Vector.Z_POS, 
                                               world_up_type=WorldUpType.OBJECT_ROTATE_AXIS, 
                                               worldUpObject=master_locator)
    return aim_constraint

