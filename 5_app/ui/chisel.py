

import os
from functools import partial

import pymel.core as pm
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from shiboken2 import wrapInstance

import components.helpers as helpers
import components.ribbon as ribbon
import core.control_framework as ctrl_lib
import utility.common as common
import utility.maya_lib as maya_lib
import utility.mesh_lib as mesh_lib
from ui.Qt import QtWidgets, QtGui, QtCore, QtCompat


FILE_NAME   = os.path.basename(__file__).replace(".py", "")
TITLE       = FILE_NAME.capitalize()
CURRENT_DIR = os.path.dirname(__file__)
UI_PATH     = os.path.join(CURRENT_DIR, f"{TITLE}.ui")
ICONS_PATH  = os.path.join(CURRENT_DIR, "icons")
QSS_PATH    = os.path.join(CURRENT_DIR, f"{TITLE}.qss")

CHISEL_ID = "ChiselRiggingUI"
WORKSPACE_CONTROL = f"{CHISEL_ID}WorkspaceControl"
_CHISEL_UI_INSTANCE = None

def get_maya_main_window():
    """
    Get a pointer to the main Maya window as a QMainWindow instance.
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if main_window_ptr is not None:
        return wrapInstance(int(main_window_ptr), QtWidgets.QMainWindow)
    return None

def deleteUI():
    if pm.workspaceControl(WORKSPACE_CONTROL, q=True, exists=True):
        pm.deleteUI(WORKSPACE_CONTROL, control=True)

    maya_window = get_maya_main_window()
    if maya_window:
        existing_window = maya_window.findChild(QtWidgets.QDialog, CHISEL_ID)
        if existing_window:
            existing_window.close()
            existing_window.deleteLater()



class ChiselUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        
        super().__init__(parent)                
        self.setObjectName(CHISEL_ID)
        
        QtCompat.loadUi(UI_PATH, self)
        self.setStyleSheet(open(QSS_PATH, "r").read())
        images = {
            "btnCircle":  "circle_icon.png",
            "btnSquare":  "square_icon.png",
            "btnTriangle":"triangle_icon.png",
            "btnCross":   "cross_icon.png",
            "btnArrow":   "arrow_icon.png",
            "btnPin":     "pin_icon.png",
            "btnCubeCN":  "cube_cn_icon.png",
            "btnCubeFk":  "cube_fk_icon.png",
            "btnSphere":  "sphere_icon.png",
            "btnOrient":  "orient_icon.png",
            "btnButton":  "button_icon.png",
            "btnRing":    "ring_icon.png",
            "btnSlider":  "slider_icon.png",
            "btnOsipa":   "osipa_icon.png",
            "btnSemiCircle": "semi_circle_icon.png",
            "btnControlText": "text_icon.png",
        }
        
        for button_name, image_file in images.items():
            button = getattr(self, button_name, None)
            if button:
                button.setText("")
                button.setIcon(QtGui.QIcon(os.path.join(ICONS_PATH, image_file)))
            else:
                pm.warning(f"Button '{button_name}' not found in the UI. Icon assignment skipped.")
        
        self.controller = MainController(self)

    def closeEvent(self, event):
        global _CHISEL_UI_INSTANCE
        _CHISEL_UI_INSTANCE = None
        super().closeEvent(event)


def showUI():
    deleteUI() # Delete Existing UI if it exists.
    global _CHISEL_UI_INSTANCE
    if _CHISEL_UI_INSTANCE is None:
        maya_window = get_maya_main_window()        
        _CHISEL_UI_INSTANCE = ChiselUI(parent=maya_window)
        #_CHISEL_UI_INSTANCE.show(dockable=True, floating=True, area="right", allowedArea=["right", "left"])
        _CHISEL_UI_INSTANCE.show()
    else:
        _CHISEL_UI_INSTANCE.raise_()


class MainController:
    def __init__(self, view):
        self.view = view
        
        self.controls   = ControlsController(self.view)  # Control related functions.
        self.edit       = EditController(self.view)      # Edit or general related functions.
        self.component  = ComponentController(self.view) # Rig component related functions.
        self.surgery    = SurgeryController(self.view)   # Surgery related functions.
        self.filter     = FilterController(self.view)    # Filtering related functions.

class ControlsController:
    def __init__(self, view):
        self.view = view
        self.bind_view()

    def bind_view(self):
        
        connections = {


            # Control functions
            "btnCircle":     partial(self.press_create_control,ctrl_lib.Shapes.CIRCLE),
            "btnSquare":     partial(self.press_create_control,ctrl_lib.Shapes.SQUARE),
            "btnTriangle":   partial(self.press_create_control,ctrl_lib.Shapes.TRIANGLE),

            "btnArrow":      partial(self.press_create_control,ctrl_lib.Shapes.ARROW),
            "btnPin":        partial(self.press_create_control,ctrl_lib.Shapes.PIN),
            "btnCross":      partial(self.press_create_control,ctrl_lib.Shapes.CROSS),

            "btnCubeCN":     partial(self.press_create_control,ctrl_lib.Shapes.CUBE_CN),
            "btnCubeFk":     partial(self.press_create_control,ctrl_lib.Shapes.CUBE_FK),
            "btnSphere":     partial(self.press_create_control,ctrl_lib.Shapes.SPHERE),
            "btnOrient":     partial(self.press_create_control,ctrl_lib.Shapes.ORIENT_3D),
            "btnButton":     partial(self.press_create_control,ctrl_lib.Shapes.BUTTON),
            "btnRing":       partial(self.press_create_control,ctrl_lib.Shapes.RING),
            "btnButton":     partial(self.press_create_control,ctrl_lib.Shapes.BUTTON),
            "btnControlText":partial(self.press_create_control,ctrl_lib.Shapes.TEXT),
            "btnSlider":     partial(self.press_create_control,ctrl_lib.Shapes.SLIDER),
            "btnOsipa":      partial(self.press_create_control,ctrl_lib.Shapes.OSIPA),
            "btnSemiCircle": partial(self.press_create_control,ctrl_lib.Shapes.SEMI_CIRCLE),

            "BtnShapeOperationReplace": self.control_shape_replace,
            "BtnShapeOperarionCombine": self.control_shape_add,
            "BtnShapeOperationSwap":    self.control_shape_swap,
            "BtnShapeOperationCopy":    self.control_shape_copy,
            "BtnShapeOpereationMirror": self.control_shape_mirror,
            "BtnShapeResizePlus":       self.control_shape_size_down,
            "BtnShapeResizeMinus":      self.control_shape_size_up,
            "BtnShapeThick":            self.control_shape_thicken,
            "BtnShapeThin":             self.control_shape_thin,
            "BtnResetControl":          self.reset_controls,

            "BtnShapeColorRed":     partial(self.control_shape_color_index, ctrl_lib.ColorIndex.RED),
            "BtnShapeColorYellow":  partial(self.control_shape_color_index, ctrl_lib.ColorIndex.YELLOW),
            "BtnShapeColorBlue":    partial(self.control_shape_color_index, ctrl_lib.ColorIndex.BLUE),
            "BtnShapeColorPurple":  partial(self.control_shape_color_index, ctrl_lib.ColorIndex.PURPLE),
            "BtnShapeColorGreen":   partial(self.control_shape_color_index, ctrl_lib.ColorIndex.GREEN),

            
        }

        for button_name, method in connections.items():
            button = getattr(self.view, button_name, None)
            if button:
                button.clicked.connect(method)
            else:
                pm.warning(f"Button '{button_name}' not found in the view. Connection skipped.")

        
        connections = {
            "RdoControlConstrained": self.update_connect_checkboxes,
            "RdoControlDirectConnect": self.update_connect_checkboxes,
        }
        for button_name, method in connections.items():
            button = getattr(self.view, button_name, None)
            if button:
                button.stateChanged.connect(method)
    
    def update_connect_checkboxes(self):

        is_constrained = self.view.RdoControlConstrained.isChecked()   
        is_direct_connected = self.view.RdoControlDirectConnect.isChecked() 

        if is_constrained:
            self.view.RdoControlDirectConnect.setChecked(False)
        
        if is_direct_connected:
            self.view.RdoControlConstrained.setChecked(False)


    def _control_connection(self, control: ctrl_lib.Control, target= None):
        # Get Connection type from UI radio buttons.        
        is_constrained = self.view.RdoControlConstrained.isChecked()   
        is_direct_connected = self.view.RdoControlDirectConnect.isChecked() 

        if not is_constrained and not is_direct_connected:
            return None

        if is_constrained:
            pm.parentConstraint(control.transform, target, maintainOffset=True)
            pm.scaleConstraint(control.transform, target, maintainOffset=True)
            return
        
        
        if is_direct_connected:
            control.transform.translate >> target.translate
            control.transform.rotate >> target.rotate
            control.transform.scale >> target.scale

    def _control_offset(self, control: ctrl_lib.Control):
        is_root = self.view.chkControlCreationRoot.isChecked()   
        if is_root:
            control.create_offset("_root")

        is_offset = self.view.chkControlCreationOffset.isChecked()  
        if is_offset:
            control.create_offset("_offset")

    def _get_control_normal(self):
        normal_X = self.view.rdoControlOrientX.isChecked()
        normal_Y = self.view.rdoControlOrientY.isChecked()
        normal_Z = self.view.rdoControlOrientZ.isChecked()
        return (int(normal_X), int(normal_Y), int(normal_Z))

    @common.undo_chunk("Create Control")
    def press_create_control(self, creation_shape: ctrl_lib.Shapes):

        creation_parameters = {
            "control_type": creation_shape,
            "control_name": "",
            "normal": self._get_control_normal(),
        }

        print("### INSTANCE OF TEXT:", creation_shape is ctrl_lib.Shapes.TEXT)
        if creation_shape is ctrl_lib.Shapes.TEXT:
            text = self.view.TxtControlTextContent.text()
            creation_parameters["text"] = text

        selection = pm.selected()
        selection = maya_lib.sort_by_hierarchy(selection) or [creation_shape.value]
        
        controls = {}
        for index, obj in enumerate(selection):
            # Control creation.
            control_name = f"{obj}_ctrl" if obj != "_" else creation_shape.value
            creation_parameters["control_name"] = control_name
            control_instance = ctrl_lib.create_control(**creation_parameters)
            control_instance.align_to(obj)
            
            # Find parent control if exists.
            parent_object = maya_lib.find_first_ancestor(obj, selection[:index])
            parent_control = controls.get(parent_object, None) if parent_object else None
            if parent_control:
                control_instance.parent_to(parent_control.transform)

            self._control_offset(control_instance)
            self._control_connection(control_instance, target=obj)

            controls[obj] = control_instance 
        
        transform_curves = [ctrl.transform for ctrl in controls.values()]
        pm.select(transform_curves, replace=True)

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
        
        control = ctrl_lib.Control(destiny)
        control.shape_combine(*source)
        pm.delete(source)

    @common.undo_chunk("Swap Control Shape")
    def control_shape_swap(self):
        selected_objects = pm.selected()
        source = selected_objects[0]
        destiny = selected_objects[1:]
        
        source_instance = ctrl_lib.Control(source)
        for obj in destiny:
            copy = source_instance.copy()
            copy.align_to(obj)

            control = ctrl_lib.Control(obj)
            control.shape_replace(copy.transform)
            pm.delete(copy.transform)

        pm.select(destiny)
    
    @common.undo_chunk("Copy Control Shape")
    def control_shape_copy(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            control = ctrl_lib.Control(obj)
            control.copy()
        pm.select(selected_objects)

    @common.undo_chunk("Mirror Control Shape")
    def control_shape_mirror(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            control = ctrl_lib.Circle(obj)
            control.mirror()

    def _resize_control_shape(self, scale_factor):
        selected_controls = pm.selected()
        for obj in selected_controls:
            control = ctrl_lib.Circle(obj)
            control.shape_scale(scale_factor)

    @common.undo_chunk("Increase Control Shape Size")
    def control_shape_size_up(self):
        scale = 1.0
        scale = scale - float(self.view.TxtShapeResizeFactor.text() or 0.0)
        self._resize_control_shape([scale,scale,scale])

    @common.undo_chunk("Decrease Control Shape Size")
    def control_shape_size_down(self):
        scale = 1.0
        scale = scale + float(self.view.TxtShapeResizeFactor.text() or 0.0)
        self._resize_control_shape([scale,scale,scale])

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
    def control_shape_color_index(self, color_index: ctrl_lib.ColorIndex):        
        #color_index = ctrl_lib.ColorIndex.RED.value  # UI input.

        selected_controls = pm.selected()
        for obj in selected_controls:
            control = ctrl_lib.Control(obj)
            control.shape_color_index(color_index)

    @common.undo_chunk("Reset Controls")
    def reset_controls(self):
        selected_controls = pm.selected()
        if not selected_controls:
            pm.warning("No selection found.")
            return
        for obj in selected_controls:
            control = ctrl_lib.Circle(obj)
            control.reset()

class EditController:
    def __init__(self, view):
        self.view = view
        self.bind_view()

    def bind_view(self):
        
        connections = {
            "BtnFreezeTransform":   self.press_freeze_transformations,
            "BtnCleanHistory":      self.press_delete_history,
            "btnZeroOut":           self.press_create_offset_group,
            "BtnMoveOffset":        self.press_move_offset_group,
            
            "BtnAlignTransform":    self.press_align_many_to_one,
            "BtnMoveToSurface":     partial(self.press_align_with_mesh_surface, "move"),
            "BtnOrientToSurface":   partial(self.press_align_with_mesh_surface, "orient"),
            
            "BtnCreateLocator":     partial(self.press_create_at_selection, maya_lib.create_locator, "locator"),
            "BtnCreateJoint":       partial(self.press_create_at_selection, maya_lib.create_joint,   "joint"),
            "BtnCreateGroup":       partial(self.press_create_at_selection, maya_lib.create_group,   "group"),
            
            "BtnBuildHierarchy":    self.press_build_hierarchy
        }

        for button_name, method in connections.items():
            button = getattr(self.view, button_name, None)
            if button:
                button.clicked.connect(method)

    @common.undo_chunk("Freeze Transformations")    
    def press_freeze_transformations(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            maya_lib.freeze_transform(obj)

    @common.undo_chunk("Delete History")
    def press_delete_history(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            maya_lib.delete_history(obj)

    @common.undo_chunk("Create Offset Group")
    def press_create_offset_group(self):
        is_root = self.view.chkZeroOutRoot.isChecked()
        is_offset = self.view.chkZeroOutOffset.isChecked()

        selected_objects = pm.selected()
        for obj in selected_objects:
            if is_root:
                maya_lib.create_offset(obj, "_root")
            if is_offset:
                maya_lib.create_offset(obj, "_offset")
        pm.select(selected_objects)

    @common.undo_chunk("Move Offset Group")
    def press_move_offset_group(self):
        selected_objects = pm.selected()
        for obj in selected_objects:
            matrix = obj.getMatrix(ws=True)
            offset = obj.getParent()
            offset.setMatrix(matrix, ws=True)
            obj.setMatrix(matrix, ws=True)

    @common.undo_chunk("Align Many to One")
    def press_align_many_to_one(self):
        master, *slaves = pm.selected()
        if not common.is_transform(master):
            pm.warning(f"Master object '{master}' is not a transform. Alignment skipped.")
            return
        
        for slave in slaves:
            if not common.is_transform(slave):
                pm.warning(f"Slave object '{slave}' is not a transform. Alignment skipped.")
                continue
            maya_lib.align_transform(master, slave)

    @common.undo_chunk("Align with Mesh Surface")
    def press_align_with_mesh_surface(self, adjustment_type:str):
        mesh, *slaves = pm.selected()
        if not common.is_mesh(mesh):
            pm.warning(f"Mesh object '{mesh}' is not a mesh. Alignment skipped.")
            return

        for slave in slaves:
            if not common.is_transform(slave):
                continue
            if adjustment_type == "move":
                mesh_lib.move_to_mesh_surface(mesh, slave)
            elif adjustment_type == "orient":
                mesh_lib.orient_to_mesh_surface(mesh, slave)

    def _create_at_center(self, selected_objects, create_func, suffix, all_transform=False, all_components=False):
        created_node = create_func()
        if all_transform:    
            constraints = maya_lib.parent_constraint_many_to_one(*selected_objects, slave=created_node, maintain_offset=False)
            pm.delete(constraints)
        elif all_components:
            cluster = pm.cluster(selected_objects, n="temp_cluster")[1]
            maya_lib.align_transform(cluster, created_node)
            pm.delete(cluster)
        else:
            return
        created_node.rename(f"center_{suffix}")
        return created_node

    def _create_at_selection(self, selected_objects, create_func, suffix, all_transform=False, all_components=False):
        for obj in selected_objects:
            name = f"{obj.name()}_{suffix}"
            created_node = create_func(name)
            if common.is_transform(obj):
                print("### OBJ:", type(obj), "### CREATED NODE:", type(created_node))
                maya_lib.align_transform(obj, created_node)
            elif all_components:
                name = f"{obj.node().name()}_{suffix}"
                created_node.rename(name)
                matrix = pm.xform(obj, q=True, matrix=True, ws=True)
                pm.xform(created_node, matrix=matrix, ws=True)
            
    @common.undo_chunk("Create at Selection")
    def press_create_at_selection(self, create_func, suffix):        
        selected_objects = pm.selected()
        all_transform = all(common.is_transform(obj) for obj in selected_objects)
        all_components = all(common.is_component(obj) for obj in selected_objects)
        if not (all_transform or all_components):
            pm.warning("Selection must be all transforms or all components. Operation skipped.")
            return
        
        on_center = self.view.ChkCreateOnCenter.isChecked()
        creation_parameters = {
            "create_func": create_func,
            "suffix": suffix,
            "all_transform": all_transform,
            "all_components": all_components,
            }
        
        if on_center:
            self._create_at_center(selected_objects, **creation_parameters)
        else:
            self._create_at_selection(selected_objects, **creation_parameters)
        
    @common.undo_chunk("Build Hierarchy")
    def press_build_hierarchy(self):
        selected_objects = pm.selected()
        maya_lib.build_hierarchy_from_list(selected_objects)

class ComponentController:
    def __init__(self, view):
        self.view = view
        self.bind_view()

    def bind_view(self):
        connections = {
            # Template module functions
            "BtnCreateTemplate":       self.press_create_template,
            "btnAlignObject2Template": self.press_move_objects_to_templates,
            "btnAlignTemplate2Object": self.press_move_templates_to_objects,
            "btnTemplateAlignMid":     self.press_constraint_templates_to_midpoint,
            "btnTemplateAimTo":        self.press_orient_templates_to_template,
            # Ribbon module functions
            "btnCreateSurface":       self.press_create_surface,
            "BntCreateRibbon":        self.press_build_ribbon,
        }

        for button_name, method in connections.items():
            button = getattr(self.view, button_name, None)
            if button:
                button.clicked.connect(method)
            else:
                pm.warning(f"Button '{button_name}' not found in the view. Connection skipped.")
    
    # Template functions
    @common.undo_chunk("Create Templates")   
    def press_create_template(self):
        selected_objects = pm.selected()
        helpers.create_templates(selected_objects)

    @common.undo_chunk("Move Objects to Templates")
    def press_move_objects_to_templates(self):
        selected_objects = pm.selected()
        helpers.move_object_to_locator(selected_objects)

    @common.undo_chunk("Move Templates to Objects")
    def press_move_templates_to_objects(self):
        selected_objects = pm.selected()
        helpers.move_locator_to_object(selected_objects)
    
    @common.undo_chunk("Constraint Templates to Midpoint")
    def press_constraint_templates_to_midpoint(self):
        template_A, template_B, template_mid = pm.selected()
        helpers.constraint_to_midpoint(template_A, template_B, template_mid)

    @common.undo_chunk("Orient Templates to Template")
    def press_orient_templates_to_template(self):
        master_template, *slaves_templates = pm.selected()
        for slave in slaves_templates:
            helpers.aim_to(master_template, slave)

    # Ribbon functions
    @common.undo_chunk("Create Surface")
    def press_create_surface(self):
        selected_objects = pm.selected()
        surface = ribbon.Surface(name="surface")
        surface.create(joints=selected_objects, width=1.0, normal=ribbon.SurfaceOrient.Y_UP)

    @common.undo_chunk("Build Ribbon")
    def press_build_ribbon(self):
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

class SurgeryController:
    def __init__(self, view):
        self.view = view
        self.bind_view()

    def bind_view(self):
        
        connections = {
            "BtnConstraintDrivers": self.press_constraint_drivers,
            "BtnConstraintNodes":   self.press_constraint_nodes,
            "BtnConstraintRename":  self.press_constraint_rename,

            "BtnSkinningJoints":   self.press_skinning_joints,
            "BtnSkinningNodes":    self.press_skinning_nodes,
            "BtnSkinningRename":   self.press_skinning_rename,

            "BtnBlendshapeTargets":self.press_blendshape_targets,
            "BtnBlendshapeNodes":  self.press_blendshape_nodes,
            "BtnBlendshapeRename": self.press_blendshape_rename,

            "BtnConnectionInputs": self.press_connection_inputs,
            "BtnConnectionOutputs":self.press_connection_outputs,
            
            "BtnAxisVisible": self.press_axis_visible,
            "BtnAxisHide":    self.press_axis_hide,

            "BtnJointVisible":          self.press_joint_visible,
            "BtnJointHide":             self.press_joint_hide,
            "BtnJointIncreaseRadius":   self.press_joint_increase_radius,
            "BtnJointDecreaseRadius":   self.press_joint_decrease_radius,
            "BtnJointSetRadiusOne":     self.press_joint_set_radius_one,
            "BtnJointSetRadiusZero":    self.press_joint_set_radius_zero,

            "BtnDisplayNormal":     self.press_display_normal,
            "BtnDisplayTemplate":   self.press_display_template,
            "BtnDisplayReference":  self.press_display_reference,

            "BtnLockNodes":   self.press_lock_nodes,
            "BtnUnlockNodes": self.press_unlock_nodes,

            "BtnCleanUnused": self.press_clean_unused,
            "BtnCleanUnknown":self.press_clean_unknown
        }

        for button_name, method in connections.items():
            button = getattr(self.view, button_name, None)
            if button:
                button.clicked.connect(method)

    def press_constraint_drivers(self):
        selection = pm.selected()
        found_drivers = []
        for obj in selection:
            constraint_nodes = maya_lib.get_constraint_nodes(obj)
            for constraint in constraint_nodes:
                drivers = maya_lib.get_constraint_target(constraint)
                found_drivers.extend(drivers)
        pm.select(found_drivers, replace=True)

    def press_constraint_nodes(self):
        selection = pm.selected()
        found_constraints = []
        for obj in selection:
            constraint_nodes = maya_lib.get_constraint_nodes(obj)
            found_constraints.extend(constraint_nodes)
        pm.select(found_constraints, replace=True)

    def press_constraint_rename(self):
        selection = pm.selected()
        constraints_list =[]
        for obj in selection:
            if common.is_transform(obj):
                constraints = maya_lib.get_constraint_nodes(obj)
                constraints_list.extend(constraints)
            if common.is_constraint(obj):
                constraints_list.append(obj)
        
        for constraint in constraints_list:
            suffix = type(constraint).__name__
            new_name = f"{obj.name()}_{suffix}"
            constraint.rename(new_name)

    def press_skinning_joints(self):
        selection = pm.selected()
        found_joints = []
        for obj in selection:
            if not (common.is_mesh(obj) or common.is_nurbs_surface(obj)):
                continue

            shape = mesh_lib.get_render_shape(obj)
            skin_nodes = mesh_lib.get_skin_cluster_nodes(shape)
            for skin_node in skin_nodes:
                influences = mesh_lib.get_skin_cluster_influences(skin_node)
                found_joints.extend(influences)

        pm.select(found_joints, replace=True)

    def press_skinning_nodes(self):
        selection = pm.selected()
        found_skin_nodes = []
        for obj in selection:
            if not (common.is_mesh(obj) or common.is_nurbs_surface(obj)):
                continue

            shape = mesh_lib.get_render_shape(obj)
            skin_nodes = mesh_lib.get_skin_cluster_nodes(shape)
            if not skin_nodes:
                continue
            found_skin_nodes.extend(skin_nodes)
        pm.select(found_skin_nodes, replace=True)
    
    def press_skinning_rename(self):
        selection = pm.selected()
        for obj in selection:
            if not (common.is_mesh(obj) or common.is_nurbs_surface(obj)):
                continue

            shape = mesh_lib.get_render_shape(obj)
            skin_nodes = mesh_lib.get_skin_cluster_nodes(shape)
            if not skin_nodes:
                continue
            name = f"{obj.nodeName()}_skinCluster"
            [node.rename(name) for node in skin_nodes]

    def press_blendshape_targets(self):
        selection = pm.selected()
        found_targets = []
        for obj in selection:
            blendshape_nodes = mesh_lib.get_blend_shape_nodes(obj)
            for blendshape in blendshape_nodes:
                targets = mesh_lib.get_blend_shape_targets(blendshape)
                found_targets.extend(targets)
        pm.select(found_targets, replace=True)

    def press_blendshape_nodes(self):
        selection = pm.selected()
        found_blendshape_nodes = []
        for obj in selection:            
            blendshape_nodes = mesh_lib.get_blend_shape_nodes(obj)
            found_blendshape_nodes.extend(blendshape_nodes)
        pm.select(found_blendshape_nodes, replace=True)

    def press_blendshape_rename(self):
        selection = pm.selected()
        for obj in selection:
            blendshape_nodes = mesh_lib.get_blend_shape_nodes(obj)
            name = f"{obj.name()}_blendShape"
            [node.rename(name) for node in blendshape_nodes]

    def press_connection_inputs(self):
        selection = pm.selected()
        found_inputs = []
        for obj in selection:
            connections = maya_lib.get_input_nodes(obj)
            found_inputs.extend(connections)
        pm.select(found_inputs, replace=True)
    
    def press_connection_outputs(self):
        selection = pm.selected()
        found_outputs = []
        for obj in selection:
            connections = maya_lib.get_output_nodes(obj)
            found_outputs.extend(connections)
        pm.select(found_outputs, replace=True)

    def press_axis_visible(self):
        selection = pm.selected()
        for obj in selection:
            if not common.is_transform(obj):
                continue
            maya_lib.show_axis(obj)
    
    def press_axis_hide(self):
        selection = pm.selected() or pm.ls(type=pm.nt.Transform)
        for obj in selection:
            if not common.is_transform(obj):
                continue
            maya_lib.hide_axis(obj)

    def press_joint_visible(self):
        selection = pm.selected()
        for obj in selection:
            if not common.is_joint(obj):
                continue
            maya_lib.show_joint(obj)
    
    def press_joint_hide(self):
        selection = pm.selected() or pm.ls(type=pm.nt.Joint)
        for obj in selection:
            if not common.is_joint(obj):
                continue
            maya_lib.hide_joint(obj)
        
    def press_joint_increase_radius(self):
        selection = pm.selected()
        for obj in selection:
            if not common.is_joint(obj):
                continue
            maya_lib.increase_joint_radius(obj, 0.1)

    def press_joint_decrease_radius(self):
        selection = pm.selected()
        for obj in selection:
            if not common.is_joint(obj):
                continue
            maya_lib.decrease_joint_radius(obj, 0.1)

    def press_joint_set_radius_one(self):
        selection = pm.selected()
        for obj in selection:
            if not common.is_joint(obj):
                continue
            obj.radius.set(1.0)
    
    def press_joint_set_radius_zero(self):
        selection = pm.selected()
        for obj in selection:
            if not common.is_joint(obj):
                continue
            obj.radius.set(0.0)

    def press_display_normal(self):
        selection = pm.selected()
        for obj in selection:
            if not common.is_transform(obj):
                continue
            maya_lib.set_display_normal(obj)

    def press_display_template(self):
        selection = pm.selected()
        for obj in selection:
            if not common.is_transform(obj):
                continue
            maya_lib.set_display_template(obj)
    
    def press_display_reference(self):
        selection = pm.selected()
        for obj in selection:
            if not common.is_transform(obj):
                continue
            maya_lib.set_display_reference(obj)

    def press_lock_nodes(self):
        selection = pm.selected()
        for obj in selection:
            maya_lib.lock_node(obj)

    def press_unlock_nodes(self):
        selection = pm.selected()
        for obj in selection:
            maya_lib.unlock_node(obj)

    def press_clean_unused(self):
        maya_lib.clean_unused_nodes()
    
    def press_clean_unknown(self):
        maya_lib.delete_unknown_nodes()

class FilterController:
    def __init__(self, view):
        self.view = view
        self.bind_view()

    def bind_view(self):
        connections = {
            "btnFilterJoints":  self.press_filter_joints,
            "btnFilterLocators":self.press_filter_locators,
            "btnFilterMeshes":  self.press_filter_meshes,
            "btnFilterNurbs":   self.press_filter_nurbs,
            "btnFilterLeaves":  self.press_filter_leaves,
        }

        for button_name, method in connections.items():
            button = getattr(self.view, button_name, None)
            if button:
                button.clicked.connect(method)

    def _is_filter_out(self):
        is_filter_out = self.view.RdoFilterOut.isChecked()
        return is_filter_out
    
    def press_filter_joints(self):
        is_filter_out = self._is_filter_out()
        selection = pm.selected()
        if is_filter_out:
            filtered = common.filter_out_joints(selection)
        else:
            filtered = common.filter_joints(selection)
        pm.select(filtered, replace=True)

    def press_filter_locators(self):
        is_filter_out = self._is_filter_out()
        selection = pm.selected()
        if is_filter_out:
            filtered = common.filter_out_locators(selection)
        else:
            filtered = common.filter_locators(selection)
        pm.select(filtered, replace=True)

    def press_filter_meshes(self):
        is_filter_out = self._is_filter_out()
        selection = pm.selected()
        if is_filter_out:
            filtered = common.filter_out_meshes(selection)
        else:
            filtered = common.filter_meshes(selection)
        pm.select(filtered, replace=True)

    def press_filter_nurbs(self):
        is_filter_out = self._is_filter_out()
        selection = pm.selected()
        if is_filter_out:
            filtered = common.filter_out_nurbs_curves(selection)
        else:
            filtered = common.filter_nurbs_curves(selection)
        pm.select(filtered, replace=True)

    def press_filter_leaves(self):
        is_filter_out = self._is_filter_out()
        selection = pm.selected()
        if is_filter_out:
            filtered = common.get_no_leaf_nodes(selection)
        else:
            filtered = common.get_leaf_nodes(selection)
        pm.select(filtered, replace=True)


