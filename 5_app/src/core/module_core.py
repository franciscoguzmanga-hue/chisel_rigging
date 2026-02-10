'''
################################################################################################################
Author: Francisco Guzmán

Content: Core classes and functions for rigging modules.
Dependency: pymel.core, src.utility.transform_utils
Maya Version tested: 2024

How to:
    - Use: Instructions to use the module
    - Test: Instructions to test the module
################################################################################################################
'''

from enum import Enum

import pymel.core as pm

from src.utility.transform_utils import get_or_create_transform


# Enum classes for display layer settings and status.
class DisplayType(Enum):
    NORMAL = 0
    REFERENCE = 1
    TEMPLATE = 2

class Status(Enum):
    OFF = 0
    ON = 1


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

class Rig:
    # Constants for naming conventions and group names.
    SUFFIX_RIG  = "rig"
    SUFFIX_SETS = "sets"

    GRP_GEO     = "Geometry"
    GRP_MODULES = "rig_modules"
    GRP_VIS     = "visible_modules"
    GRP_HID     = "hidden_modules"


    def __init__(self, name=""):        
        self.name = name
        self.root_name = f"{name}_{self.SUFFIX_RIG}" if name else self.SUFFIX_RIG
        self.set_name = f"{self.root_name}_{self.SUFFIX_SETS}"
        
        # Basic groups and sets names.
        self.grp_root   = None
        self.grp_geo    = None
        self.grp_modules = None
        self.grp_vis    = None
        self.grp_hid    = None
        self.set        = None

        self.modules = []

    def create_structure(self):
        # 1. Root
        self.grp_root = get_or_create_transform(self.root_name, None)

        # 2. Main groups
        self.grp_geo          = get_or_create_transform(self.GRP_GEO, self.grp_root)
        self.grp_modules      = get_or_create_transform(self.GRP_MODULES, self.grp_root)

        # 3. Sub groups
        self.grp_vis          = get_or_create_transform(self.GRP_VIS, self.grp_modules)
        self.grp_hid          = get_or_create_transform(self.GRP_HID, self.grp_modules)

        # 4. Sets
        self.set = get_or_create_set(self.set_name)

    def _create_display_layer(self, name: str, 
                       display_type: DisplayType, 
                       visibility:Status, 
                       playback_vis: Status, 
                       *members: pm.PyNode) -> pm.nt.DisplayLayer:
        """Create a display layer ste it up and add given members to it.
        Args:
            name (str): Name of the display layer to create.
            display_type (DisplayType): Display type for the display layer.
            visibility (Status): Visibility status for the display layer.
            playback_vis (Status): Playback visibility status for the display layer.
            members (pm.PyNode): Nodes to add to the display layer.

        Returns:
            pm.nt.DisplayLayer: The created display layer.
        """
        if pm.objExists(name):
            return pm.nt.DisplayLayer(name)
        
        display_layer = pm.nt.DisplayLayer(n=name)
        display_layer.displayType.set(display_type.value) # Reference
        display_layer.visibility.set(visibility.value)
        display_layer.playbackVisibility.set(playback_vis.value)
        if members:
            pm.editDisplayLayerMembers(display_layer, members)

        return display_layer

    def add_to_geometry_layer(self, *members: pm.PyNode) -> pm.nt.DisplayLayer:
        """Add given members to the geometry display layer, and create it if it doesn't exist.

        Returns:
            pm.nt.DisplayLayer: The geometry display layer with the new members added.
        """
        return self._create_display_layer(name="Geometry_DL",
                                   display_type=DisplayType.REFERENCE,
                                   visibility=Status.ON,
                                   playback_vis=Status.OFF, 
                                   *members)
        
    def add_to_control_layer(self, *members: pm.PyNode) -> pm.nt.DisplayLayer:
        """Add given members to the control display layer, and create it if it doesn't exist.

        Returns:
            pm.nt.DisplayLayer: The control display layer with the new members added.
        """
        return self._create_display_layer(name="Control_DL",
                                   display_type=DisplayType.NORMAL,
                                   visibility=Status.ON,
                                   playback_vis=Status.OFF, 
                                   *members)

    def register_module(self, module_grp, visible=True):
        """Register module and group it to the correct hierarchy."""
        parent = self.grp_vis if visible else self.grp_hid
        self.modules.append(module_grp)
        pm.parent(module_grp, parent)

    def register_set(self, object_set: pm.nt.ObjectSet):
        """Add the given set to the rig's main set."""
        self.set.addMember(object_set)

    def is_rig(self) -> bool:
        """Check if the current group is a rig group by checking if the main groups and sets exist in the given namespace.

        Returns:
            bool: True if the rig structure exists, False otherwise.
        """
        return all([pm.objExists(self.root_name),
                    pm.objExists(f"|{self.root_name}|{self.GRP_GEO}"),
                    pm.objExists(f"|{self.root_name}|{self.GRP_MODULES}"),
                    ])
    
    def cast(self) -> None:
    
        if not self.is_rig():
            raise ValueError(f"The group {self.root_name} does not have the structure of a Rig.")
    
        self.grp_root = pm.nt.Transform(self.root_name)
        self.grp_geo = pm.nt.Transform(f"|{self.root_name}|{self.GRP_GEO}")
        self.grp_modules = pm.nt.Transform(f"|{self.root_name}|{self.GRP_MODULES}")
        self.grp_vis = pm.nt.Transform(f"|{self.root_name}|{self.GRP_MODULES}|{self.GRP_VIS}")
        self.grp_hid = pm.nt.Transform(f"|{self.root_name}|{self.GRP_MODULES}|{self.GRP_HID}")
        self.set = pm.nt.ObjectSet(self.set_name)


class RigModule:
    SUFFIX_MODULE = "module"
    SUFFIX_SETS = "sets"
    GRP_VIS = "visible_grp"
    GRP_HID = "hidden_grp"

    def __init__(self, name: str):
        self.name = name
        self.root_name = f"{name}_{self.SUFFIX_MODULE}" if name else self.SUFFIX_MODULE
        self.name_set = f"{name}_{self.SUFFIX_SETS}" if name else self.SUFFIX_SETS

        self.name_vis_grp = f"{name}_{self.GRP_VIS}"
        self.name_hid_grp = f"{name}_{self.GRP_HID}"

        self.control_set_name = f"{self.name}_control_set"
        self.joint_set_name = f"{self.name}_joint_set"
        self.deformer_set_name = f"{self.name}_deformer_set"

        self.grp_root = None
        self.grp_vis = None
        self.grp_hid = None
        
        self.root_set = None
        self.control_set = None
        self.joint_set = None
        self.deformer_set = None

        self.controls = []
        self.joints = []
        self.deformers = []
        self.systems = []

    def create_structure(self) -> None:
        # 1. Root
        self.grp_root = get_or_create_transform(self.root_name, None)

        # 2. Sub groups
        self.grp_vis = get_or_create_transform(self.name_vis_grp, self.grp_root)
        self.grp_hid = get_or_create_transform(self.name_hid_grp, self.grp_root)
        self.grp_hid.it.set(0)
        self.grp_hid.v.set(0)

        # 3. Create sets
        self.root_set = get_or_create_set(self.name_set)

    def register_sub_system(self, system_grp, visible=True):
        """Register sub-system group to the module in the correct hierarchy.
         Args:
            system_grp (pm.PyNode): Sub-system root group to register.
            visible (bool, optional): Whether the sub-system should be registered as visible or hidden. Defaults to True.
        """
        parent = self.grp_vis if visible else self.grp_hid
        self.systems.append(system_grp)
        pm.parent(system_grp, parent)

    def register_controls(self, *controls: pm.PyNode) -> None:
        """Add controls to correct attribute and assign it to the module's control set.
        
        Args:
            controls (pm.PyNode): Control nodes to register.
        """
        [self.controls.append(control) for control in controls if control not in self.controls]
        self.control_set = get_or_create_set(self.control_set_name)
        [self.control_set.addMember(control) for control in controls]
        self.root_set.addMember(self.control_set)

    def register_joints(self, *joints: pm.PyNode) -> None:
        """Add joints to correct attribute and assign it to the module's joint set.
        
        Args:
            joints (pm.PyNode): Joint nodes to register.
        """
        [self.joints.append(joint) for joint in joints if joint not in self.joints]
        self.joint_set = get_or_create_set(self.joint_set_name)
        [self.joint_set.addMember(joint) for joint in joints]
        self.root_set.addMember(self.joint_set)

    def register_deformers(self, *deformers: pm.PyNode) -> None:
        """Add deformers to correct attribute and assign it to the module's deformer set.
        
        Args:
            deformers (pm.PyNode): Deformer nodes to register.
        """
        [self.deformers.append(deformer) for deformer in deformers if deformer not in self.deformers]
        self.deformer_set = get_or_create_set(self.deformer_set_name)
        [self.deformer_set.addMember(deformer) for deformer in deformers]
        self.root_set.addMember(self.deformer_set)
        
    def anchor_to(self, anchor_node: pm.nt.Transform) -> list[pm.nt.Constraint]:
        """Constrain module's root group to the given transform node to follow it and attach the 
         module to the main rig using constraints.
        
        Args:            
            anchor_node (pm.nt.Transform): Transform node to anchor the module to.
        
        Returns:            
            list[pm.nt.Constraint]: List of the created constraints.
        """
        parent_constraint = pm.parentConstraint(anchor_node, self.grp_root, mo=True)
        scale_constraint = pm.scaleConstraint(anchor_node, self.grp_root, mo=True)
        return [parent_constraint, scale_constraint]
    
    def is_module(self) -> bool:
        """Check if the current group is a rig module group by checking if the main groups and sets exist in the given namespace.

        Returns:
            bool: True if the rig module structure exists, False otherwise.
        """
        return all([pm.objExists(self.root_name),
                    pm.objExists(f"|{self.root_name}|{self.name_vis_grp}"),
                    pm.objExists(f"|{self.root_name}|{self.name_hid_grp}"),
                    pm.objExists(self.name_set),
                    ])

    def cast(self) -> None:
        """Cast the current group to a RigModule by checking if the rig module structure exists 
        in the given namespace and assigning the corresponding groups and sets to the instance variables."""
        if not self.is_module():
            raise ValueError(f"The group {self.root_name} does not have the structure of a RigModule.")
        
        self.grp_root = pm.nt.Transform(self.root_name)
        self.grp_vis = pm.nt.Transform(f"|{self.root_name}|{self.name_vis_grp}")
        self.grp_hid = pm.nt.Transform(f"|{self.root_name}|{self.name_hid_grp}")
        self.root_set = pm.nt.ObjectSet(self.name_set)

        # Optional sets
        if pm.objExists(self.control_set_name):
            self.control_set = pm.nt.ObjectSet(self.control_set_name)
            self.controls = self.control_set.members()
        if pm.objExists(self.joint_set_name):
            self.joint_set = pm.nt.ObjectSet(self.joint_set_name)
            self.joints = self.joint_set.members()
        if pm.objExists(self.deformer_set_name):
            self.deformer_set = pm.nt.ObjectSet(self.deformer_set_name)
            self.deformers = self.deformer_set.members()

    def build(self) -> None:
        self.create_structure()
