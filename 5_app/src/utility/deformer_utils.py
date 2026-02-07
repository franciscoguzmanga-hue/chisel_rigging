'''
################################################################################################################
Author: Francisco Guzmán

Content: Function collection to get and manipulate SkinCluster and Blendshapes.
Dependency: pymel.core, src.utility.inspect_utils
Maya Version tested: 2024

How to:
    - Use: Import the module and call the functions as needed.
    - Extend: Add more deformer-related utility functions as needed.
    - Test: Use pymel.core to get mesh and transform nodes and test the functions interactively in Maya.

TODO: if this module gets too big, split skinCluster and blendshape functions into separate modules.
################################################################################################################
'''


import pymel.core as pm

from src.utility.inspect_utils import is_mesh


def get_all_deformer_nodes(transform_node: pm.nt.Transform) -> list:
    deformers = pm.listHistory(transform_node, type="deformer")
    return deformers or []


# SkinCluster Utility Functions
def getSkinCluster(*selection):
    cluster = {}
    for obj in selection:
        node = pm.ls(pm.listHistory(obj), type="skinCluster")
        if node: cluster[obj] = node[0]
    return cluster

def getSkinnedJoints(*selection):
    joints = []
    for obj in selection:
        sknCluster = getSkinCluster(obj)
        if not sknCluster: continue
        influences = pm.skinCluster(sknCluster[obj], q=True, inf=True)
        [ joints.append(jnt) for jnt in influences if jnt not in joints ]
    return joints

def renameSkincluster(*selection):
    """
    Args:
        *selection: list of skinned meshes.
    Returns: list of given meshes.
    """
    for obj in selection:
        if isinstance(obj, nt.SkinCluster):
            skn = obj
            geometry = skn.getGeometry()[0].getParent().name()
        else:
            skn = getSkinCluster(obj)[obj]
            geometry = obj.name()
        pm.rename(skn, "{}_skinCluster".format(geometry))

def bind_skinCluster(joints: list[pm.nt.Transform],
                     geometry: pm.nt.Mesh) -> pm.nt.SkinCluster:
    """Bind a skin cluster to the geometry with the given joints as influences.

        Args:
        joints (list[pm.nt.Transform]): List of joints to bind to the skin cluster.
        geometry (pm.nt.Mesh): Geometry to bind the skin cluster to.
    
    Returns:
        pm.nt.SkinCluster: The skin cluster node created.
    """
    skin_cluster = pm.skinCluster(joints, geometry, toSelectedBones=True, 
                                                    bindMethod=0,       # 0 = Closest Distance
                                                    skinMethod=0,       # 0 = Classic Linear
                                                    normalizeWeights=1, # 1 = Interactive
                                                    maximumInfluences=5, 
                                                    obeyMaxInfluences=True,
                                                    dropoffRate=4.0)[0]
    rename_skinCluster(skin_cluster)
    return skin_cluster

def add_influences_to_skinCluster(skinCluster: pm.nt.SkinCluster, influences: list[pm.nt.Transform]) -> None:
    """Add influences to a skin cluster if they are not already in it.
    
    Args:
        skinCluster (pm.nt.SkinCluster): Skin cluster to add the influences to.
        influences (list[pm.nt.Transform]): List of joints to add as influences.
    """
    current_influences = skinCluster.getInfluence()
    for jnt in influences:
        if jnt in current_influences:
            continue
        skinCluster.addInfluence(jnt, weight=0.0)

def copy_skin_weights(source_mesh: pm.nt.Mesh, target_mesh: pm.nt.Mesh, is_add_weights=True) -> None:
    """Copy skin weights from a source mesh to a target mesh. If the target mesh doesn't have a skin cluster, it will be created with the same influences as the source mesh.
       
    Args:        
        source_mesh (pm.nt.Mesh): Mesh to copy the skin weights from.
        target_mesh (pm.nt.Mesh): Mesh to copy the skin weights to.
        is_add_weights (bool, optional): Whether to add the source influences to the target skin cluster if it already exists. Defaults to True.
    """
    source_skinCluster = get_skinCluster_nodes(source_mesh)
    if not source_skinCluster: raise ValueError(f"{source_mesh.name()} has no skinCluster.")

    source_influences = get_skinCluster_influences(source_skinCluster[0])
    target_skinCluster = get_skinCluster_nodes(target_mesh)
    if not target_skinCluster:
        target_skinCluster= bind_skinCluster(joints=source_influences, geometry=target_mesh)
    if is_add_weights:
        add_influences_to_skinCluster(skinCluster=target_skinCluster[0], influences=source_influences)

    pm.copySkinWeights(ss=source_mesh, ds=target_mesh, noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='oneToOne')

# BlendShape Utility Functions
def getBlendshape(*selection):
    BS = {}
    for obj in selection:
        node = pm.ls(pm.listHistory(obj), type="blendShape")
        if node: BS[obj] = node[0]
    return BS

def getBlendshapeTargets(*selection):
    """
        Args:
            *selection: list of basemeshes.
    """
    targets = []
    for obj in selection:
        bs_node = getBlendshape(obj)[obj]
        weight_list = list(bs_node.weight)

        for target in bs_node.weight:
            try:
                index = weight_list.index(target)

                str = "{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem".format(bs_node, index)
                target_mesh = pm.listConnections(str)
                targets.append(target_mesh)
            except Exception as ex:
                message(ex, "info")
    return targets

def add_blendshape_target(blend_shape_node: pm.nt.BlendShape, target_mesh: pm.nt.Mesh, target_name: str) -> None:
    """Add a blendshape target to a blendshape node.
    Args:
        blend_shape_node (pm.nt.BlendShape): Blendshape node to add the target to.
        target_mesh (pm.nt.Mesh): Mesh to add as a blendshape target.
        target_name (str): Name of the blendshape target.
    """
    blend_shape_node.addTarget( targetMesh=target_mesh, weight=1.0, name=target_name)

def rename_blendShape_node(blend_shape_node: pm.nt.BlendShape) -> None:
    """Rename the blendshape node to match the geometry name.
    Args:
        blend_shape_node (pm.nt.BlendShape): Blendshape node to rename.
    """
    geometry = blend_shape_node.getGeometry()[0]
    new_name = f"{geometry.name()}_blendShape"
    pm.rename(blend_shape_node, new_name)

def renameTargets(*selection):
    """
    Args:
        *selection: list of basemeshes.
    """
    for obj in selection:
        bs_node = getBlendshape(obj)[obj]
        weight_list = list(bs_node.weight)

        for target in bs_node.weight:
            try:
                index = weight_list.index(target)

                str = "{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem".format(bs_node, index)
                target_mesh = pm.listConnections(str)
                if target_mesh:
                    pm.aliasAttr(target_mesh[0], target)
            except Exception as ex:
                message(ex, "info")

def extract_blendshape_delta(deformed_mesh: pm.nt.Transform, corrected_mesh: pm.nt.Transform, delete_delta=False) -> pm.nt.Transform:
    """
    Creates a delta between a deformed mesh and it's corrected version, to later add it to a blendshape in the original mesh.
    Args:
        deformed_mesh (pm.nt.Transform): Mesh deformed, might or not have skinning.
        corrected_mesh (pm.nt.Transform): Mesh sculpted with the corrected shape.
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

