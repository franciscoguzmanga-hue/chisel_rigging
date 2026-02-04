from enum import Enum

import pymel.core as pm

from src.utility.transform_utils import align_transform, create_offset
from src.utility.constraint_utils import pointConstraint_many_to_one, aimConstraint_many_to_one, Vector, WorldUpType


TEMPLATE_SUFFIX = "_template"
ATTR_ID= "original"

# Template creation functions
def create_template_group() -> pm.nt.Transform:
    group_name = "template_group"
    if pm.objExists(group_name):
        return pm.nt.Transform(group_name)
    
    return pm.group(n=group_name, em=True)

def create_template_locator(name: str) -> pm.nt.Transform:
    if pm.objExists(name):
        return pm.nt.Transform(name)

    locator = pm.spaceLocator(name= name)
    locator.getShape().localScale.set(.2, .2, .2)

    normals = [(1,0,0),
               (0,1,0)
               (0,0,1)]
    for normal in normals:
        circle = pm.circle(normal=normal)
        pm.parent(circle.getShapes(), locator, s=True, r=True)
        pm.delete(circle)

    return locator

def create_templates(*selection: pm.nt.Transform) -> list:
    locators = []
    template_group = create_template_group()

    for obj in selection:
        name = f"{obj.name()}{TEMPLATE_SUFFIX}"
        locator = create_template_locator(name)

        if not locator.hasAttr(ATTR_ID):
            pm.addAttr(locator, ln=ATTR_ID, dt="string", keyable=True)

        locator.attr(ATTR_ID).set(obj.name())
        pm.delete(pm.parentConstraint(obj, locator))

        pm.parent(locator, template_group)
        locators.append(locator)

    return locators

def get_original_transform(locator: pm.nt.Transform) -> pm.nt.Transform:
    if not locator.hasAttr(ATTR_ID): return None

    object_name = locator.attr(ATTR_ID).get()
    if not pm.objExists(object_name): return None

    return pm.nt.Transform(object_name)

def move_objet_to_locator(*templates: pm.nt.Transform) -> list:
    original_objects = []
    for template in templates:
        original_object = get_original_transform(template)
        if not original_object: continue
        
        align_transform(template, original_object)
        original_objects.append(original_object)

    return original_objects

def move_locator_to_object(*templates: pm.nt.Transform) -> list:
    original_objects = []
    for template in templates:
        original_object = get_original_transform(template)
        if not original_object: continue

        align_transform(original_object, template)
        original_objects.append(original_object)
    return original_objects


# Template adjustments functions
def constraint_to_midpoint(locator_A: pm.nt.Transform, locator_B: pm.nt.Transform, locator_mid: pm.nt.Transform) -> None:
    locator_mid_offset = create_offset(locator_mid)
    point_constraint = pointConstraint_many_to_one(locator_A, locator_B, locator_mid_offset, maintain_offset=False)
    return point_constraint

def aim_to(master: pm.nt.Transform, slave: pm.nt.Transform) -> None:
    aim_constraint = aimConstraint_many_to_one(master, slave, 
                              maintain_offset=False, 
                              aim_vector=Vector.X_POS, 
                              up_vector=Vector.Z_POS, 
                              world_up_type=WorldUpType.OBJECT_ROTATE_AXIS, 
                              worldUpObject=master)
    return aim_constraint

