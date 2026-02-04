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
    for attr in attributes:
        if slave.hasAttr(attr) and master.hasAttr(attr):
            master.attr(attr) >> slave.attr(attr)

def connect_all_keyable_attributes(master: pm.nt.Transform, slave: pm.nt.Transform) -> None:
    master_keyable_attributes = [attr.shortName() for attr in master.listAttr(keyable=True) if attr.isSettable()]
    connect_attributes(master=master, slave=slave, attributes=master_keyable_attributes)

def get_selected_attributes(transform_node: pm.nt.Transform) -> list:
    selected_attrs = pm.channelBox("mainChannelBox", q=True, sma=True) or []
    attributes = []
    for attribute in selected_attrs:
        if transform_node.hasAttr(attribute):
            attributes.append(transform_node.attr(attribute))
    return attributes

def update_attribute_default(attribute: pm.Attribute) -> None:
    current_value = attribute.get()
    pm.addAttr(attribute, edit=True, defaultValue=current_value)

def lock_attribute(attribute: pm.Attribute) -> None:
    attribute.set(lock=True)

def lock_and_hide_attribute(attribute: pm.Attribute) -> None:
    attribute.set(lock=True)
    attribute.setKeyable(False)
    attribute.showInChannelBox(False)

def unlock_attribute(attribute: pm.Attribute) -> None:
    attribute.set(lock=False)   

def set_non_keyable(attribute: pm.Attribute) -> None:
    attribute.set(keyable=False)

def set_keyable(attribute: pm.Attribute) -> None:
    attribute.set(keyable=True)

def create_proxy_attribute(source_attribute: pm.Attribute, target_node: pm.nt.Transform) -> None:
    proxy_attr_name = source_attribute.longName()
    if not target_node.hasAttr(proxy_attr_name):
        pm.addAttr(target_node, ln=proxy_attr_name, k=True, proxy=source_attribute)

def reset_attribute(attribute: pm.Attribute) -> None:
    if attribute.isKeyable() and attribute.isSettable() and not attribute.isLocked():
        default_value = attribute.getDefault()
        attribute.set(default_value)

