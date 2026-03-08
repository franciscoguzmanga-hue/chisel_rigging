'''
Content: Common utility functions for rigging modules.
Dependency: pymel.core, time, functools
Maya Version tested: 2024

Author: Francisco Guzmán
Email: francisco.guzmanga@gmail.com
'''

import pymel.core as pm
import time
from functools import wraps


####################################################################################################################################
#  COMMON  #########################################################################################################################
####################################################################################################################################

def undo_chunk(name):
    def decorator(function):
        @wraps(function)
        def proxy(*args, **kwargs):
            start = time.perf_counter()
            pm.undoInfo(openChunk=True, cn=name)
            
            try:
                display_message(text=f"Executing: {name}", message_type=MessageType.INFO)
                func = function(*args, **kwargs)
                return func
            
            except Exception as ex:
                pm.undoInfo(closeChunk=True)
                error_message = f"{ex}.\n{name}'s Changes reversed"
                display_message(text=error_message, message_type=MessageType.ERROR)
                pm.undo()
                raise ex
            
            finally:
                if pm.undoInfo(q=True, openChunk=True):
                    pm.undoInfo(closeChunk=True)
                end = time.perf_counter()
                elapsed_time = end - start
                time_message = f"Time: {elapsed_time:.2f} seconds"
                display_message(text=time_message, message_type=MessageType.INFO)

        return proxy
    return decorator


class MessageType:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def display_message(text: str, message_type=MessageType.INFO):
    if not text: 
        raise ValueError("Message text cannot be empty.")

    display_type = {MessageType.INFO: pm.displayInfo,
                    MessageType.WARNING: pm.displayWarning,
                    MessageType.ERROR: pm.displayError}
    
    if message_type in display_type:
        display_type[message_type](text)
        

####################################################################################################################################
#  MATH FUNCTIONS  #################################################################################################################
####################################################################################################################################
def get_distance_between_vectors(point_a: pm.dt.Vector, point_b: pm.dt.Vector) -> float:
    vec_a = pm.datatypes.Vector(point_a)
    vec_b = pm.datatypes.Vector(point_b)
    return (vec_b - vec_a).length()

def get_distance_between_transforms(transform_a: pm.nt.Transform, transform_b: pm.nt.Transform) -> float:
    pos_a = pm.xform(transform_a, q=True, ws=True, t=True)
    pos_b = pm.xform(transform_b, q=True, ws=True, t=True)
    return get_distance_between_vectors(pos_a, pos_b)

def get_midpoint_between_vectors(point_a: pm.dt.Vector, point_b: pm.dt.Vector) -> pm.datatypes.Vector:
    vec_a = pm.datatypes.Vector(point_a)
    vec_b = pm.datatypes.Vector(point_b)
    midpoint = (vec_a + vec_b) / 2
    return midpoint

def get_midpoint_between_transforms(transform_a: pm.nt.Transform, transform_b: pm.nt.Transform) -> pm.datatypes.Vector:
    pos_a = pm.xform(transform_a, q=True, ws=True, t=True)
    pos_b = pm.xform(transform_b, q=True, ws=True, t=True)
    return get_midpoint_between_vectors(pos_a, pos_b)

def calculate_pole_vector(start_pos: pm.dt.Vector, end_pos: pm.dt.Vector, mid_pos: pm.dt.Vector, scale=1.0) -> pm.datatypes.Vector:
    """Find the location of the pole vector."""
    start_vec = pm.datatypes.Vector(start_pos)
    end_vec = pm.datatypes.Vector(end_pos)
    mid_vec = pm.datatypes.Vector(mid_pos)

    start_to_end = end_vec - start_vec
    start_to_mid = mid_vec - start_vec

    projection_length = start_to_mid * start_to_end.normal()
    projection_vec = start_to_end.normal() * projection_length

    perpendicular_vec = start_to_mid - projection_vec
    pole_vector = perpendicular_vec.normal() * scale

    return pole_vector + mid_vec


####################################################################################################################################
#  NAMING FUNCTIONS  ###############################################################################################################
####################################################################################################################################

def find_repeated_names() -> list[str]:
    """Search for repeated names in DAG nodes."""
    nodes = pm.ls("*", dag=True, long=True)
    repeated_names = [node.shortName() for node in nodes if "|" in node.shortName()]
    return list(set(repeated_names))

def convert_number_to_character(number: int) -> str:
    """Converts a non-negative integer to its corresponding Excel-style column name."""
    if number < 0: raise ValueError("Number must be non-negative.")
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    base = len(alphabet)
    result = ''
    while number >= 0:
        result = alphabet[number % base] + result
        number = number // base - 1
    return result

def convert_character_to_number(char: str) -> int:
    """Converts an Excel-style column name to its corresponding non-negative integer."""
    if not char.isalpha(): raise ValueError("Input must be a non-empty string of alphabetic characters.")
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    base = len(alphabet)
    result = 0
    for i, c in enumerate(reversed(char.upper())):
        result += (alphabet.index(c) + 1) * (base ** i)
    return result - 1


####################################################################################################################################
#  TYPE CHECKING FUNCTIONS ########################################################################################################
####################################################################################################################################

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

def is_vector(node: pm.PyNode) -> bool:
    return isinstance(node, pm.datatypes.Vector)

def is_component(node: pm.PyNode) -> bool:
    return isinstance(node, pm.Component)

####################################################################################################################################
#  FILTERING FUNCTIONS  ############################################################################################################
####################################################################################################################################

def filter_meshes(nodes: list[pm.PyNode]) -> list[pm.nt.Transform]:
    return [node for node in nodes if is_mesh(node)]

def filter_nurbs_surfaces(nodes: list[pm.PyNode]) -> list[pm.nt.Transform]:
    return [node for node in nodes if is_nurbs_surface(node)]

def filter_nurbs_curves(nodes: list[pm.PyNode]) -> list:
    return [node for node in nodes if is_nurbs_curve(node)]

def filter_locators(nodes: list[pm.PyNode]) -> list[pm.nt.Transform]:
    return [node for node in nodes if is_locator(node)] 

def filter_joints(nodes: list[pm.PyNode]) -> list[pm.nt.Joint]:
    return [node for node in nodes if is_joint(node)]

def filter_out_constraints(selection: list[pm.PyNode]) -> list[pm.PyNode]:
    return [node for node in selection if not isinstance(node, pm.nt.Constraint)]

def filter_out_joints(selection: list[pm.PyNode]) -> list[pm.PyNode]:
    return [node for node in selection if not is_joint(node)]

def filter_out_nurbs_curves(selection: list[pm.PyNode]) -> list[pm.PyNode]:
    return [node for node in selection if not is_nurbs_curve(node)]

def filter_out_nurbs_surfaces(selection: list[pm.PyNode]) -> list[pm.PyNode]:
    return [node for node in selection if not is_nurbs_surface(node)]

def filter_out_meshes(selection: list[pm.PyNode]) -> list[pm.PyNode]:
    return [node for node in selection if not is_mesh(node)]

def filter_out_locators(selection: list[pm.PyNode]) -> list[pm.PyNode]:
    return [node for node in selection if not is_locator(node)]


####################################################################################################################################
#  HIERARCHY FUNCTIONS ############################################################################################################
####################################################################################################################################

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



