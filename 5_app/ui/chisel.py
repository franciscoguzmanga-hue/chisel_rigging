
from functools import partial
import pymel.core as pm
import utility.common as common
import utility.maya_lib as maya_lib
import utility.mesh_lib as mesh_lib
import core.control_framework as ctrl_lib
from components.template import template, ribbon

class MainController:
    def __init__(self, view):
        self.view = view
        
        self.builder = BuilderController(self.view)
        self.edit    = EditController(self.view)
        self.surgery = SurgeryController(self.view)


class BuilderController:
    def __init__(self, view):
        self.view = view
        self.bind_view()

    def bind_view(self):
        
        connections = {
            # Template module functions
            "btn_create_template":      self.create_template,
            "btn_object_to_template":   self.move_objects_to_templates,
            "btn_template_to_object":   self.move_templates_to_objects,
            "btn_template_to_mid":      self.constraint_templates_to_midpoint,
            "btn_aim_to_template":      self.orient_templates_to_template,

            # Ribbon module functions
            "btn_create_surface":       self.create_surface,
            "btn_build_ribbon":         self.build_ribbon,

            # Control functions
            "btn_create_control_circle":    partial(self._create_control,ctrl_lib.Circle),
            "btn_create_control_square":    partial(self._create_control,ctrl_lib.Square),
            "btn_create_control_triangle":  partial(self._create_control,ctrl_lib.Triangle),

            "btn_create_control_arrow":     partial(self._create_control,ctrl_lib.Arrow),
            "btn_create_control_pin":       partial(self._create_control,ctrl_lib.Pin),
            "btn_create_control_cross":     partial(self._create_control,ctrl_lib.Cross),

            "btn_create_control_cube":      partial(self._create_control,ctrl_lib.Cube),
            "btn_create_control_cube_fk":   partial(self._create_control,ctrl_lib.CubeFK),
            "btn_create_control_sphere":    partial(self._create_control,ctrl_lib.Sphere),
            "btn_create_control_orient":    partial(self._create_control,ctrl_lib.Orient),
            "btn_create_control_button":    partial(self._create_control,ctrl_lib.Button),
            "btn_create_control_ring":      partial(self._create_control,ctrl_lib.Ring),

            "btn_create_control_slider":    partial(self._create_control,ctrl_lib.Slider),
            "btn_create_control_osipa":     partial(self._create_control,ctrl_lib.Osipa),
            "btn_create_control_semicircle":partial(self._create_control,ctrl_lib.SemiCircle),
            "btn_create_control_text":      partial(self._create_control,ctrl_lib.Text),

            "btn_control_shape_replace":    self.control_shape_replace,
            "btn_control_shape_add":        self.control_shape_add,
            "btn_control_shape_swap":       self.control_shape_swap,
            "btn_control_shape_copy":       self.control_shape_copy,
            "btn_control_shape_mirror":     self.control_shape_mirror,
            "btn_control_shape_resize":     self.control_shape_resize,
            "btn_control_shape_thicken":    self.control_shape_thicken,
            "btn_control_shape_thin":       self.control_shape_thin,
            "btn_control_shape_color_index":self.control_shape_color_index,
            "btn_reset_controls":           self.reset_controls,
        }

        for button_name, method in connections.items():
            button = getattr(self.view, button_name, None)
            if button:
                button.clicked.connect(method)
            else:
                pm.warning(f"Button '{button_name}' not found in the view. Connection skipped.")

    # Template functions
    @common.undo_chunk("Create Templates")   
    def create_template(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            template.create_template(obj)

    @common.undo_chunk("Move Objects to Templates")
    def move_objects_to_templates(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            template.move_object_to_locator(obj)

    @common.undo_chunk("Move Templates to Objects")
    def move_templates_to_objects(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            template.move_locator_to_object(obj)
    
    @common.undo_chunk("Constraint Templates to Midpoint")
    def constraint_templates_to_midpoint(self):
        template_A, template_B, template_mid = pm.selected()
        template.constraint_to_midpoint(template_A, template_B, template_mid)

    @common.undo_chunk("Orient Templates to Template")
    def orient_templates_to_template(self):
        master_template, *slaves_templates = pm.selected()
        for slave in slaves_templates:
            template.aim_to(master_template, slave)

    # Ribbon functions
    @common.undo_chunk("Create Surface")
    def create_surface(self):
        selected_objects = pm.selected()
        surface = ribbon.Surface(name="surface")
        surface.create(joints=selected_objects, width=1.0, normal=ribbon.SurfaceOrient.Y_UP)

    @common.undo_chunk("Build Ribbon")
    def build_ribbon(self):
        # TODO: Complete with UI inputs.
        module_name = "ribbon"      # UI input.
        surface = pm.selected()[0]  # UI input.
        section_joints = 2          # UI input.
        ctrl_quantity = 5           # UI input.
        module = ribbon.Ribbon(name     = module_name, 
                        surface         = surface, 
                        section_joints  = section_joints, 
                        ctrl_quantity   = ctrl_quantity)
        module.build()

    # Control functions
    @common.undo_chunk("Create Control")
    def _create_control(self, control_class: ctrl_lib.Control):
        normal = common.Vector.X_POS  # UI input.
        with_offset = True     # UI input.
        
        selected_objects = pm.selected()
        control_suffix = "_ctrl"

        # Sort objects by hierarchy depth.
        objects = sorted(selected_objects, key= lambda obj: obj.name(long=True))
        for obj_index in range(len(objects)):
            obj = objects[obj_index]

            # Control creation.
            control_name = f"{obj}{control_suffix}"
            control = control_class()
            control.create(name=control_name, normal=normal)
            control.align_to(obj)

            # Parent control to the previous one in the hierarchy.
            if obj_index > 0:
                parent_object_name = f"{objects[obj_index-1]}"
                parent_object = pm.nt.Transform(parent_object_name)
                if not maya_lib.is_ancestor(parent_object, obj):
                    continue
                
                control.offset = parent_object_name
                parent_control = f"{objects[obj_index-1]}{control_suffix}"
                pm.parent(control.transform, parent_control)
            
            # Optional offset group.
            if with_offset:
                control.create_offset("_offset")

    def create_control_text(self, control_class: ctrl_lib.Control):
        text = "Control"  # UI input.
        normal = common.Vector.X_POS  # UI input.
        
        control_instance = ctrl_lib.Text(text=text)

        self._create_control(control_class=control_instance)

    @common.undo_chunk("Replace Control Shape")
    def control_shape_replace(self):
        selected_objects = pm.selected()
        source = selected_objects[:-1]
        destiny = selected_objects[-1]
        
        control = ctrl_lib.Circle(destiny)
        control.shape_replace(*source)
        pm.delete(source)
    
    @common.undo_chunk("Add Control Shape")
    def control_shape_add(self):
        selected_objects = pm.selected()
        source = selected_objects[:-1]
        destiny = selected_objects[-1]
        
        control = ctrl_lib.Circle(destiny)
        control.shape_combine(*source)
        pm.delete(source)

    @common.undo_chunk("Swap Control Shape")
    def control_shape_swap(self):
        selected_objects = pm.selected()
        source = selected_objects[0]
        destiny = selected_objects[1:]
        
        for obj in destiny:
            control = ctrl_lib.Circle(obj)
            control.shape_replace(source)
    
    @common.undo_chunk("Copy Control Shape")
    def control_shape_copy(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            control = ctrl_lib.Circle(obj)
            control.copy()

    @common.undo_chunk("Mirror Control Shape")
    def control_shape_mirror(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            control = ctrl_lib.Circle(obj)
            control.mirror()

    @common.undo_chunk("Resize Control Shape")
    def control_shape_resize(self):
        scale = 1.5  # UI input.

        selected_controls = pm.selected()
        for obj in selected_controls:
            control = ctrl_lib.Circle(obj)
            control.shape_scale(scale)

    @common.undo_chunk("Thicken Control Shape")
    def control_shape_thicken(self):
        selected_controls = pm.selected()
        for obj in selected_controls:
            if not common.is_transform(obj):
                continue
            control = ctrl_lib.Circle(obj)
            control.shape_line_thick()
    
    @common.undo_chunk("Thin Control Shape")
    def control_shape_thin(self):
        selected_controls = pm.selected()
        for obj in selected_controls:
            if not common.is_transform(obj):
                continue
            control = ctrl_lib.Circle(obj)
            control.shape_line_thin()

    @common.undo_chunk("Change Control Color Index")
    def control_shape_color_index(self):
            color_index = ctrl_lib.ColorIndex.RED.value  # UI input.
            selected_controls = pm.selected()
            for obj in selected_controls:
                control = ctrl_lib.Circle(obj)
                control.shape_color_index(color_index)

    @common.undo_chunk("Reset Controls")
    def reset_controls(self):
        selected_controls = pm.selected()
        for obj in selected_controls:
            control = ctrl_lib.Circle(obj)
            control.reset()
        
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

    @common.undo_chunk("Freeze Transformations")    
    def freeze_transformations(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            maya_lib.freeze_transform(obj)

    @common.undo_chunk("Delete History")
    def delete_history(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            maya_lib.delete_history(obj)

    @common.undo_chunk("Create Offset Group")
    def create_offset_group(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            maya_lib.create_offset(obj, "_root")

    @common.undo_chunk("Align Many to One")
    def align_many_to_one(self):
        master, *slaves = pm.selected()
        for slave in slaves:
            if not common.is_transform(slave) and not common.is_transform(master):
                continue
            maya_lib.align_transform(master, slave)

    @common.undo_chunk("Move to Surface")
    def move_to_surface(self):
        mesh, *slaves = pm.selected()
        for slave in slaves:
            if not common.is_transform(slave) and not common.is_transform(mesh):
                continue
            mesh_lib.move_to_mesh_surface(mesh, slave)

    @common.undo_chunk("Orient to Surface")
    def orient_to_surface(self):
        mesh, *slaves = pm.selected()
        for slave in slaves:
            if not common.is_transform(slave) and not common.is_transform(mesh):
                continue
            mesh_lib.orient_to_mesh_surface(mesh, slave)

    @common.undo_chunk("Create Locator at Selection")
    def _create_at_selection(self, create_func, suffix):
        selected_objects = pm.selected()
        for obj in selected_objects:
            created_node = create_func()
            
            if common.is_transform(obj):
                name = f"{obj.name()}_{suffix}"
                maya_lib.align_transform(obj, created_node)
            else:
                # To align with components like vertices.
                name = f"{obj.node().name()}_{suffix}"
                matrix = obj.getMatrix(worldSpace=True)
                created_node.setMatrix(matrix, worldSpace=True)
            created_node.rename(name)

    @common.undo_chunk("Create Locator at Selection")
    def create_locator_at_selection(self):
        self._create_at_selection(pm.spaceLocator, "locator")

    @common.undo_chunk("Create Transform at Selection")
    def create_transform_at_selection(self):
        self._create_at_selection(pm.nt.Transform, "grp")

    @common.undo_chunk("Create Joint at Selection")
    def create_joint_at_selection(self):
        self._create_at_selection(pm.nt.Joint, "jnt")

    @common.undo_chunk("Create Joint at Center")
    def create_joint_at_center(self):
        selected_objects = pm.selected()
        cluster = pm.cluster(selected_objects, n="temp_cluster")[1]
        
        name = f"{selected_objects[0].name()}_center"
        joint = pm.nt.Joint(n=name)
        maya_lib.align_transform(cluster, joint)
        pm.delete(cluster)

    @common.undo_chunk("Build Hierarchy")
    def build_hierarchy(self):
        selected_objects = pm.selected()
        maya_lib.build_hierarchy_from_list(selected_objects)


class SurgeryController:
    def __init__(self, view):
        self.view = view
        self.bind_view()

    def bind_view(self):
        pass
        #self.view.surgery_button.clicked.connect(self.handle_surgery)
