'''
Content: Basic utility functions for mesh related nodes in Maya.
Dependency: pymel.core, common
Maya Version tested: 2024

Author: Francisco Guzmán
Email: francisco.guzmanga@gmail.com
'''

import pymel.core as pm
import utility.common as common
import utility.mesh_lib as mesh_lib

# Mesh Interaction Functions
def orient_to_mesh_surface(mesh_transform: pm.nt.Transform, transform_node: pm.nt.Transform):
    """Orient a transform node to match the normal of a mesh surface."""
    normal_constraint = pm.normalConstraint( mesh_transform, transform_node)
    pm.delete(normal_constraint)

def move_to_mesh_surface(mesh_transform: pm.nt.Transform, transform_node: pm.nt.Transform):
    """Move a transform node to the closest point on a mesh surface."""
    geometry_constraint = pm.geometryConstraint( mesh_transform, transform_node)
    pm.delete(geometry_constraint)


# UV Set Functions
def get_uv_sets(mesh_transform: pm.nt.Transform) -> list[str]:
    if not common.is_mesh(mesh_transform): return []
    
    mesh = mesh_transform.getShape()
    return mesh.getUVSetNames()

def rename_uv_set(mesh_transform: pm.nt.Transform, old_name: str, new_name: str):
    if not common.is_mesh(mesh_transform): return None
    mesh = mesh_transform.getShape()
    mesh.renameUVSet(old_name, new_name)

def get_empty_uv_sets(mesh_transform: pm.nt.Transform) -> list[str]:
    if not common.is_mesh(mesh_transform): return []
    
    mesh = mesh_transform.getShape()
    uv_sets = mesh.getUVSetNames()
    empty_uv_sets = []
    for uv_set in uv_sets:
        u_array, v_array = mesh.getUVs(uvSet=uv_set)
        if len(u_array) == 0 and len(v_array) == 0:
            empty_uv_sets.append(uv_set)
    return empty_uv_sets

def delete_uv_set(mesh_transform: pm.nt.Transform, uv_set_name: str):
    if not common.is_mesh(mesh_transform): return None
    mesh = mesh_transform.getShape()
    mesh.deleteUVSet(uv_set_name)

def delete_empty_uv_sets(mesh_transform: pm.nt.Transform):
    if not common.is_mesh(mesh_transform): return None
    
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

def check_non_manifold_geometry(mesh_transform: pm.nt.Transform) -> list[pm.MeshEdge]:
    """Check for non-manifold edges in the given mesh."""
    if not common.is_mesh(mesh_transform): return []
    mesh = mesh_transform.getShape()
    non_manifold_edges = mesh.getNonManifoldEdges()
    return non_manifold_edges

def check_n_gons(mesh_transform: pm.nt.Transform) -> list[pm.MeshFace]:
    """Check for n-gon faces in the given mesh."""
    if not common.is_mesh(mesh_transform): return []
    mesh = mesh_transform.getShape()
    n_gon_faces = []
    for face in mesh.f:
        connected_edges = face.getEdges()
        if len(connected_edges) > 4:
            n_gon_faces.append(face)
    return n_gon_faces

def check_zero_area_faces(mesh: pm.nt.Mesh, threshold=0.0001) -> list[pm.MeshFace]:
    """Check for faces with zero or near-zero area in the given mesh."""
    zero_area_faces = []
    for face in mesh.f:
        area = face.getArea()
        if area < threshold:
            zero_area_faces.append(face)
    return zero_area_faces

def get_render_shape(mesh_transform: pm.nt.Transform) -> pm.nt.Shape:
    """Get the render shape of a mesh transform, which is the shape that is visible in the viewport and renders."""
    shapes = mesh_transform.getShapes()
    for shape in shapes:
        if not shape.intermediateObject.get():
            return shape
    return None

# Intermediate Shape Functions
def get_intermediate_shapes(mesh_transform: pm.nt.Transform) -> list[pm.nt.Shape]:
    """Get all intermediate shapes from the given mesh."""
    shapes = mesh_transform.getShapes()
    intermediate_shapes = [shape for shape in shapes if shape.intermediateObject.get()]
    return intermediate_shapes

def delete_intermediate_shapes(mesh_transform: pm.nt.Transform):
    """Delete all intermediate shapes from the given mesh."""
    intermediate_shapes = get_intermediate_shapes(mesh_transform)
    pm.delete(intermediate_shapes)

def has_intermediate_shapes(mesh_transform: pm.nt.Transform) -> bool:
    """Check if the given mesh has intermediate shapes."""
    intermediate_shapes = get_intermediate_shapes(mesh_transform)
    return len(intermediate_shapes) > 0

################################################################################################################
def get_all_deformer_nodes(transform_node: pm.nt.Transform) -> list:
    deformers = pm.listHistory(transform_node, type="deformer")
    return deformers or []


# SkinCluster Utility Functions
def get_skin_cluster_nodes(mesh: pm.nt.Mesh) -> list[pm.nt.SkinCluster]:
    """Get skin cluster nodes from surface or geometry or any node with a skin cluster in its history."""
    skin_clusters = pm.listConnections(mesh, type="skinCluster")
    return skin_clusters or []

def get_skin_cluster_influences(skin_cluster_node: pm.nt.SkinCluster) -> list[pm.nt.Transform]:
    """Get joints that are binded into the given skin cluster."""
    influences = skin_cluster_node.getInfluence()
    return influences or []

def rename_skin_cluster(skin_cluster_node: pm.nt.SkinCluster):
    """Rename the skin cluster node to match the geometry name."""
    geometry = skin_cluster_node.getGeometry()[0]
    new_name = f"{geometry.name()}_skinCluster"
    pm.rename(skin_cluster_node, new_name)

def bind_skin_cluster(joints: list[pm.nt.Joint], geometry: pm.nt.Mesh) -> pm.nt.SkinCluster:
    """Bind a skin cluster to the geometry with the given joints as influences."""
    skin_cluster = pm.skinCluster(joints, geometry, toSelectedBones=True, 
                                                    bindMethod=0,       # 0 = Closest Distance
                                                    skinMethod=0,       # 0 = Classic Linear
                                                    normalizeWeights=1, # 1 = Interactive
                                                    maximumInfluences=5, 
                                                    obeyMaxInfluences=True,
                                                    dropoffRate=4.0)[0]
    rename_skin_cluster(skin_cluster)
    return skin_cluster

def add_influences_to_skin_cluster(skin_cluster: pm.nt.SkinCluster, influences: list[pm.nt.Joint]):
    """Add influences to a skin cluster if they are not already in it."""
    current_influences = skin_cluster.getInfluence()
    for jnt in influences:
        if jnt in current_influences:
            continue
        skin_cluster.addInfluence(jnt, weight=0.0)

def copy_skin_weights(source_mesh: pm.nt.Mesh, target_mesh: pm.nt.Mesh, is_add_weights=True):
    """Copy skin weights from a source mesh to a target mesh. 
       If the target mesh doesn't have a skin cluster, it will be created.
       
    Args:        
        source_mesh: Mesh to copy the skin weights from.
        target_mesh: Mesh to copy the skin weights to.
        is_add_weights: Whether to add the source influences. Defaults to True.
    """
    source_skin_cluster = get_skin_cluster_nodes(source_mesh)
    if not source_skin_cluster: raise ValueError(f"{source_mesh.name()} has no skinCluster.")

    source_influences = get_skin_cluster_influences(source_skin_cluster[0])
    target_skin_cluster = get_skin_cluster_nodes(target_mesh)
    if not target_skin_cluster:
        target_skin_cluster= bind_skin_cluster(joints=source_influences, geometry=target_mesh)
    if is_add_weights:
        add_influences_to_skin_cluster(skin_cluster=target_skin_cluster[0], influences=source_influences)

    pm.copySkinWeights(ss=source_mesh, 
                       ds=target_mesh, 
                       noMirror=True, 
                       surfaceAssociation='closestPoint', 
                       influenceAssociation='oneToOne')

# BlendShape Utility Functions
def get_blend_shape_nodes(transform: pm.nt.Transform) -> list[pm.nt.BlendShape]:
    """Get blend shape nodes from surface or geometry."""
    shape = mesh_lib.get_render_shape(transform)
    blend_shapes = filter(lambda x: isinstance(x, pm.nt.BlendShape), shape.listHistory())
    return list(blend_shapes) or []

def get_blend_shape_targets(blend_shape_node: pm.nt.BlendShape) -> list[pm.nt.Transform]:
    """Get blend shape target nodes from a blend shape node."""
    target_aliases = blend_shape_node.inputTarget.inputs()
    return target_aliases or []

def add_blend_shape_target(blend_shape_node: pm.nt.BlendShape, target_mesh: pm.nt.Mesh, target_name: str):
    """Add a blend shape target to a blend shape node."""
    blend_shape_node.addTarget( targetMesh=target_mesh, weight=1.0, name=target_name)

def rename_blend_shape_node(blend_shape_node: pm.nt.BlendShape):
    """Rename the blend shape node to match the geometry name."""
    geometry = blend_shape_node.getGeometry()[0]
    new_name = f"{geometry.name()}_blendShape"
    pm.rename(blend_shape_node, new_name)

def rename_blend_shape_target(blend_shape_node: pm.nt.BlendShape, old_name: str, new_name: str):
    """Rename a blend shape target in a blend shape node."""
    index = blend_shape_node.getTargetIndex(old_name)
    if index != -1:
        blend_shape_node.setTargetAlias(index, new_name)

def extract_blend_shape_delta(deformed_mesh: pm.nt.Transform, corrected_mesh: pm.nt.Transform, delete_delta=False) -> pm.nt.Transform:
    """
    Creates a delta between a deformed mesh and it's corrected version, then adds it to a blend shape node in the original mesh.
    Args:
        deformed_mesh: Mesh deformed, might or not have skinning.
        corrected_mesh: Mesh sculpted with the corrected shape.
    Returns:

    """
    if not common.is_mesh(deformed_mesh):  raise TypeError (f"Geometry {deformed_mesh} is not mesh.")
    if not common.is_mesh(corrected_mesh): raise TypeError (f"Geometry {corrected_mesh} is not mesh.")

    delta_mesh = pm.PyNode(pm.invertShape(deformed_mesh, corrected_mesh))
    delta_mesh.rename("{}_corrective".format(corrected_mesh))
    add_blend_shape_target(deformed_mesh, delta_mesh)
    pm.parent(delta_mesh, w=True)

    if delete_delta: 
        pm.delete(delta_mesh)
        return None
    
    return delta_mesh