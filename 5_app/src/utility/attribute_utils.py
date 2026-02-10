'''
################################################################################################################
Author: Francisco Guzmán

Content: Collection of functions to manipulate node attributes inside Maya.
Dependency: pymel.core, Enum
Maya Version tested: 2024

How to:
    - Use: Import the module and call the functions as needed.
    - Test: Use pymel.core to create transform nodes and test the functions interactively in Maya.
################################################################################################################
'''


from enum import Enum

import pymel.core as pm



class Vector(Enum):
    X_POS = (1, 0, 0)
    X_NEG = (-1, 0, 0)
    Y_POS = (0, 1, 0)
    Y_NEG = (0, -1, 0)
    Z_POS = (0, 0, 1)
    Z_NEG = (0, 0, -1)


# Attribute Manipulation Functions
def connect_attributes(master: pm.nt.Transform, slave: pm.nt.Transform, attributes=("t", "r", "s", "v")) -> None:
    """Connect related attributes between two transforms.

    Args:
        master (pm.nt.Transform): The driving transform node.
        slave (pm.nt.Transform): The driven transform node.
        attributes (list[str], optional): Attributes to connect. Defaults to ("t", "r", "s", "v").
    """
    for attr in attributes:
        if slave.hasAttr(attr) and master.hasAttr(attr):
            master.attr(attr) >> slave.attr(attr)

def connect_all_keyable_attributes(master: pm.nt.Transform, slave: pm.nt.Transform) -> None:
    """Connect all keyable and related attributes between two transform nodes.

    Args:
        master (pm.nt.Transform): The driving transform node.
        slave (pm.nt.Transform): The driven transform node.
    """
    master_keyable_attributes = [attr.shortName() for attr in master.listAttr(keyable=True) if attr.isSettable()]
    connect_attributes(master=master, slave=slave, attributes=master_keyable_attributes)

def get_selected_attributes(transform_node: pm.nt.Transform) -> list[pm.Attribute]:
    """Get a list of the selected attributes in the channelbox.

    Args:
        transform_node (pm.nt.Transform): The transform node to check for the selected attributes.

    Returns:
        list[pm.Attribute]: List of the selected attributes.
    """
    selected_attrs = pm.channelBox("mainChannelBox", q=True, sma=True) or []
    attributes = []
    for attribute in selected_attrs:
        if transform_node.hasAttr(attribute):
            attributes.append(transform_node.attr(attribute))
    return attributes

def update_attribute_default(attribute: pm.Attribute) -> None:
    """Update the default value of an attribute to its current value.

    Args:
        attribute (pm.Attribute): The attribute to update.
    """
    current_value = attribute.get()
    pm.addAttr(attribute, edit=True, defaultValue=current_value)

def lock_attribute(attribute: pm.Attribute) -> None:
    attribute.set(lock=True)

def lock_and_hide_attribute(attribute: pm.Attribute) -> None:
    """Lock and hide the given attribute from the channelBox.

    Args:
        attribute (pm.Attribute): The attribute to lock and hide.
    """
    attribute.set(lock=True)
    attribute.setKeyable(False)
    attribute.showInChannelBox(False)

def unlock_attribute(attribute: pm.Attribute) -> None:
    """Unlock and set it visible in the channel box.

    Args:
        attribute (pm.Attribute): The attribute to unlock and show.
    """
    attribute.set(lock=False)
    attribute.setKeyable(True)
    attribute.showInChannelBox(True)

def set_non_keyable(attribute: pm.Attribute) -> None:
    attribute.set(keyable=False)

def set_keyable(attribute: pm.Attribute) -> None:
    attribute.set(keyable=True)

def create_proxy_attribute(source_attribute: pm.Attribute, target_node: pm.nt.Transform) -> None:
    """Create an attribute from a source and keep it related, similar to an instance.
       Helps to have an attribute accessible from different transform nodes and simplify animation.

    Args:
        source_attribute (pm.Attribute): Source attribute to proxy.
        target_node (pm.nt.Transform): Target node to create the proxy attribute in.
    """
    proxy_attr_name = source_attribute.longName()
    if not target_node.hasAttr(proxy_attr_name):
        pm.addAttr(target_node, ln=proxy_attr_name, k=True, proxy=source_attribute)

def reset_attribute(attribute: pm.Attribute) -> None:
    """Reset the attribute to its default value if it is keyable, settable, and not locked.

    Args:
        attribute (pm.Attribute): The attribute to reset.
    """
    if attribute.isKeyable() and attribute.isSettable() and not attribute.isLocked():
        default_value = attribute.getDefault()
        attribute.set(default_value)

def connect_or_assign_value(value, target_attribute: pm.Attribute) -> None:
    """Connect the value to the target attribute if it's an attribute, else assign the value to the attribute.

    Args:
        value (int, float, list, pm.Attribute): The value to connect or assign.
        target_attribute (pm.Attribute): The attribute to connect or assign the value to.
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


