'''
################################################################################################################
Author: Francisco Guzmán

Content: Tools to dissect and understand the internal structure of a rig to then make improvements or adjustments.
Dependency: pymel.core, src.utility.deformer_utils, src.utility.inspect_utils, src.utility.constraint_utils
Maya Version tested: 2024

How to:
    - Use: Import the module and call the functions as needed.
    - Test: Use pymel.core to create transform nodes and test the functions interactively in Maya.
################################################################################################################
'''


import pymel.core as pm

from src.utility.deformer_utils import get_skinCluster_nodes, get_skinCluster_influences, get_all_deformer_nodes, get_blendShape_nodes, get_blendshape_targets
from src.utility.inspect_utils import is_constraint, is_transform
from src.utility.constraint_utils import get_constraint_nodes, get_constraint_target

def get_inputs_from_attribute(node: pm.PyNode) -> list[pm.PyNode]:
    pass   

def get_outputs_from_attribute(node: pm.PyNode) -> list[pm.PyNode]:
    pass

def get_deformers_from_node(nodes: list[pm.PyNode]) -> list[pm.PyNode]:
    """Get all deformers from given node.

    Args:
        node (list[pm.PyNode]): List of transform nodes.

    Returns:
        list[pm.PyNode]: List of deformer nodes.
    """
    all_deformers = []
    for node in nodes:
        deformers = get_all_deformer_nodes(transform_node=node)
        all_deformers.extend(deformers)
    return all_deformers


# Blendshape functions
def get_all_blendshape_nodes(transforms: list[pm.nt.Transform]) -> list[pm.nt.BlendShape]:
    """Get blendshape node from given transform node list.

    Args:
        transforms (list[pm.nt.Transform]): List of transform nodes.

    Returns:
        list[pm.nt.BlendShape]: List of blendshape nodes.
    """
    blendshape_nodes = []
    for transform in transforms:
        deformers = get_blendShape_nodes(transform_node=transform)
        blendshape_nodes.extend(deformers)
    return blendshape_nodes

def get_all_blenshape_targets(transforms: list[pm.nt.Transform]) -> list[pm.nt.Transform]:
    """Get every blendshape target from given transforms.

    Args:
        transforms (list[pm.nt.Transform]): List of transform nodes.

    Returns:
        list[pm.nt.Transform]: List of blendshape target nodes.
    """
    blendshape_targets = []
    blendshape_nodes = get_all_blendshape_nodes(transforms=transforms)
    for blendshape in blendshape_nodes:
        targets = get_blendshape_targets(blendshape_node=blendshape)
        blendshape_targets.extend(targets)
    return blendshape_targets

# Skin Cluster functions
def get_all_skinCluster_nodes(transforms: list[pm.nt.Transform]) -> list[pm.nt.SkinCluster]:
    """Get every skin cluster node from transform list.

    Args:
        transforms (list[pm.nt.Transform]): List of transform nodes.

    Returns:
        list[pm.nt.SkinCluster]: List of skin cluster nodes.
    """
    skin_nodes = []
    for transform in transforms:
        skin_node = get_skinCluster_nodes(mesh=transform)
        skin_nodes.extend(skin_node)
    return skin_nodes

def get_all_influences(transforms: list[pm.nt.Transform]) -> list[pm.nt.Joint]:
    """Get every joint binded to skin cluster related to the current transforms lists.

    Args:
        transforms (list[pm.nt.Transform]): List of transform nodes.

    Returns:
        list[pm.nt.Joint]: List of joint nodes.
    """
    influences = []

    skin_cluster_nodes = get_all_skinCluster_nodes(*transforms)

    for skin_cluster in skin_cluster_nodes:
        node_influences = get_skinCluster_influences(skin_cluster_node=skin_cluster)
        influences.extend(node_influences)
    return influences


# Constraint functions
def get_all_constraint_nodes(transforms: list[pm.PyNode]) -> list[pm.nt.Constraint]:
    """Get every constraint node related to the transform list.

    Args:
        transforms (list[pm.PyNode]): List of transform nodes.

    Returns:
        list[pm.nt.Constraint]: List of constraint nodes.
    """
    constraint_nodes = []
    for node in transforms:
        if is_constraint(node):
            constraint_nodes.append(node)
        else:
            constraints = get_constraint_nodes(node)
            constraint_nodes.extend(constraints)
    return constraint_nodes

def get_all_constraint_targets(transforms: list[pm.PyNode]) -> list[pm.nt.Transform]:
    """Get every transform node that drives the nodes in the given list.

    Args:
        transforms (list[pm.PyNode]): List of transform nodes.

    Returns:
        list[pm.nt.Transform]: List of transform nodes.
    """
    constraint_targets = []
    for node in transforms:
        if is_constraint(node):
            targets = get_constraint_target(node)
            constraint_targets.extend(targets)
        if is_transform(node):
            constraints = get_all_constraint_nodes(node)
            targets = get_all_constraint_targets(*constraints)
            constraint_targets.extend(targets)
        else:
            continue


