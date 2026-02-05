'''
################################################################################################################
Author: Francisco Guzmán

Content: Basic utility functions for mesh nodes in Maya.
Dependency: pymel.core
Maya Version tested: 2024

How to:
    - Use: Import into your script and call the functions as needed.
    - Extend: Add more mesh-related utility functions as needed.
    - Test: Use pymel.core to get mesh and transform nodes and test the functions interactively in Maya.
################################################################################################################
'''



import pymel.core as pm

from src.utility.inspect_utils import is_mesh

# Mesh Interaction Functions
def orient_to_mesh_surface(mesh_transform: pm.nt.Transform, transform_node: pm.nt.Transform) -> None:
    """Orient a transform node to match the normal of a mesh surface.
    Args:
        mesh_transform (pm.nt.Transform): Mesh to get the surface normal from.
        transform_node (pm.nt.Transform): Transform node to orient.
    """
    normal_constraint = pm.normalConstraint( mesh_transform, transform_node)
    pm.delete(normal_constraint)

def move_to_mesh_surface(mesh_transform: pm.nt.Transform, transform_node: pm.nt.Transform) -> None:
    """Move a transform node to the closest point on a mesh surface.
    Args:
        mesh_transform (pm.nt.Transform): Mesh to get the closest point from.
        transform_node (pm.nt.Transform): Transform node to move.
    """
    geometry_constraint = pm.geometryConstraint( mesh_transform, transform_node)
    pm.delete(geometry_constraint)

def delete_history(transform_node: pm.nt.Transform) -> None:
    """Delete the construction history of a mesh transform node.
    Args:
        transform_node (pm.nt.Transform): Mesh transform node to delete history from.
    """
    pm.delete(transform_node, ch=True)


# UV Set Functions
def get_uv_sets(mesh_transform: pm.nt.Transform) -> list[str]:
    """Get all UV set names from the given mesh.
    Args:
        mesh (pm.nt.Mesh): Mesh to get UV sets from.
    Returns:
        list[str]: List of UV set names.
    """
    if not is_mesh(mesh_transform): return []
    
    mesh = mesh_transform.getShape()
    return mesh.getUVSetNames()

def rename_uv_set(mesh_transform: pm.nt.Transform, old_name: str, new_name: str) -> None:
    """Rename a UV set on the given mesh.
    Args:
        mesh (pm.nt.Mesh): Mesh to rename UV set on.
        old_name (str): Old name of the UV set.
        new_name (str): New name for the UV set.
    """
    if not is_mesh(mesh_transform): return None
    mesh = mesh_transform.getShape()
    mesh.renameUVSet(old_name, new_name)

def get_empty_uv_sets(mesh_transform: pm.nt.Transform) -> list[str]:    
    """Get all empty UV sets from the given mesh.
    Args:
        mesh_transform (pm.nt.Transform): Mesh to get empty UV sets from.
    Returns:
        list[str]: List of empty UV set names.
    """
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
    """Delete a UV set from the given mesh.
    Args:
        mesh_transform (pm.nt.Transform): Mesh to delete UV set from.
        uv_set_name (str): Name of the UV set to delete.
    """
    if not is_mesh(mesh_transform): return None
    mesh = mesh_transform.getShape()
    mesh.deleteUVSet(uv_set_name)

def delete_empty_uv_sets(mesh_transform: pm.nt.Transform) -> None:
    """Delete all empty UV sets from the given mesh.
    Args:
        mesh_transform (pm.nt.Transform): Mesh to delete empty UV sets from.
    """
    if not is_mesh(mesh_transform): return None
    
    empty_uv_sets = get_empty_uv_sets(mesh_transform)
    mesh = mesh_transform.getShape()
    for uv_set in empty_uv_sets:
        mesh.deleteUVSet(uv_set)


def check_simmetry(mesh: pm.nt.Mesh, axis="x", tolerance=0.001) -> bool:
    """Check for simmetry in the given mesh along the specified axis.
    
    Args:        
        mesh (pm.nt.Mesh): Mesh to check for simmetry.
        axis (str, optional): Axis to check for simmetry. Defaults to "x".
        tolerance (float, optional): Tolerance for simmetry check. Defaults to 0.001.
    
    Returns:        
        bool: True if the mesh is simmetrical, False otherwise.
    """
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
    """Check for n-gon faces in the given mesh.
    
    Args:
        mesh_transform (pm.nt.Transform): Mesh to check for n-gons.
        
    Returns:
        list[pm.nt.Face]: List of n-gon faces.
    """
    if not is_mesh(mesh_transform): return []
    mesh = mesh_transform.getShape()
    n_gon_faces = []
    for face in mesh.f:
        connected_edges = face.getEdges()
        if len(connected_edges) > 4:
            n_gon_faces.append(face)
    return n_gon_faces

def check_zero_area_faces(mesh: pm.nt.Mesh, threshold=0.0001) -> list[pm.nt.Face]:
    """Check for faces with zero or near-zero area in the given mesh.
    Args:
        mesh (pm.nt.Mesh): Mesh to check for zero area faces.
        threshold (float, optional): Area threshold to consider a face as zero area. Defaults to 0.0001.
    Returns:
        list[pm.nt.Face]: List of zero area faces.
    """
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

