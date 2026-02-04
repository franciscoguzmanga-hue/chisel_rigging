import pymel.core as pm

from src.utility.inspect_utils import is_mesh


def get_all_deformer_nodes(transform_node: pm.nt.Transform) -> list:
    deformers = pm.listHistory(transform_node, type="deformer")
    return deformers or []


# SkinCluster Utility Functions
def get_skinCluster_nodes(mesh: pm.nt.Deformer) -> list:
    skin_clusters = pm.listConnections(mesh, type="skinCluster")
    return skin_clusters or []

def get_skinCluster_influences(skin_cluster_node: pm.nt.SkinCluster) -> list:
    influences = skin_cluster_node.getInfluence()
    return influences or []

def rename_skinCluster(skin_cluster_node: pm.nt.SkinCluster) -> None:
    geometry = skin_cluster_node.getGeometry()[0]
    new_name = f"{geometry.name()}_skinCluster"
    pm.rename(skin_cluster_node, new_name)

def bind_skinCluster(joints: list,
                     geometry: pm.nt.Mesh) -> pm.nt.SkinCluster:
    skin_cluster = pm.skinCluster(joints, geometry, toSelectedBones=True, 
                                                    bindMethod=0,       # 0 = Closest Distance
                                                    skinMethod=0,       # 0 = Classic Linear
                                                    normalizeWeights=1, # 1 = Interactive
                                                    maximumInfluences=5, 
                                                    obeyMaxInfluences=True,
                                                    dropoffRate=4.0)[0]
    rename_skinCluster(skin_cluster)
    return skin_cluster

def add_influences_to_skinCluster(skinCluster: pm.nt.SkinCluster, influences: list) -> None:
    current_influences = skinCluster.getInfluence()
    for jnt in influences:
        if jnt in current_influences:
            continue
        skinCluster.addInfluence(jnt, weight=0.0)

def copy_skin_weights(source_mesh: pm.nt.Mesh, target_mesh: pm.nt.Mesh, is_add_weights=True) -> None:
    source_skinCluster = get_skinCluster_nodes(source_mesh)
    if not source_skinCluster: raise ValueError(f"{source_mesh.name()} has no skinCluster.")

    source_influences = get_skinCluster_influences(source_skinCluster[0])
    target_skinCluster = get_skinCluster_nodes(target_mesh)
    if not target_skinCluster:
        target_skinCluster= bind_skinCluster(joints=source_influences, geometry=target_mesh)
    if is_add_weights:
        add_influences_to_skinCluster(skinCluster=target_skinCluster[0], influences=source_influences)
    

    source_skinCluster.envelope.set(0)
    target_skinCluster.envelope.set(0)
    pm.copySkinWeights(ss=source_mesh, ds=target_mesh, noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='oneToOne')
    source_skinCluster.envelope.set(1)
    target_skinCluster.envelope.set(1)


# BlendShape Utility Functions
def get_blendShape_nodes(deformer_node: pm.nt.Deformer) -> list:
    blend_shapes = pm.listConnections(deformer_node, type="blendShape")
    return blend_shapes or []

def get_blendshape_targets(blend_shape_node: pm.nt.BlendShape) -> list:
    target_aliases = blend_shape_node.getTargetAliasList()
    return target_aliases or []

def add_blendshape_target(blend_shape_node: pm.nt.BlendShape, target_mesh: pm.nt.Mesh, target_name: str) -> None:
    blend_shape_node.addTarget( targetMesh=target_mesh, weight=1.0, name=target_name)

def rename_blendShape_node(blend_shape_node: pm.nt.BlendShape) -> None:
    geometry = blend_shape_node.getGeometry()[0]
    new_name = f"{geometry.name()}_blendShape"
    pm.rename(blend_shape_node, new_name)

def rename_blendshape_target(blend_shape_node: pm.nt.BlendShape, old_name: str, new_name: str) -> None:
    index = blend_shape_node.getTargetIndex(old_name)
    if index != -1:
        blend_shape_node.setTargetAlias(index, new_name)

def extract_blendshape_delta(deformed_mesh: pm.nt.Transform, corrected_mesh: pm.nt.Transform, delete_delta=False) -> pm.nt.Transform:
    """
    Creates a delta between a deformed mesh and it's corrected version, to later add it to a blendshape in the original mesh.
    Args:
        deformed: nt.Transform, mesh deformed, might or not have skinning.
        corrected: nt.Transform, mesh sculpted with the corrected shape.

    Returns:

    """
    if not is_mesh(deformed_mesh):  raise TypeError (f"Geometry {deformed_mesh} is not mesh.")
    if not is_mesh(corrected_mesh): raise TypeError (f"Geometry {corrected_mesh} is not mesh.")

    delta_mesh = pm.PyNode(pm.invertShape(deformed_mesh, corrected_mesh))
    delta_mesh.rename("{}_corrective".format(corrected_mesh))
    add_blendshape_target(deformed_mesh, delta_mesh)
    pm.parent(delta_mesh, w=True)

    if delete_delta: 
        pm.delete(delta_mesh)
        return None
    
    return delta_mesh

