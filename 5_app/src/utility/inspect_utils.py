
'''
################################################################################################################
Author: Francisco Guzmán

Content: Basic utility functions for inspecting node types in Maya.
Dependency: pymel.core
Maya Version tested: 2024

How to:
    - Use: Import the module and call the functions as needed.
    - Test: Use pymel.core to create nodes and test the functions interactively in Maya.
################################################################################################################
'''


import pymel.core as pm

# Type checking utility functions
def get_shape(node: pm.PyNode) -> pm.PyNode:
    if hasattr(node, 'getShape'):
        return node.getShape()
    return node

def is_transform(node: pm.PyNode) -> bool:
    return isinstance(node, pm.nt.Transform)

def is_mesh(node: pm.PyNode) -> bool:
    shape = get_shape(node)
    return isinstance(shape, pm.nt.Mesh)

def is_nurbs_surface(node: pm.PyNode) -> bool:
    shape = get_shape(node)
    return isinstance(shape, pm.nt.NurbsSurface)

def is_nurbs_curve(node: pm.PyNode) -> bool:
    shape = get_shape(node)
    return isinstance(shape, pm.nt.NurbsCurve)

def is_locator(node: pm.PyNode) -> bool:
    shape = get_shape(node)
    return isinstance(shape, pm.nt.Locator)

def is_joint(node: pm.PyNode) -> bool:
    return isinstance(node, pm.nt.Joint)

def is_constraint(node: pm.PyNode) -> bool:
    return isinstance(node, pm.nt.Constraint)

def is_type(node: pm.PyNode, node_type: pm.PyNode) -> bool:
    shape = get_shape(node)
    return isinstance(shape, node_type)



# Filtering functions
def filter_meshes(nodes: list) -> list:
    return [node for node in nodes if is_mesh(node)]

def filter_nurbs_surfaces(nodes: list) -> list:
    return [node for node in nodes if is_nurbs_surface(node)]

def filter_nurbs_curves(nodes: list) -> list:
    return [node for node in nodes if is_nurbs_curve(node)]

def filter_locators(nodes: list) -> list:
    return [node for node in nodes if is_locator(node)] 

def filter_joints(nodes: list) -> list:
    return [node for node in nodes if is_joint(node)]

def filter_out_constraints(selection: list) -> list:
    return [node for node in selection if not isinstance(node, pm.nt.Constraint)]

def filter_out_joints(selection: list) -> list:
    return [node for node in selection if not is_joint(node)]

def filter_out_nurbs_curves(selection: list) -> list:
    return [node for node in selection if not is_nurbs_curve(node)]

def filter_out_nurbs_surfaces(selection: list) -> list:
    return [node for node in selection if not is_nurbs_surface(node)]

def filter_out_meshes(selection: list) -> list:
    return [node for node in selection if not is_mesh(node)]

def filter_out_locators(selection: list) -> list:
    return [node for node in selection if not is_locator(node)]


# Hierarchy functions
def get_leaf_nodes(selection: list) -> list[pm.nt.Transform]:
    """Get every node without children from the given selection."""
    leaf_nodes = [node for node in selection if not node.getChildren(type= pm.nt.Transform)]
    return leaf_nodes

def get_no_leaf_nodes(selection: list) -> list[pm.nt.Transform]:
    """Get every node with children from the given selection."""
    no_leaf_nodes = [node for node in selection if node.getChildren(type= pm.nt.Transform)]
    return no_leaf_nodes

def get_top_level_nodes(nodes: list) -> list[pm.nt.Transform]:
    """Get every top level node from the given list (nodes without parents in the list)."""
    top_level_nodes = []
    node_set = set(nodes)
    for node in nodes:
        parent = pm.listRelatives(node, parent=True)
        if not parent or parent[0] not in node_set:
            top_level_nodes.append(node)
    return top_level_nodes


