'''
Content: Basic utility functions for mesh nodes in Maya.
Dependency: pymel.core
Maya Version tested: 2024

Author: Francisco Guzmán

How to:
    - Use: Import into your script and call the functions as needed.
    - Extend: Add more mesh-related utility functions as needed.
    - Test: Use pymel.core to get mesh and transform nodes and test the functions interactively in Maya.

'''

import pymel.core as pm
from src.utility.inspect_utils import is_mesh


# Mesh Interaction Functions
def orient_to_mesh_surface(mesh_transform: pm.nt.Transform, transform_node: pm.nt.Transform) -> None:
    """Orient a transform node to match the normal of a mesh surface."""
    normal_constraint = pm.normalConstraint( mesh_transform, transform_node)
    pm.delete(normal_constraint)

def move_to_mesh_surface(mesh_transform: pm.nt.Transform, transform_node: pm.nt.Transform) -> None:
    """Move a transform node to the closest point on a mesh surface."""
    geometry_constraint = pm.geometryConstraint( mesh_transform, transform_node)
    pm.delete(geometry_constraint)


# UV Set Functions
def get_uv_sets(mesh_transform: pm.nt.Transform) -> list[str]:
    if not is_mesh(mesh_transform): return []
    
    mesh = mesh_transform.getShape()
    return mesh.getUVSetNames()

def rename_uv_set(mesh_transform: pm.nt.Transform, old_name: str, new_name: str) -> None:
    if not is_mesh(mesh_transform): return None
    mesh = mesh_transform.getShape()
    mesh.renameUVSet(old_name, new_name)

def get_empty_uv_sets(mesh_transform: pm.nt.Transform) -> list[str]:
    if not is_mesh(mesh_transform): return []
    
    mesh = mesh_transform.getShape()
    uv_sets = mesh.getUVSetNames()
    empty_uv_sets = []
    for uv_set in uv_sets:
        u_array, v_array = mesh.getUVs(uvSet=uv_set)
        if len(u_array) == 0 and len(v_array) == 0:
            empty_uv_sets.append(uv_set)
    return empty_uv_sets

def delete_uv_set(mesh_transform: pm.nt.Transform, uv_set_name: str) -> None:
    if not is_mesh(mesh_transform): return None
    mesh = mesh_transform.getShape()
    mesh.deleteUVSet(uv_set_name)

def delete_empty_uv_sets(mesh_transform: pm.nt.Transform) -> None:
    if not is_mesh(mesh_transform): return None
    
    empty_uv_sets = get_empty_uv_sets(mesh_transform)
    mesh = mesh_transform.getShape()
    for uv_set in empty_uv_sets:
        mesh.deleteUVSet(uv_set)


def check_symmetry(mesh: pm.nt.Mesh, axis="x", tolerance=0.001) -> bool:
    """Check for simmetry in the given mesh along the specified axis."""
    vertices = mesh.vtx
    asymmetric_vertices = []
    for vtx in vertices:
        pos = pm.xform(vtx, q=True, ws=True, t=True)
        mirrored_pos = list(pos)
        axis_index = {"x": 0, "y": 1, "z": 2}
        mirrored_pos[axis_index[axis]] *= -1

        closest_point = mesh.getClosestPoint(pm.datatypes.Vector(mirrored_pos), space='world')
        distance = pm.datatypes.Vector(pos).distanceTo(closest_point)

        if distance > tolerance:
            asymmetric_vertices.append(vtx)
    return asymmetric_vertices

def check_non_manifold_geometry(mesh_transform: pm.nt.Transform) -> list[pm.nt.Edge]:
    """Check for non-manifold edges in the given mesh."""
    if not is_mesh(mesh_transform): return []
    mesh = mesh_transform.getShape()
    non_manifold_edges = mesh.getNonManifoldEdges()
    return non_manifold_edges

def check_n_gons(mesh_transform: pm.nt.Transform) -> list[pm.nt.Face]:
    """Check for n-gon faces in the given mesh."""
    if not is_mesh(mesh_transform): return []
    mesh = mesh_transform.getShape()
    n_gon_faces = []
    for face in mesh.f:
        connected_edges = face.getEdges()
        if len(connected_edges) > 4:
            n_gon_faces.append(face)
    return n_gon_faces

def check_zero_area_faces(mesh: pm.nt.Mesh, threshold=0.0001) -> list[pm.nt.Face]:
    """Check for faces with zero or near-zero area in the given mesh."""
    zero_area_faces = []
    for face in mesh.f:
        area = face.getArea()
        if area < threshold:
            zero_area_faces.append(face)
    return zero_area_faces


# Intermediate Shape Functions
def get_intermediate_shapes(mesh_transform: pm.nt.Transform) -> list[pm.nt.Shape]:
    """Get all intermediate shapes from the given mesh."""
    shapes = mesh_transform.getShapes()
    intermediate_shapes = [shape for shape in shapes if shape.intermediateObject.get()]
    return intermediate_shapes

def delete_intermediate_shapes(mesh_transform: pm.nt.Transform) -> None:
    """Delete all intermediate shapes from the given mesh."""
    intermediate_shapes = get_intermediate_shapes(mesh_transform)
    pm.delete(intermediate_shapes)

def has_intermediate_shapes(mesh_transform: pm.nt.Transform) -> bool:
    """Check if the given mesh has intermediate shapes."""
    intermediate_shapes = get_intermediate_shapes(mesh_transform)
    return len(intermediate_shapes) > 0

