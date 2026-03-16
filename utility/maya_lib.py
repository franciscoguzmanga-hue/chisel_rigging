'''
Content: Collection of functions to work with Maya nodes.
Dependency: pymel.core, Enum, common
Maya Version tested: 2024

Author: Francisco Guzmán
email: francisco.guzmanga@gmail.com
'''


from enum import Enum
import pymel.core as pm
import chisel_rigging.utility.common as common
import chisel_rigging.utility.mesh_lib as mesh_lib

class Vector(Enum):
    X_POS = (1, 0, 0)
    X_NEG = (-1, 0, 0)
    Y_POS = (0, 1, 0)
    Y_NEG = (0, -1, 0)
    Z_POS = (0, 0, 1)
    Z_NEG = (0, 0, -1)

####################################################################################################################################
# Attribute Manipulation Functions  ################################################################################################
####################################################################################################################################
def connect_attributes(master: pm.nt.Transform, slave: pm.nt.Transform, attributes=("t", "r", "s", "v")):
    """Connect related attributes between two transforms.

    Args:
        master: The driving transform node.
        slave: The driven transform node.
        attributes: Attributes to connect. Defaults to ("t", "r", "s", "v").
    """
    for attr in attributes:
        if slave.hasAttr(attr) and master.hasAttr(attr):
            master.attr(attr) >> slave.attr(attr)

def connect_all_keyable_attributes(master: pm.nt.Transform, slave: pm.nt.Transform):
    """Connect all keyable and related attributes between two transform nodes.

    Args:
        master: The driving transform node.
        slave: The driven transform node.
    """
    master_keyable_attributes = [attr.shortName() for attr in master.listAttr(keyable=True) if attr.isSettable()]
    connect_attributes(master=master, slave=slave, attributes=master_keyable_attributes)

def get_selected_attributes(transform_node: pm.nt.Transform) -> list[pm.Attribute]:
    """Get a list of the selected attributes in the channelbox.

    Args:
        transform_node: The transform node to check for the selected attributes.

    Returns:
        list: List of the selected attributes.
    """
    selected_attrs = pm.channelBox("mainChannelBox", q=True, sma=True) or []
    attributes = []
    for attribute in selected_attrs:
        if transform_node.hasAttr(attribute):
            attributes.append(transform_node.attr(attribute))
    return attributes

def update_attribute_default(attribute: pm.Attribute):
    """Update the default value of an attribute to its current value.

    Args:
        attribute: The attribute to update.
    """
    current_value = attribute.get()
    pm.addAttr(attribute, edit=True, defaultValue=current_value)

def lock_attribute(attribute: pm.Attribute):
    attribute.set(lock=True)

def lock_and_hide_attribute(attribute: pm.Attribute):
    """Lock and hide the given attribute from the channelBox.

    Args:
        attribute: The attribute to lock and hide.
    """
    pm.setAttr(attribute, e=True, lock=True, keyable=False, channelBox=False)
    #attribute.set(lock=True)
    #attribute.setKeyable(False)
    #attribute.showInChannelBox(False)

def unlock_attribute(attribute: pm.Attribute):
    """Unlock and set it visible in the channel box.

    Args:
        attribute: The attribute to unlock and show.
    """
    attribute.set(lock=False)
    attribute.setKeyable(True)
    attribute.showInChannelBox(True)

def set_non_keyable(attribute: pm.Attribute):
    attribute.set(keyable=False)

def set_keyable(attribute: pm.Attribute):
    attribute.set(keyable=True)

def create_proxy_attribute(source_attribute: pm.Attribute, target_node: pm.nt.Transform):
    """Create an attribute from a source and keep it related, similar to an instance.
       Helps to have an attribute accessible from different transform nodes and simplify animation.

    Args:
        source_attribute: Source attribute to proxy.
        target_node: Target node to create the proxy attribute in.
    """
    proxy_attr_name = source_attribute.longName()
    if not target_node.hasAttr(proxy_attr_name):
        pm.addAttr(target_node, ln=proxy_attr_name, k=True, proxy=source_attribute)

def reset_attribute(attribute: pm.Attribute):
    """Reset the attribute to its default value if it is keyable, settable, and not locked.

    Args:
        attribute: The attribute to reset.
    """
    if attribute.isKeyable() and attribute.isSettable() and not attribute.isLocked():
        default_value = attribute.getDefault()
        attribute.set(default_value)

def connect_or_assign_value(value, target_attribute: pm.Attribute):
    """If the parameter value is not pm.Attribute, assign the value to target_attribute.
       If the parameter value is pm.Attribute, connects it to target_attribute.

    Args:
        value (int, float, list, pm.Attribute): The value to connect or assign.
        target_attribute: The attribute to connect or assign the value to.
    """
    is_source_attr = isinstance(value, pm.Attribute)
    is_source_vector = (is_source_attr and value.type() == "double3") or isinstance(value, (pm.dt.Vector, list))

    is_target_vector = target_attribute.type() == "double3" or target_attribute.type() == "float3"

    current_target = target_attribute
    if is_target_vector and not is_source_vector:
        current_target = target_attribute.getChildren()[0]

    if is_source_attr:
        value >> current_target
    else:
        current_target.set(value)

def get_input_nodes(transform_node: pm.nt.Transform) -> list[pm.PyNode]:
    connections = transform_node.inputs(source=True, destination=False)
    return connections

def get_output_nodes(transform_node: pm.nt.Transform) -> list[pm.PyNode]:
    connections = transform_node.outputs(source=False, destination=True)
    return connections


####################################################################################################################################
# Constraint Utility Functions #####################################################################################################
####################################################################################################################################

class WorldUpType(Enum):
    SCENE   = "scene"
    OBJECT  = "object"
    OBJECT_ROTATE_AXIS = "objectrotation"
    VECTOR  = "vector"
    NONE    = "none"


def get_constraint_nodes(transform_node: pm.nt.Transform) -> list[pm.nt.Constraint]:
    constraints = pm.listRelatives(transform_node, type="constraint")
    return constraints

def get_constraint_target(constraint_node: pm.nt.Constraint) -> list[pm.PyNode]:
    return constraint_node.getTargetList()

def parent_constraint_one_to_many(master: pm.nt.Transform, *slaves: pm.nt.Transform, maintain_offset=True) -> list[pm.nt.ParentConstraint]:
    constraints = []
    for slave in slaves:
        constraint = pm.parentConstraint(master, slave, mo=maintain_offset)
        constraints.append(constraint)
    return constraints

def parent_constraint_many_to_one(*masters: pm.nt.Transform, slave: pm.nt.Transform, maintain_offset=True) -> pm.nt.ParentConstraint:
    constraint = pm.parentConstraint(masters, slave, mo=maintain_offset)
    return constraint

def scale_constraint_one_to_many(master: pm.nt.Transform, *slaves: pm.nt.Transform, maintain_offset=True) -> list[pm.nt.ScaleConstraint]:
    constraints = []
    for slave in slaves:
        constraint = pm.scaleConstraint(master, slave, mo=maintain_offset)
        constraints.append(constraint)
    return constraints

def scale_constraint_many_to_one(*masters: pm.nt.Transform, slave: pm.nt.Transform, maintain_offset=True) -> pm.nt.ScaleConstraint:
    constraint = pm.scaleConstraint(masters, slave, mo=maintain_offset)
    return constraint

def orient_constraint_one_to_many(master: pm.nt.Transform, *slaves: pm.nt.Transform, maintain_offset=True) -> list[pm.nt.OrientConstraint]:
    constraints = []
    for slave in slaves:
        constraint = pm.orientConstraint(master, slave, mo=maintain_offset)
        constraints.append(constraint)
    return constraints

def orient_constraint_many_to_one(*masters: pm.nt.Transform, slave: pm.nt.Transform, maintain_offset=True) -> pm.nt.OrientConstraint:
    constraint = pm.orientConstraint(masters, slave, mo=maintain_offset)
    return constraint

def point_constraint_one_to_many(master: pm.nt.Transform, *slaves: pm.nt.Transform, maintain_offset=True) -> list[pm.nt.PointConstraint]:
    constraints = []
    for slave in slaves:
        constraint = pm.pointConstraint(master, slave, mo=maintain_offset)
        constraints.append(constraint)
    return constraints

def point_constraint_many_to_one(*masters: pm.nt.Transform, slave: pm.nt.Transform, maintain_offset=True) -> pm.nt.PointConstraint:
    constraint = pm.pointConstraint(masters, slave, mo=maintain_offset)
    return constraint

def aim_constraint_many_to_one(master: pm.nt.Transform, *slaves: pm.nt.Transform, 
                              maintain_offset=True, 
                              aim_vector=Vector.X_POS, 
                              up_vector= Vector.Y_POS, 
                              world_up_type= WorldUpType.SCENE,
                              worldUpObject: pm.nt.Transform = None,
                              worldUpVector= Vector.Z_POS) -> list[pm.nt.AimConstraint]:
    constraints = []
    for slave in slaves:
        constraint = pm.aimConstraint(master, slave, 
                                      mo=maintain_offset, 
                                      aimVector  =aim_vector.value      if isinstance(aim_vector, Vector)         else aim_vector, 
                                      upVector   =up_vector.value       if isinstance(up_vector,  Vector)         else up_vector,
                                      worldUpType=world_up_type.value   if isinstance(world_up_type, WorldUpType) else world_up_type,
                                      worldUpObject=worldUpObject if worldUpObject else None,
                                      worldUpVector=worldUpVector.value if isinstance(worldUpVector, Vector) else worldUpVector)
        constraints.append(constraint)
    return constraints


####################################################################################################################################
# Transform Manipulation Functions #################################################################################################
####################################################################################################################################

def get_or_create_transform(name:str, parent: pm.nt.Transform =None) -> pm.nt.Transform:
    """Create a group transform node with the given name or cast it if it already exists.
    Args:
        name: Name of the transform node.
        parent: Parent transform node. Defaults is None.
    """
    group_node = None
    if pm.objExists(name):
        group_node = pm.nt.Transform(name)
    else:
        group_node = pm.nt.Transform(n=name)
        if parent and pm.objExists(parent):
            pm.parent(group_node, parent)
    return group_node

def get_or_create_set(set_name: str,*members: pm.PyNode) -> pm.nt.ObjectSet:
    """ Add nodes to main rig set and creates it if it doesn't exist.

    Returns:
        pm.nt.ObjectSet: The rig set with the new members added.
    """
    rig_set = None
    if pm.objExists(set_name):
        rig_set = pm.nt.ObjectSet(set_name) 
    else:
        rig_set = pm.nt.ObjectSet(n=set_name)
    
    if members:
        [rig_set.addMember(obj) for obj in members]

    return rig_set

def flip_transform(transform_node: pm.nt.Transform, axis="x", replace_str=("_L", "_R"), use_scale=True):
    """Flip a transform node along the specified axis.
    Args:
        transform_node: Transform node to flip.
        axis: Axis to flip along. Defaults to "x".
        replace_str: Strings to replace in the name. Defaults to ("_L", "_R").
        use_scale: Whether to use scale for flipping. Defaults to True.
    """
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
    """Create a copy of transform node and flip it along the specified axis.
    Args:
        transform_node: Transform node to mirror.
        axis: Axis to mirror along. Defaults to "x".
        replace_str: Strings to replace in the name. Defaults to ("_L", "_R").
        use_scale: Whether to use scale for mirroring. Defaults to True.
    Returns:
        pm.nt.Transform: The mirrored transform node.
    """
    duplicated_transform = pm.duplicate(transform_node)[0]
    flip_transform(transform_node=duplicated_transform, axis=axis, use_scale=use_scale)
    
    # update name of mirrored object.
    transform_name = transform_node.name()
    new_name = transform_name.replace(replace_str[0], replace_str[1])
    pm.rename(duplicated_transform, new_name)
    return duplicated_transform

def align_transform(master_transform: pm.nt.Transform, slave_transform: pm.nt.Transform, 
                    use_position=True, 
                    use_rotation=True, 
                    use_scale=False) -> None:
    """Move slave transform to the exact matrix of the master transform."""
    if use_position:
        constraint = pm.pointConstraint(master_transform, slave_transform)
        pm.delete(constraint)
    if use_rotation:
        constraint = pm.orientConstraint(master_transform, slave_transform)
        pm.delete(constraint)
    if use_scale:
        constraint = pm.scaleConstraint(master_transform, slave_transform)
        pm.delete(constraint)

def freeze_transform(transform_node: pm.nt.Transform, position=True, rotation=True, scale=True):
    """Freeze the transformations of a transform node."""
    pm.makeIdentity(transform_node, apply=True, t=position, r=rotation, s=scale, n=False)

def delete_history(transform_node: pm.nt.Transform):
    pm.delete(transform_node, ch=True)

def reset_transform(transform_node: pm.nt.Transform, position=True, rotation=True, scale=True):
    if position: 
        transform_node.setTranslation((0,0,0))
    if rotation:
        transform_node.setRotation((0,0,0))
    if scale:
        transform_node.setScale((1,1,1))

def negate_transform_matrix(transform_node: pm.nt.Transform):
    # TODO: This is generating circular dependencies.
    name = f"{transform_node.name()}_negateMatrix"
    decompose_matrix_node = pm.nt.DecomposeMatrix(n=name)
    
    transform_node.worldInverseMatrix >> decompose_matrix_node.inputMatrix
    decompose_matrix_node.outputTranslate >> transform_node.getParent().translate
    decompose_matrix_node.outputRotate >> transform_node.getParent().rotate
    decompose_matrix_node.outputScale >> transform_node.getParent().scale

####################################################################################################################################
#  TRANSFORM GETTER FUNCTIONS ######################################################################################################
####################################################################################################################################
def get_side_of_transform(transform_node: pm.nt.Transform, axis="x") -> int:
    """Get the side of the transform node along the specified axis.
    Returns:
        int: 1 for positive side, -1 for negative side, 0 for center.
    """
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
    """Get the closest transform from a list to the reference transform."""
    ref_pos = pm.xform(reference_transform, q=True, ws=True, t=True)
    closest_transform = None
    min_distance = float('inf')
    
    for transform in transform_list:
        target_pos = pm.xform(transform, q=True, ws=True, t=True)
        distance = common.get_distance_between_transforms(ref_pos, target_pos)
        if distance < min_distance:
            closest_transform = transform
            min_distance = distance
    return closest_transform

####################################################################################################################################
#  OFFSET FUNCTIONS ################################################################################################################
####################################################################################################################################
def create_offset(transform_node: pm.nt.Transform, offset_name_suffix="_offset") -> pm.nt.Transform:
    """Create an offset group for the given transform node to zero out transformations."""
    name = f"{transform_node.name()}{offset_name_suffix}"
    offset_transform = pm.nt.Transform(n=name)
    pm.delete((pm.parentConstraint(transform_node, offset_transform)))
    pm.delete((pm.scaleConstraint(transform_node, offset_transform)))

    pm.parent(offset_transform, transform_node.getParent())
    pm.parent(transform_node, offset_transform)
    return offset_transform

def center_offset(transform_node: pm.nt.Transform):
    """Zero out transform node by centering it's offset."""
    offset_transform = transform_node.getParent()
    if not offset_transform:
        pm.warning(f"{transform_node.name()} has no parent offset to center.")
        return
    
    original_matrix = transform_node.getMatrix(worldSpace=True)
    offset_transform.setMatrix(original_matrix, worldSpace=True)
    transform_node.setMatrix(original_matrix, worldSpace=True)

####################################################################################################################################
#  PIVOT FUNCTIONS #################################################################################################################
####################################################################################################################################
def bake_pivot(transform_node: pm.nt.Transform):
    selection = pm.selected()
    pm.select(transform_node)
    pm.mel.eval("BakeCustomPivot;")
    pm.select(selection)

def set_center_pivot(transform_node: pm.nt.Transform):
    center_point = get_center_pivot(transform_node)
    pm.xform(transform_node, piv=center_point, ws=True)

def get_center_pivot(transform_node: pm.nt.Transform) -> pm.datatypes.Vector:
    """Get the center pivot point of the given transform node."""
    bbox = transform_node.getBoundingBox(space='world')
    center_point = bbox.center()
    return center_point

####################################################################################################################################
#  VISIBILITY FUNCTIONS ############################################################################################################
####################################################################################################################################
def show_axis(transform_node: pm.nt.Transform):
    """ Display the local axis in the viewport. """
    transform_node.displayLocalAxis.set(1)

def hide_axis(transform_node: pm.nt.Transform):
    """Hide the local axis in the viewport."""
    transform_node.displayLocalAxis.set(0)
    
def has_visible_axis(transform_node: pm.nt.Transform) -> bool:
    """Ask if the local axis is visible in the viewport."""
    return transform_node.displayLocalAxis.get()

def hide_joint(joint_node: pm.nt.Joint):
    """Hide the joint shape in the viewport."""
    attrs = [
        ["v", 0],
        ["radius", 0],
        ["drawStyle", 2],  # 2 for none
        ["overrideDisplayType", 2]       
    ]

    for attr in attrs:
        if not joint_node.hasAttr(attr[0]):
            continue
        try:
            joint_node.overrideEnabled.set(1)
            joint_node.attr(attr[0]).set(attr[1])
            break
        except:
            continue

def show_joint(joint_node: pm.nt.Joint):
    """Show the joint shape in the viewport."""
    attrs = [
        ["v", 1],
        ["radius", 1],
        ["drawStyle", 0],  # 0 for normal
        ["overrideDisplayType", 0]       
    ]

    for attr in attrs:
        if not joint_node.hasAttr(attr[0]):
            continue
        try:
            joint_node.overrideEnabled.set(0)
            joint_node.attr(attr[0]).set(attr[1])
            break
        except:
            continue

def increase_joint_radius(joint_node: pm.nt.Joint, increment=1):
    """Increase the joint radius by the given increment."""
    if joint_node.hasAttr("radius"):
        current_radius = joint_node.radius.get()
        joint_node.radius.set(current_radius + increment)

def decrease_joint_radius(joint_node: pm.nt.Joint, decrement=1):
    """Decrease the joint radius by the given decrement."""
    if joint_node.hasAttr("radius"):
        current_radius = joint_node.radius.get()
        new_radius = max(0, current_radius - decrement)  # Prevent negative radius
        joint_node.radius.set(new_radius)  

####################################################################################################################################
#  HIERARCHY FUNCTIONS #############################################################################################################
####################################################################################################################################
def build_hierarchy_from_list(transform_list: list[pm.nt.Transform]) -> pm.nt.Transform:
    """Build a parent-child hierarchy following the list order."""
    for i in range(1, len(transform_list)):
        pm.parent(transform_list[i], transform_list[i-1])
    return transform_list[0]

def is_ancestor(ancestor_transform: pm.nt.Transform, descendant_transform: pm.nt.Transform) -> bool:
    """Check if the ancestor_transform is an ancestor of the descendant_transform."""
    if not ancestor_transform or not descendant_transform:
        return False
    if not isinstance(ancestor_transform, pm.nt.Transform) or not isinstance(descendant_transform, pm.nt.Transform):
        return False
    ancestors = pm.nt.Transform(descendant_transform).getAllParents()
    return ancestor_transform in ancestors

def find_first_ancestor(transform_node: pm.nt.Transform, transform_list: list[pm.nt.Transform]) -> pm.nt.Transform:
    parent_control = None
    ancestors = list(filter(lambda x: is_ancestor(x, transform_node), transform_list))
    if ancestors:
        parent_reference = ancestors[-1]  # Closest ancestor in the selection.
        parent_control = parent_reference
    return parent_control

def has_children(transform_node: pm.nt.Transform) -> bool:
    # TODO: Check if the transform has non-shape nodes.
    """Check if the given transform node has children."""
    children = transform_node.getChildren(type=pm.nt.Transform)
    return len(children) > 0

def create_hierarchy_from_dict(structure: dict, parent: pm.nt.Transform=None):
    """Creates a hierarchy from a Dictionary's keys.

    Args:
        structure: Dictionary with the hierarchy structure. Keys will be the name of groups.
        parent: Parent transform node. Defaults to None.
    """
    for key in structure.keys():
        transform_node = get_or_create_transform(key, parent)
        if structure[key]:
            create_hierarchy_from_dict(structure[key], transform_node)

def sort_by_hierarchy(transform_list: list[pm.nt.Transform]) -> list[pm.nt.Transform]:
    """Sort a list of transform nodes by their hierarchy, parents first."""
    updated_list = set(transform_list)

    if updated_list:
        updated_list = sorted(updated_list, key= lambda obj: obj.name(long=True))
        return list(updated_list)
    return []


####################################################################################################################################
#  DISPLAY FUNCTIONS ###############################################################################################################
####################################################################################################################################
def set_display_normal(transform_node: pm.nt.Transform):
    """Set the display of the given transform node to normal."""
    transform_node.overrideEnabled.set(0)  # Disable override to show normal display    

def set_display_template(transform_node: pm.nt.Transform):
    """Set the display of the given transform node to template mode."""
    transform_node.overrideEnabled.set(1)
    transform_node.overrideDisplayType.set(1)  # 1 for template mode

def set_display_reference(transform_node: pm.nt.Transform):
    """Set the display of the given transform node to reference mode."""
    transform_node.overrideEnabled.set(1)
    transform_node.overrideDisplayType.set(2)  # 2 for reference mode   

####################################################################################################################################
#  LOCKING FUNCTIONS ###############################################################################################################
####################################################################################################################################
def lock_node(node: pm.PyNode):
    node.setLocked(True)

def unlock_node(node: pm.PyNode):
    node.setLocked(False)

####################################################################################################################################
#  NODE CREATION ###################################################################################################################
####################################################################################################################################

def create_locator(name="locator") -> pm.nt.Transform:
    """Create a locator transform node."""
    locator = pm.spaceLocator(n=name)
    return locator

def create_joint(name="joint", parent=None) -> pm.nt.Transform:
    """Create a joint transform node."""
    joint = pm.joint(parent, n=name)
    return joint

def create_group(name="group", em=True) -> pm.nt.Transform:
    group = pm.group(em=em, n=name)
    return group

def create_condition_node(first_term=0, operation="==", second_term=0, if_true_value=[0, 0, 0], if_false_value=[1, 1, 1], name="condition") -> pm.nt.Condition:
    """
        Coded simplification of the use of Condition node in Node Editor to work more visually in text editor.
        Examples: condition(miNode.translateX, ">", yourNode.customAttribute, ifTrue= thatNode.scale, ifFalse=[1,1,1] )
        Args:
            firstTerm: 	int, float or Attribute,	first term of the condition, if is Attribute, will be connected, else will be assigned. (DEFAULT: 0)
            operation: 	string, 					conditional operation, might be: ==, !=, >,  >=, <, <=. (DEFAULT: "==")
            secondTerm:	int, float or Attribute,	second term of the condition, if is Attribute, will be connected, else will be assigned. (DEFAULT: 0)
            ifTrue: 	int, float or Attribute, 	resulting value if condition gives TRUE, if is Attribute, will be connected, else will be assigned. (DEFAULT: [0,0,0])
            ifFalse: 	int, float or Attribute, 	resulting value if condition gives FALSE, if is Attribute, will be connected, else will be assigned. (DEFAULT: [1,1,1])
            name: 		string, 					name that will be given to the condition node. (DEFAULT: "")

        Returns: node, condition node.
	"""
    operation_dict = {"==": 0, "!=": 1, ">": 2, ">=": 3, "<": 4, "<=": 5}

    condition_node = pm.nt.Condition(n=name) if name else pm.nt.Condition()
    condition_node.operation.set(operation_dict[operation])

    # Set first term. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(first_term, condition_node.firstTerm)
    
    # Set second term. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(second_term, condition_node.secondTerm)

    # Set ifTrue value. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(if_true_value, condition_node.colorIfTrue)    
    
    # Set ifFalse value. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(if_false_value, condition_node.colorIfFalse)

    return condition_node

def create_multiply_divide_node(input1=[0, 0, 0], operation="*", input2=[1, 1, 1], name="multiplyDivide") -> pm.nt.MultiplyDivide:
    """
        Coded simplification of the use of MultiplyDivide node in Node Editor.
        Inputs could be int, float, Attribute, nt.Vector or list(number, number, number).
        If the input is Attribute, it will be connected, else the value will be assigned to the input.
        
        Usage Example: create_multiply_divide_node(miNode.translateX, "/", yourNode.customAttribute, name="activator_MULT" )

	"""
    # MultiplyDivide node creation.
    operation_dict = {"": 0, "*": 1, "/": 2, "**": 3}
    multiply_node = pm.nt.MultiplyDivide(n=name) if name else pm.nt.MultiplyDivide()
    multiply_node.operation.set(operation_dict[operation])

    # Set input1. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(input1, multiply_node.input1)
    
    # Set input2. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(input2, multiply_node.input2)
    
    return multiply_node

def create_remapValue_node(input_min=0, input_max=1, output_min=0, output_max=0, name="remapValue") -> pm.nt.RemapValue:
    """Coded simplification of the use of remapValue node in Node Editor.
        Inputs could be int, float, Attribute.
        If the input is Attribute, it will be connected, else the value will be assigned to the input.
    Args:
        input_min (int, float): Minimum value of the input range. (DEFAULT: 0)
        input_max (int, float): Maximum value of the input range. (DEFAULT: 1)
        output_min (int, float): Minimum value of the output range. (DEFAULT: 0)
        output_max (int, float): Maximum value of the output range. (DEFAULT: 0)
        name (str): Name that will be given to the remapValue node. (DEFAULT: "")
    
    """
    remap_node = pm.shadingNode("remapValue", asUtility=True, n=name)

    connect_or_assign_value(input_min, remap_node.inputMin)
    connect_or_assign_value(input_max, remap_node.inputMax)

    connect_or_assign_value(output_min, remap_node.outputMin)
    connect_or_assign_value(output_max, remap_node.outputMax)
    return remap_node

def create_reverse(input: pm.Attribute, *outputs: pm.Attribute, name="reverse") -> pm.nt.Reverse:
    """Code simplification of the use of reverse node in Node Editor."""
    name = name if name else input.node().name() + "_reverse"
    reverse = pm.nt.Reverse(n=name)
    connect_or_assign_value(input, reverse.input)
    for output in outputs:
        connect_or_assign_value(reverse.outputX, output)
    return reverse

def create_blend_matrix(master:pm.nt.Transform,  weights: list[pm.nt.Transform], name="blendMatrix", ws=True) -> pm.nt.BlendMatrix:
    """Code simplification of the use of blendMatrix node in Node Editor to work more visually in text editor."""
    name = name if name else master.name() + "_blendMatrix"
    blend_matrix = pm.nt.BlendMatrix(n=name)

    matrix_at = master.worldMatrix if ws else master.matrix
    matrix_at >> blend_matrix.inputMatrix
    influence = 1 / (len(weights) + 1) if len(weights) > 0 else 0
    for index, weight in enumerate(weights):
        weight.worldMatrix >> blend_matrix.target[index].targetMatrix
        blend_matrix.target[index].weight.set(influence)
    return blend_matrix

def create_decompose_matrix(source_matrix: pm.Attribute, name="decomposeMatrix") -> pm.nt.DecomposeMatrix:
    """Code simplification of the use of decomposeMatrix node in Node Editor to work more visually in text editor."""
    name = name if name else source_matrix.node().name() + "_decomposeMatrix"
    node = pm.nt.DecomposeMatrix(n=name)

    source_matrix >> node.inputMatrix
    return node

def create_follicle(name="follicle") -> pm.nt.Transform:
    """Code simplification of the use of follicle node in Node Editor to work more visually in text editor.
    Args:
        name: Name that will be given to the follicle node and its transform parent.
    Return:
        pm.nt.Transform: follicle transform node.
    """
    name = name if name else "follicle"
    follicle_shape = pm.nt.Follicle(n=name)
    follicle_shape.simulationMethod.set(0)
    transform_node = follicle_shape.getParent()
    transform_node.rename(name)

    follicle_shape.outTranslate >> transform_node.t
    follicle_shape.outRotate >> transform_node.r

    return transform_node

def create_closest_point_on_mesh(name: str, mesh_transform: pm.nt.Transform, reference_object: pm.nt.Transform,) -> pm.nt.Transform:
    """Code simplification of the use of closestPointOnMesh node in Node Editor to work more visually in text editor."""
    closest_node = pm.nt.ClosestPointOnMesh(n=name)
    mesh_transform.getShape().worldMesh >> closest_node.inMesh

    decompose = create_decompose_matrix(reference_object.worldMatrix)
    decompose.outputTranslate >> closest_node.inPosition

    return closest_node

def create_closest_point_on_surface(name: str, surface_transform: pm.nt.Transform, reference_object: pm.nt.Transform) -> pm.nt.Transform:
    """Code simplification of the use of closestPointOnSurface node in Node Editor to work more visually in text editor."""
    closest_node = pm.nt.ClosestPointOnSurface(n=name)
    surface_transform.getShape().worldSpace >> closest_node.inputSurface

    decompose = create_decompose_matrix(reference_object.worldMatrix)
    decompose.outputTranslate >> closest_node.inPosition

    return closest_node

def create_rivet(name: str, surface: pm.nt.Transform, position_object: pm.nt.Transform, is_orbital=False) -> pm.nt.Transform:
        surface_shape = mesh_lib.get_render_shape(surface)
        follicle = create_follicle(name)

        decompose = create_decompose_matrix(position_object.worldMatrix)

        if common.is_mesh(surface):
            closest_node = create_closest_point_on_mesh(f"{name}_closestPointOnMesh", surface, position_object)
            surface_shape.worldMesh >> follicle.getShape().inputMesh
        if common.is_nurbs_surface(surface):
            closest_node = create_closest_point_on_surface(f"{name}_closestPointOnSurface", surface, position_object)
            surface_shape.worldSpace >> follicle.getShape().inputSurface

        decompose.outputTranslate >> closest_node.inPosition
        if is_orbital:
            closest_node.parameterU >> follicle.parameterU
            closest_node.parameterV >> follicle.parameterV
            
        else:
            follicle.parameterU.set(closest_node.parameterU.get())
            follicle.parameterV.set(closest_node.parameterV.get())
            pm.delete(closest_node, decompose)
        
        if not common.is_nurbs_surface(surface):
            surface_shape.worldMatrix >> follicle.inputWorldMatrix
            
        return follicle


####################################################################################################################################
#  SCENE CLEANING ##################################################################################################################
####################################################################################################################################

def clean_unused_nodes():
    """Delete unused nodes in the scene."""
    pm.mel.eval("MLdeleteUnused;")

def delete_unknown_nodes():
    """Delete unknown nodes in the scene."""
    pm.mel.eval("MLdeleteUnknown;")
