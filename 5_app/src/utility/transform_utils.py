import pymel.core as pm

from src.utility.math_utils import get_distance


# Transform Manipulation Functions
def flip_transform(transform_node: pm.nt.Transform, axis="x", replace_str=("_L", "_R"), use_scale=True) -> None:
    
    flip_axis = {"x": [-1,  1,  1],
                 "y": [ 1, -1,  1],
                 "z": [ 1,  1, -1]}
    if use_scale:
        pivot_node = pm.nt.Transform(n="pivot_temp")
        pm.parent(transform_node, pivot_node)
        pivot_node.setScale(flip_axis[axis])
        pm.parent(transform_node, world=True)
        pm.delete(pivot_node)
    else:
        original_pos = transform_node.getTranslation(ws=True)
        new_pos = original_pos * flip_axis[axis]
        transform_node.setTranslation(new_pos, ws=True)

def mirror_transform(transform_node: pm.nt.Transform, axis="x", replace_str=("_L", "_R"), use_scale=True) -> pm.nt.Transform:
    duplicated_transform = pm.duplicate(transform_node)[0]
    flip_transform(transform_node=duplicated_transform, axis=axis, use_scale=use_scale)
    
    # update name of mirrored object.
    transform_name = transform_node.name()
    new_name = transform_name.replace(replace_str[0], replace_str[1])
    pm.rename(duplicated_transform, new_name)
    return duplicated_transform

def align_transform(master_transform: pm.nt.Transform, slave_transform: pm.nt.Transform, position=True, rotation=True, scale=False) -> None:
    if position:
        constraint = pm.pointConstraint(master_transform, slave_transform)
        pm.delete(constraint)
    if rotation:
        constraint = pm.orientConstraint(master_transform, slave_transform)
        pm.delete(constraint)
    if scale:
        constraint = pm.scaleConstraint(master_transform, slave_transform)
        pm.delete(constraint)

def freeze_transform(transform_node: pm.nt.Transform, position=True, rotation=True, scale=True) -> None:
    pm.makeIdentity(transform_node, apply=True, t=position, r=rotation, s=scale, n=False)

def reset_transform(transform_node: pm.nt.Transform, position=True, rotation=True, scale=True) -> None:
    if position:
        transform_node.setTranslation((0,0,0), ws=True)
    if rotation:
        transform_node.setRotation((0,0,0), ws=True)
    if scale:
        transform_node.setScale((1,1,1))

"""def fix_double_transform(transform_node: pm.nt.Transform) -> None:
    decompose_matrix_node = pm.nt.DecomposeMatrix(n=f"{transform_node.name()}_fixDoubleTransform_decomposeMatrix")
    transform_node.worldInverseMatrix >> decompose_matrix_node.inputMatrix
    decompose_matrix_node.outputTranslate >> transform_node.getParent().translate
    decompose_matrix_node.outputRotate >> transform_node.getParent().rotate
    decompose_matrix_node.outputScale >> transform_node.getParent().scale"""

# Transform getter functions
def get_side_of_transform(transform_node: pm.nt.Transform, axis="x") -> int:
    pos = pm.xform(transform_node, q=True, ws=True, t=True)
    axis_index = {"x": 0, "y": 1, "z": 2}
    coord = pos[axis_index[axis]]
    if coord > 0:
        return 1
    elif coord < 0:
        return -1
    else:
        return 0
    
def get_closest_transform(reference_transform: pm.nt.Transform, transform_list: list) -> pm.nt.Transform:
    ref_pos = pm.xform(reference_transform, q=True, ws=True, t=True)
    closest_transform = None
    min_distance = float('inf')
    
    for transform in transform_list:
        target_pos = pm.xform(transform, q=True, ws=True, t=True)
        distance = get_distance(ref_pos, target_pos)
        if distance < min_distance:
            closest_transform = transform
    return closest_transform

# Offset functions
def create_offset(transform_node: pm.nt.Transform, offset_name_suffix="_offset") -> pm.nt.Transform:
    offset_transform = pm.nt.Transform(n=f"{transform_node.name()}{offset_name_suffix}")
    offset_transform.setMatrix(transform_node.getMatrix(worldSpace=True), worldSpace=True)
    pm.parent(offset_transform, transform_node.getParent())
    pm.parent(transform_node, offset_transform)
    return offset_transform

def center_offset(transform_node: pm.nt.Transform) -> None:
    offset_transform = transform_node.getParent()
    if not offset_transform:
        pm.warning(f"{transform_node.name()} has no parent offset to center.")
        return
    
    original_matrix = transform_node.getMatrix(worldSpace=True)
    offset_transform.setMatrix(original_matrix, worldSpace=True)
    transform_node.setMatrix(original_matrix, worldSpace=True)


# Pivot functions
def bake_pivot(transform_node: pm.nt.Transform) -> None:
    selection = pm.selected()
    pm.select(transform_node)
    pm.mel.eval("BakeCustomPivot;")
    pm.select(selection)

def set_center_pivot(transform_node: pm.nt.Transform) -> None:
    center_point = get_center_pivot(transform_node)
    pm.xform(transform_node, piv=center_point, ws=True)

def get_center_pivot(transform_node: pm.nt.Transform) -> pm.datatypes.Vector:
    bbox = transform_node.getBoundingBox(space='world')
    center_point = bbox.center()
    return center_point


# Axis visibility funcions
def show_axis(transform_node: pm.nt.Transform) -> None:
    transform_node.displayLocalAxis.set(1)

def hide_axis(transform_node: pm.nt.Transform) -> None:
    transform_node.displayLocalAxis.set(0)
    
def has_visible_axis(transform_node: pm.nt.Transform) -> bool:
    return transform_node.displayLocalAxis.get()


# Hierarchy Functions
def build_hierarchy_from_list(transform_list: list) -> pm.nt.Transform:
    for i in range(1, len(transform_list)):
        pm.parent(transform_list[i], transform_list[i-1])
    return transform_list[0]

def is_ancestor(ancestor_transform: pm.nt.Transform, descendant_transform: pm.nt.Transform) -> bool:
    ancestors = descendant_transform.getAllParents()
    return ancestor_transform in ancestors

def has_children(transform_node: pm.nt.Transform) -> bool:
    children = transform_node.getChildren(type=pm.nt.Transform)
    return len(children) > 0


# Display Functions
def set_display_normal(transform_node: pm.nt.Transform) -> None:
    transform_node.overrideEnabled.set(0)  # Disable override to show normal display    

def set_display_template(transform_node: pm.nt.Transform) -> None:
    transform_node.overrideEnabled.set(1)
    transform_node.overrideDisplayType.set(1)  # 1 for template mode

def set_display_reference(transform_node: pm.nt.Transform) -> None:
    transform_node.overrideEnabled.set(1)
    transform_node.overrideDisplayType.set(2)  # 2 for reference mode   


# Locking Functions
def lock_node(node: pm.PyNode) -> None:
    node.setLocked(True)

def unlock_node(node: pm.PyNode) -> None:
    node.setLocked(False)



