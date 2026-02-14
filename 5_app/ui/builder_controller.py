

from functools import partial
import pymel.core as pm

from src.utility.attribute_utils import Vector
from src.utility.transform_utils import is_ancestor
from src.utility.inspect_utils import is_transform
from src.core.control_lib import ctrl_lib
from src.rigging_modules.template import template
from src.rigging_modules.ribbon import Ribbon
from src.rigging_modules.ribbon import Surface
from src.rigging_modules.ribbon import SurfaceOrient


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
            "btn_create_control_semicircle":partial(self._create_control,ctrl_lib.Semicircle),
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
    def create_template(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            template.create_template(obj)

    def move_objects_to_templates(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            template.move_object_to_locator(obj)

    def move_templates_to_objects(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            template.move_locator_to_object(obj)
    
    def constraint_templates_to_midpoint(self):
        template_A, template_B, template_mid = pm.selected()
        template.constraint_to_midpoint(template_A, template_B, template_mid)

    def orient_templates_to_template(self):
        master_template, *slaves_templates = pm.selected()
        for slave in slaves_templates:
            template.aim_to(master_template, slave)

    # Ribbon functions
    def create_surface(self):
        selected_objects = pm.selected()
        surface = Surface(name="surface")
        surface.create(joints=selected_objects, width=1.0, normal=SurfaceOrient.Y_UP)

    def build_ribbon(self):
        # TODO: Complete with UI inputs.
        module_name = "ribbon"      # UI input.
        surface = pm.selected()[0]  # UI input.
        section_joints = 2          # UI input.
        ctrl_quantity = 5           # UI input.
        ribbon = Ribbon(name            = module_name, 
                        surface         = surface, 
                        section_joints  = section_joints, 
                        ctrl_quantity   = ctrl_quantity)
        ribbon.build()

    # Control functions
    def _create_control(self, control_class: ctrl_lib.Control):
        normal = Vector.X_POS  # UI input.
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
                if not is_ancestor(parent_object, obj):
                    continue
                
                control.parent_to(parent_object_name)
                parent_control = f"{objects[obj_index-1]}{control_suffix}"
                pm.parent(control.transform, parent_control)
            
            # Optional offset group.
            if with_offset:
                control.create_offset("_offset")

    def create_control_text(self, control_class: ctrl_lib.Control):
        text = "Control"  # UI input.
        control = ctrl_lib.Text()
        control.create(name="text_ctrl", text=text)
        
        selected_objects = pm.selected()
        for obj in selected_objects:
            control_name = f"{obj}{control_suffix}"
            control = control_class()
            control.create(name=control_name, text=text)
            control.align_to(obj)

    def control_shape_replace(self):
        selected_objects = pm.selected()
        source = selected_objects[:-1]
        destiny = selected_objects[-1]
        
        control = ctrl_lib.Control(destiny)
        control.replace_shape(*source)
        pm.delete(source)
    
    def control_shape_add(self):
        selected_objects = pm.selected()
        source = selected_objects[:-1]
        destiny = selected_objects[-1]
        
        control = ctrl_lib.Control(destiny)
        control.combine_shape(*source)
        pm.delete(source)

    def control_shape_swap(self):
        selected_objects = pm.selected()
        source = selected_objects[0]
        destiny = selected_objects[1:]
        
        for obj in destiny:
            control = ctrl_lib.Control(obj)
            control.replace_shape(source)

    def control_shape_copy(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            control = ctrl_lib.Control(obj)
            control.shape_copy()

    def control_shape_mirror(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            control = ctrl_lib.Control(obj)
            control.shape_mirror()

    def control_shape_resize(self):
        scale = 1.5  # UI input.

        selected_controls = pm.selected()
        for obj in selected_controls:
            control = ctrl_lib.Control(obj)
            control.scale_shape(scale)

    def control_shape_thicken(self):
        selected_controls = pm.selected()
        for obj in selected_controls:
            if not is_transform(obj):
                continue
            control = ctrl_lib.Control(obj)
            control.thicken()
    
    def control_shape_thin(self):
        selected_controls = pm.selected()
        for obj in selected_controls:
            if not is_transform(obj):
                continue
            control = ctrl_lib.Control(obj)
            control.thin()

    def control_shape_color_index(self):
            color_index = ctrl_lib.ColorIndex.RED.value  # UI input.
            selected_controls = pm.selected()
            for obj in selected_controls:
                control = ctrl_lib.Control(obj)
                control.set_color_index(color_index)

    def reset_controls(self):
        selected_controls = pm.selected()
        for obj in selected_controls:
            control = ctrl_lib.Control(obj)
            control.reset()
        
    