'''
################################################################################################################
Author: Francisco Guzmán

Content: Rigging module for the limb.
Dependency: pymel.core
Maya Version tested: 2024

How to:
    - Use: Instructions to use the module
    - Test: Instructions to test the module

TODO: IMPLEMENT.
################################################################################################################
'''


import pymel.core as pm
from src.core.control_lib import Circle, Vector
from src.utility.transform_utils import is_ancestor

class Limb(RigModule):
    def create_joints(self, quantity=5):
        parent = None
        length = len(str(quantity + 1)) + 1
        self.joints = []
        for i in range(quantity):

            jnt = pm.joint(parent, n=f"{self.name}_{str(i + 1).zfill(length)}")
            if parent:
                jnt.tx.set(1)
            parent = jnt
            self.joints.append(jnt)


class FK(Limb):
    def __init__(self, name: str, joints=[]):
        super().__init__(name)
        self.joints = joints

    def create_controls(self, references: pm.nt.Transform, normal: Vector, use_offset: bool) -> list[Control]:
        control_suffix = "_ctrl"

        # Sort objects by hierarchy depth.
        objects = sorted(references, key= lambda obj: obj.name(long=True))

        for obj_index in range(len(objects)):
            obj = objects[obj_index]

            # Control creation.
            control_name = f"{obj}{control_suffix}"
            control = Circle()
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
            if use_offset:
                control.create_offset("_offset")

    def build(self):
        controls = []
        for joint in self.joints:
            ###     MAIN CONTROL.
            control = Circle(joint.name(), normal=[1, 0, 0], reference=joint)
            control.create()
            control.constrain(target=joint)
            controls.append(control)

            """###     DETAIL CONTROL.
            detail = Circle(f"{joint.name()}_detail", normal=[1,0,0], reference=control.transform, scale=[.8,.8,.8])
            detail.create()
            detail.constrain(target=joint)
            pm.parent(detail.transform, control.transform)"""

        aux = [control.transform for control in controls]
        self.controls = aux
        [control.reparent() for control in controls]

        root_control = []
        [root_control.append(control) for control in controls if not control.parent]

        ###     SORT COMPONENTS     ###
        super().build()
        [pm.parent(control.transform, self.group_visible) for control in root_control]
        [control.set_root() for control in controls]


class IK(Limb):
    def __init__(self, name: str, joints=[]):
        super().__init__(name)
        self.joints = joints

    def get_poleVector(self):
        start, mid, end = self.joints
        locator = pm.spaceLocator()
        pm.pointConstraint(start, end, locator)
        pm.aimConstraint(start, locator, aimVector=[1, 0, 0], upVector=[0, 1, 0], worldUpType="object",
                         worldUpObject=mid)

        locator_2 = pm.spaceLocator()
        pm.parent(locator_2, locator)
        locator_2.t.set([0, 0, 0])
        locator_2.r.set([0, 0, 0])
        pm.pointConstraint(mid, locator_2, skip=["y", "z"])
        pole = pm.spaceLocator()
        pm.parent(pole, locator_2)
        pole.setMatrix(locator_2.getMatrix(ws=True), ws=True)
        distance = start.getTranslation(ws=True).distanceTo(end.getTranslation(ws=True))
        pole.ty.set(distance)

        control = Circle(f"{self.name}_poleVector", [0, 1, 0], pole, [.3, .3, .3])
        control.create()
        pm.delete(locator, locator_2, pole)
        return control

    def build(self):
        ####    CREATE IK HANDLE    ###
        ikHandle = pm.ikHandle(sj=self.joints[0], ee=self.joints[-1], s="rotatePlane", solver="ikRPsolver")[0]
        ikHandle.rename(self.name + "_ikHandle")
        pm.hide(ikHandle)

        ###     CREATE POLE VECTOR  ###
        poleVector = self.get_poleVector()
        pm.poleVectorConstraint(poleVector.transform, ikHandle)

        ###     CREATE CONTROLS     ###
        control_root = Circle(self.joints[0], reference=self.joints[0], is_constrained=True)
        control_leaf = Circle(self.joints[-1], reference=self.joints[-1], is_constrained=False)

        control_root.create()
        control_leaf.create()
        control_leaf.constrain(ikHandle)

        self.controls.append(control_root.transform)
        self.controls.append(control_leaf.transform)
        self.controls.append(poleVector.transform)

        ###     SORT PIECES     ###
        super().build()
        pm.parent(control_root.transform, control_leaf.transform, poleVector.transform, self.group_visible)
        pm.parent(ikHandle, self.group_hidden)
        control_root.set_root()
        control_leaf.set_root()
        poleVector.set_root()


class Appendage(Limb):
    def __init__(self, name: str, joints=[], quantity=5):
        super().__init__(name)
        self.joints = joints
        self.quantity = quantity

    def build(self):
        tail_fk = FK(self.name, self.joints)
        if not self.joints:
            tail_fk.create_joints(self.quantity)
        tail_fk.build()

        surface = Surface(self.name)
        surface.create(tail_fk.joints, 0.5, [0, 0, 1])

        ribbon = Ribbon(self.name, surface.transform, 1, surface.spans + 1)
        ribbon.build()

        for ctrl in ribbon.controls:
            control = Control(ctrl)
            control.scale([.6, .6, .6])

        for control_fk, control_ribbon in zip(tail_fk.controls, ribbon.controls):
            detail = Control(control_fk)
            rb = Control(control_ribbon)
            rb.set_offset()

            pm.parentConstraint(detail.transform, rb.offset, mo=True)
            pm.scaleConstraint(detail.transform, rb.offset, mo=True)



class IkSpline(Limb):
    def __init__(self, name: str, joints=[], n_controls=0):
        super().__init__(name)
        self.joints = joints

        self.curve = None
        self.n_controls = n_controls

    def create_curve(self):
        points = [pm.xform(point, q=True, t=True, ws=True) for point in self.joints]
        curve = pm.curve(p=points, d=3, n=self.name + "_crv")
        self.curve = curve

    def rebuild_curve(self):
        pm.rebuildCurve(self.curve, rpo=1, rt=0, end=1, kr=0, kep=1, kt=0, s=self.n_joints, d=3, tol=0.01)

    def build(self):
        self.create_curve()
        drivers = []
        cvs = pm.ls(self.curve + ".cv[*]", fl=True)
        for cv in cvs:
            control = Circle(self.name, normal=[1, 0, 0])
            control.create()
            pos = pm.xform(cv, q=True, t=True, ws=True)
            pm.xform(control.transform, t=pos, ws=True)

            driver = pm.joint(None, n=joint.name() + "_drv")
            driver.setMatrix(control.transform.getMatrix(ws=True), ws=True)
            drivers.append(driver)

            control.constrain(driver)
            self.controls.append(control.transform)

        pm.skinCluster(self.curve, drivers)

        ikHandle = pm.ikHandle(sj=self.joints[0], ee=self.joints[-1], c=self.curve, sol="ikSplineSolver", ccv=False,
                               tws="easeInOut", pcv=False)[0]
        ikHandle.rename(self.name + "_ikHandle")

        ###     SORT COMPONENTS     ###
        super().build()

        pm.parent(self.controls, self.group_visible)
        pm.parent(self.curve, ikHandle, drivers, self.group_hidden)
