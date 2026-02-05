'''
################################################################################################################
Author: Francisco Guzmán

Content: Collection of constraint functions to apply and get information from constraint nodes.
Dependency: pymel.core, src.utility.attribute_utils
Maya Version tested: 2024

How to:
    - Use: Import the module and call the functions as needed.
    - Test: Use pymel.core to create transform nodes and test the functions interactively in Maya.
################################################################################################################
'''


from enum import Enum

import pymel.core as pm

from src.utility.attribute_utils import Vector


class WorldUpType(Enum):
    SCENE   = "scene"
    OBJECT  = "object"
    OBJECT_ROTATE_AXIS = "objectrotation"
    VECTOR  = "vector"
    NONE    = "none"


# Constraint Utility Functions
def get_constraint_nodes(transform_node: pm.nt.Transform) -> list:
    constraints = pm.listRelatives(transform_node, type="constraint")
    return constraints

def get_constraint_target(constraint_node: pm.nt.Constraint) -> list:
    return constraint_node.getTargetList()

def parentConstraint_one_to_many(master: pm.nt.Transform, *slaves: pm.nt.Transform, maintain_offset=True) -> list:
    constraints = []
    for slave in slaves:
        constraint = pm.parentConstraint(master, slave, mo=maintain_offset)
        constraints.append(constraint)
    return constraints

def parentConstraint_many_to_one(*masters: pm.nt.Transform, slave: pm.nt.Transform, maintain_offset=True) -> pm.nt.ParentConstraint:
    constraint = pm.parentConstraint(masters, slave, mo=maintain_offset)
    return constraint

def scaleConstraint_one_to_many(master: pm.nt.Transform, *slaves: pm.nt.Transform, maintain_offset=True) -> list:
    constraints = []
    for slave in slaves:
        constraint = pm.scaleConstraint(master, slave, mo=maintain_offset)
        constraints.append(constraint)
    return constraints

def scaleConstraint_many_to_one(*masters: pm.nt.Transform, slave: pm.nt.Transform, maintain_offset=True) -> pm.nt.ScaleConstraint:
    constraint = pm.scaleConstraint(masters, slave, mo=maintain_offset)
    return constraint

def orientConstraint_one_to_many(master: pm.nt.Transform, *slaves: pm.nt.Transform, maintain_offset=True) -> list:
    constraints = []
    for slave in slaves:
        constraint = pm.orientConstraint(master, slave, mo=maintain_offset)
        constraints.append(constraint)
    return constraints

def orientConstraint_many_to_one(*masters: pm.nt.Transform, slave: pm.nt.Transform, maintain_offset=True) -> pm.nt.OrientConstraint:
    constraint = pm.orientConstraint(masters, slave, mo=maintain_offset)
    return constraint

def pointConstraint_one_to_many(master: pm.nt.Transform, *slaves: pm.nt.Transform, maintain_offset=True) -> list:
    constraints = []
    for slave in slaves:
        constraint = pm.pointConstraint(master, slave, mo=maintain_offset)
        constraints.append(constraint)
    return constraints

def pointConstraint_many_to_one(*masters: pm.nt.Transform, slave: pm.nt.Transform, maintain_offset=True) -> pm.nt.PointConstraint:
    constraint = pm.pointConstraint(masters, slave, mo=maintain_offset)
    return constraint

def aimConstraint_many_to_one(master: pm.nt.Transform, *slaves: pm.nt.Transform, 
                              maintain_offset=True, 
                              aim_vector=Vector.X_POS, 
                              up_vector= Vector.Y_POS, 
                              world_up_type= WorldUpType.SCENE,
                              worldUpObject: pm.nt.Transform = None) -> list:
    constraints = []
    for slave in slaves:
        constraint = pm.aimConstraint(master, slave, 
                                      mo=maintain_offset, 
                                      aimVector  =aim_vector.value      if isinstance(aim_vector, Vector)         else aim_vector, 
                                      upVector   =up_vector.value       if isinstance(up_vector,  Vector)         else up_vector,
                                      worldUpType=world_up_type.value   if isinstance(world_up_type, WorldUpType) else world_up_type,
                                      worldUpObject=worldUpObject if worldUpObject else None)
        constraints.append(constraint)
    return constraints

