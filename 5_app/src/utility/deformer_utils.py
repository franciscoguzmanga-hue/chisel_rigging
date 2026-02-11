'''
Content: Function collection to get and manipulate SkinCluster and Blendshapes.
Dependency: pymel.core, src.utility.inspect_utils
Maya Version tested: 2024

Author: Francisco Guzmán
Email: francisco.guzmanga@gmail.com

How to:
    - Use: Import the module and call the functions as needed.
    - Extend: Add more deformer-related utility functions as needed.
    - Test: Use pymel.core to get mesh and transform nodes and test the functions interactively in Maya.

TODO: if this module gets too big, split skinCluster and blendshape functions into separate modules.
'''


import pymel.core as pm

from src.utility.inspect_utils import is_mesh


def get_all_deformer_nodes(transform_node: pm.nt.Transform) -> list:
    deformers = pm.listHistory(transform_node, type="deformer")
    return deformers or []


# SkinCluster Utility Functions
def get_skin_cluster_nodes(mesh: pm.nt.Transform) -> list[pm.nt.SkinCluster]:
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
    blend_shapes = pm.listConnections(transform, type="blendShape")
    return blend_shapes or []

def get_blend_shape_targets(blend_shape_node: pm.nt.BlendShape) -> list[pm.nt.Transform]:
    """Get blend shape target nodes from a blend shape node."""
    target_aliases = blend_shape_node.getTargetAliasList()
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
        deformed_mesh (pm.nt.Transform): Mesh deformed, might or not have skinning.
        corrected_mesh (pm.nt.Transform): Mesh sculpted with the corrected shape.
    Returns:

    """
    if not is_mesh(deformed_mesh):  raise TypeError (f"Geometry {deformed_mesh} is not mesh.")
    if not is_mesh(corrected_mesh): raise TypeError (f"Geometry {corrected_mesh} is not mesh.")

    delta_mesh = pm.PyNode(pm.invertShape(deformed_mesh, corrected_mesh))
    delta_mesh.rename("{}_corrective".format(corrected_mesh))
    add_blend_shape_target(deformed_mesh, delta_mesh)
    pm.parent(delta_mesh, w=True)

    if delete_delta: 
        pm.delete(delta_mesh)
        return None
    
    return delta_mesh