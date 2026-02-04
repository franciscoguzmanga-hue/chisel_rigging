import pymel.core as pm

from src.utility.deformer_utils import get_skinCluster_nodes, get_skinCluster_influences, get_all_deformer_nodes
from src.utility.inspect_utils import is_constraint, is_transform
from src.utility.constraint_utils import get_constraint_nodes, get_constraint_target

def get_inputs_from_attribute(node: pm.PyNode) -> list[pm.PyNode]:
    pass

def get_outputs_from_attribute(node: pm.PyNode) -> list[pm.PyNode]:
    pass

def get_deformers_from_node(node: pm.PyNode) -> list[pm.PyNode]:
    all_deformers = []
    for transform in transforms:
        deformers = get_all_deformer_nodes(transform_node=transform)
        all_deformers.extend(deformers)
    return all_deformers


# Blendshape functions
def get_all_blendshape_nodes(transforms: list[pm.nt.Transform]) -> list[pm.nt.BlendShape]:
    pass

def get_all_blenshape_targets(transforms: list[pm.nt.Transform]) -> list[pm.nt.Transform]:
    pass

# Skin Cluster functions
def get_all_skinCluster_nodes(transforms: list[pm.nt.Transform]) -> list[pm.nt.SkinCluster]:
    skin_nodes = []
    for transform in transforms:
        skin_node = get_skinCluster_nodes(mesh=transform)
        skin_nodes.extend(skin_node)
    return skin_nodes

def get_all_influences(transforms: list[pm.nt.Transform]) -> list[pm.nt.Joint]:
    influences = []

    skin_cluster_nodes = get_all_skinCluster_nodes(*transforms)

    for skin_cluster in skin_cluster_nodes:
        node_influences = get_skinCluster_influences(skin_cluster_node=skin_cluster)
        influences.extend(node_influences)
    return influences


# Constraint functions
def get_all_constraint_nodes(nodes: list[pm.PyNode]) -> list[pm.nt.Constraint]:
    constraint_nodes = []
    for node in nodes:
        if is_constraint(node):
            constraint_nodes.append(node)
        else:
            constraints = get_constraint_nodes(node)
            constraint_nodes.extend(constraints)
    return constraint_nodes

def get_all_constraint_targets(nodes: list[pm.PyNode]) -> list[pm.nt.Transform]:
    constraint_targets = []
    for node in nodes:
        if is_constraint(node):
            targets = get_constraint_target(node)
            constraint_targets.extend(targets)
        if is_transform(node):
            constraints = get_all_constraint_nodes(node)
            targets = get_all_constraint_targets(*constraints)
            constraint_targets.extend(targets)
        else:
            continue


