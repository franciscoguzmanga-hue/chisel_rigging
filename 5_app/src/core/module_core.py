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

from src.utils.transform_utils import create_transform_node, create_hierarchy_from_dict


# RIG AND MODULE STRUCTURE
RIG_STRUCTURE = {
    "rig": {
        "geometry": [],
        "rig_modules": {
            "visible_modules": [],
            "hidden_modules": []
        },
    "sets": []
    }
}

MODULE_STRUCTURE = {
    "module": {
        "visible_grp": {
            "control_grp": [],
        },
        "hidden_grp": [],
    }
}

# Enum classes for display layer settings and status.
class DisplayType(Enum):
    NORMAL = 0
    REFERENCE = 1
    TEMPLATE = 2

class Status(Enum):
    OFF = 0
    ON = 1


class Rig:
    def __init__(self, name=""):
        root_key = list(RIG_STRUCTURE.keys())[0]
        
        self.name_main = f"{name}_{root_key}" # Main rig group name.
        
        # Basic groups and sets names.
        self.name_geometry      = "Geometry"
        self.name_rig_modules   = "rig_modules"
        self.name_visible_modules   = "visible_modules"
        self.name_hidden_modules    = "hidden_modules"
        self.name_set = f"{self.name_main}_sets"

        # Create rig group structure.
        
        rig_structure = {self.name_main: RIG_STRUCTURE[root_key]}
        create_hierarchy_from_dict(rig_structure, None)

        self.visible_modules = []
        self.hidden_modules = []

    def create_structure(self):
        self.group_main         = create_transform_node(self.name_main, None)
        self.group_geometry     = create_transform_node(self.name_geometry)
        self.group_rig_modules  = create_transform_node(self.name_rig_modules)
        self.group_visible_modules = create_transform_node(self.name_visible_modules)
        self.group_hidden_modules  = create_transform_node(self.name_hidden_modules)

        self.set = self.add_to_rig_set(self.name_set)

    def add_to_rig_set(self, *members: pm.PyNode) -> pm.nt.ObjectSet:
        """ Add nodes to main rig set and creates it if it doesn't exist.

        Returns:
            pm.nt.ObjectSet: The rig set with the new members added.
        """
        rig_set = None
        if pm.objExists(self.name_set):
            rig_set = pm.nt.ObjectSet(self.name_set) 
        else:
            rig_set = pm.nt.ObjectSet(n=self.name_set)
        
        if members:
            [rig_set.addMember(obj) for obj in members]

        return rig_set

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

    def add_to_geometry_display_layer(self, *members: pm.PyNode) -> pm.nt.DisplayLayer:
        """Add given members to the geometry display layer, and create it if it doesn't exist.

        Returns:
            pm.nt.DisplayLayer: The geometry display layer with the new members added.
        """
        return self._create_display_layer(name="Geometry_DL",
                                   display_type=DisplayType.REFERENCE,
                                   visibility=Status.ON,
                                   playback_vis=Status.OFF, 
                                   *members)
        
    def add_to_control_display_layer(self, *members: pm.PyNode) -> pm.nt.DisplayLayer:
        """Add given members to the control display layer, and create it if it doesn't exist.

        Returns:
            pm.nt.DisplayLayer: The control display layer with the new members added.
        """
        return self._create_display_layer(name="Control_DL",
                                   display_type=DisplayType.NORMAL,
                                   visibility=Status.ON,
                                   playback_vis=Status.OFF, 
                                   *members)

    def add_to_visible_module(self, module_grp:pm.nt.Transform) -> None:
        pm.parent(module_grp, self.group_visible_modules)

    def add_to_hidden_module(self, module_grp: pm.nt.Transform)-> None:
        pm.parent(module_grp, self.group_hidden_modules)

    def is_rig(self, namespace: str=":") -> bool:
        """Check if the current group is a rig group by checking if the main groups and sets exist in the given namespace.

        Returns:
            bool: True if the rig structure exists, False otherwise.
        """
        exists_root_grp = pm.objExists(f"{namespace}{self.group_main}") 
        exists_geometry_grp = pm.objExists(f"{namespace}{self.group_geometry}")
        exists_modules = pm.objExists(f"{namespace}{self.group_rig_modules}")

        return exists_root_grp and exists_geometry_grp and exists_modules

TODO: REFACTOR RigModule
class RigModule:
    def __init__(self, name: str):
        self.name = f"{name}"
        self.name_visible_grp = f"{name}_visible_grp"
        self.name_hidden_grp = f"{name}_hidden_grp"

        self.controls = []
        self.joints = []

    def create_structure(self):
        self.group_main = self.create_internal_group(self.name + "_module", None)
        self.group_visible = self.create_internal_group(self.name_visible_grp, self.group_main)
        self.group_hidden = self.create_internal_group(self.name_hidden_grp, self.group_main)
        self.group_hidden.it.set(0)
        self.group_hidden.v.set(0)

        self.anchored_to = None
        self.set_master = None
        self.set_slaves = []

    def create_internal_group(self, name, parent):
        group = pm.nt.Transform(name) if pm.objExists(name) else pm.nt.Transform(n=name)
        pm.parent(group, parent)
        return group

    def create_module_set(self, name, *members):
        ##  CREATE SUB SET.
        set_name = f"{self.name}_{name}_set"
        object_set = pm.nt.ObjectSet(set_name) if pm.objExists(set_name) else pm.nt.ObjectSet(n=set_name)
        [object_set.addMember(obj) for obj in members]

        self.set_slaves.append(object_set) if object_set not in self.set_slaves else None

        ##  OBTAIN MASTER SET.
        master_name = f"{self.name}_sets"
        master_set = pm.nt.ObjectSet(master_name) if pm.objExists(master_name) else pm.nt.ObjectSet(n=master_name)
        master_set.addMember(object_set)
        self.set = master_set

    def anchor_to(self, obj):
        pm.parentConstraint(obj, self.group_main, mo=True)
        pm.scaleConstraint(obj, self.group_main, mo=True)
        self.anchored_to = obj

    def build(self):
        self.create_structure()
        if self.joints:
            self.create_module_set("joints", *self.joints)
        if self.controls:
            self.create_module_set("controls", *self.controls)

    def rebuild(self):
        pass


