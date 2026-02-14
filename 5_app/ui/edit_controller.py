'''
Content: Class to bind edit functions to UI's edit.
Dependency: pymel.core, src.utility.transform_utils, src.utility.mesh_utils
Maya Version tested: 2024

Author: Francisco Guzmán
Email: francisco.guzmanga@gmail.com
How to:
    - Use: Instructions to use the module
    - Test: Instructions to test the module
'''

import pymel.core as pm
from src.utility.inspect_utils import is_transform
from src.utility.transform_utils import freeze_transform
from src.utility.transform_utils import delete_history
from src.utility.transform_utils import align_transform
from src.utility.transform_utils import build_hierarchy_from_list
from src.utility.transform_utils import create_offset
from src.utility.mesh_utils import move_to_mesh_surface, orient_to_mesh_surface

class EditController:
    def __init__(self, view):
        self.view = view
        self.bind_view()

    def bind_view(self):
        
        connections = {
            "btn_freeze_transformation":    self.freeze_transformations,
            "btn_delete_history":           self.delete_history,
            "btn_create_offset_group":      self.create_offset_group,
            "btn_align_many_to_one":        self.align_many_to_one,
            "btn_move_to_surface":          self.move_to_surface,
            "btn_orient_to_surface":        self.orient_to_surface,
            "btn_create_locator_at_selection":   self.create_locator_at_selection,
            "btn_create_transform_at_selection": self.create_transform_at_selection,
            "btn_create_joint_at_selection": self.create_joint_at_selection,
            "btn_create_joint_at_center":   self.create_joint_at_center,
            "btn_build_hierarchy":          self.build_hierarchy,
        }

        for button_name, method in connections.items():
            button = getattr(self.view, button_name, None)
            if button:
                button.clicked.connect(method)
        
    def freeze_transformations(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            freeze_transform(obj)

    def delete_history(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            delete_history(obj)

    def create_offset_group(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            create_offset(obj, "_root")

    def align_many_to_one(self):
        master, *slaves = pm.selected()
        for slave in slaves:
            if not is_transform(slave) and not is_transform(master):
                continue
            align_transform(master, slave)

    def move_to_surface(self):
        mesh, *slaves = pm.selected()
        for slave in slaves:
            if not is_transform(slave) and not is_transform(mesh):
                continue
            move_to_mesh_surface(mesh, slave)

    def orient_to_surface(self):
        mesh, *slaves = pm.selected()
        for slave in slaves:
            if not is_transform(slave) and not is_transform(mesh):
                continue
            orient_to_mesh_surface(mesh, slave)

    def _create_at_selection(self, create_func, suffix):
        selected_objects = pm.selected()
        for obj in selected_objects:
            created_node = create_func()
            
            if is_transform(obj):
                name = f"{obj.name()}_{suffix}"
                align_transform(obj, created_node)
            else:
                # To align with components like vertices.
                name = f"{obj.node().name()}_{suffix}"
                matrix = obj.getMatrix(worldSpace=True)
                created_node.setMatrix(matrix, worldSpace=True)
            created_node.rename(name)

    def create_locator_at_selection(self):
        self._create_at_selection(pm.spaceLocator, "locator")

    def create_transform_at_selection(self):
        self._create_at_selection(pm.nt.Transform, "grp")

    def create_joint_at_selection(self):
        self._create_at_selection(pm.nt.Joint, "jnt")

    def create_joint_at_center(self):
        selected_objects = pm.selected()
        cluster = pm.cluster(selected_objects, n="temp_cluster")[1]
        
        name = f"{selected_objects[0].name()}_center"
        joint = pm.nt.Joint(n=name)
        align_transform(cluster, joint)
        pm.delete(cluster)

    def build_hierarchy(self):
        selected_objects = pm.selected()
        build_hierarchy_from_list(selected_objects)
        
