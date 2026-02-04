
import pymel.core as pm


# Mesh Interaction Functions
def orient_to_mesh_surface(mesh_transform: pm.nt.Transform, transform_node: pm.nt.Transform) -> None:
    normal_constraint = pm.normalConstraint( mesh_transform, transform_node)
    pm.delete(normal_constraint)

def move_to_mesh_surface(mesh_transform: pm.nt.Transform, transform_node: pm.nt.Transform) -> None:
    geometry_constraint = pm.geometryConstraint( mesh_transform, transform_node)
    pm.delete(geometry_constraint)

def delete_history(transform_node: pm.nt.Transform) -> None:
    pm.delete(transform_node, ch=True)


# UV Set Functions
def get_uv_sets(mesh: pm.nt.Mesh) -> list:
    return mesh.getUVSetNames()

def rename_uv_set(mesh: pm.nt.Mesh, old_name: str, new_name: str) -> None:
    mesh.renameUVSet(old_name, new_name)

def get_empty_uv_sets(mesh: pm.nt.Mesh) -> list:
    uv_sets = mesh.getUVSetNames()
    empty_uv_sets = []
    for uv_set in uv_sets:
        u_array, v_array = mesh.getUVs(uvSet=uv_set)
        if len(u_array) == 0 and len(v_array) == 0:
            empty_uv_sets.append(uv_set)
    return empty_uv_sets

def delete_uv_set(mesh: pm.nt.Mesh, uv_set_name: str) -> None:
    mesh.deleteUVSet(uv_set_name)

def delete_empty_uv_sets(mesh: pm.nt.Mesh) -> None:
    empty_uv_sets = get_empty_uv_sets(mesh)
    for uv_set in empty_uv_sets:
        mesh.deleteUVSet(uv_set)


"""def check_simmetry(mesh: pm.nt.Mesh, axis="x", tolerance=0.001) -> bool:
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
    return asymmetric_vertices"""

def check_non_manifold_geometry(mesh: pm.nt.Mesh) -> list:
    non_manifold_edges = mesh.getNonManifoldEdges()
    return non_manifold_edges

def check_n_gons(mesh: pm.nt.Mesh) -> list:
    n_gon_faces = []
    for face in mesh.f:
        connected_edges = face.getEdges()
        if len(connected_edges) > 4:
            n_gon_faces.append(face)
    return n_gon_faces

def check_zero_area_faces(mesh: pm.nt.Mesh, threshold=0.0001) -> list:
    zero_area_faces = []
    for face in mesh.f:
        area = face.getArea()
        if area < threshold:
            zero_area_faces.append(face)
    return zero_area_faces


# Intermediate Shape Functions
def get_intermediate_shapes(mesh_transform: pm.nt.Transform) -> list:
    shapes = mesh_transform.getShapes()
    intermediate_shapes = [shape for shape in shapes if shape.intermediateObject.get()]
    return intermediate_shapes

def delete_intermediate_shapes(mesh_transform: pm.nt.Transform) -> None:
    intermediate_shapes = get_intermediate_shapes(mesh_transform)
    pm.delete(intermediate_shapes)

def has_intermediate_shapes(mesh_transform: pm.nt.Transform) -> bool:
    intermediate_shapes = get_intermediate_shapes(mesh_transform)
    return len(intermediate_shapes) > 0

