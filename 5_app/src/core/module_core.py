import pymel.core as pm
import pymel.core.nodetypes as nt
from ..library.common import Sufix

class ModuleIndex:
    jointsGroup = "jntGrp"
    controlGroup = "ctrlGrp"
    jointsResultGroup = "jointsResult"

class ModuleBase(object):
    def __init__(self, controls=None, joints=None, jointsResult=None, constraints=None):
        self.controls = None
        self.joints = None
        self.constraints = None

        #self.mapBase(controls, joints, jointsResult,  constraints)

    def mapBase(self, constrols=None, joints=None, constraints=None):
        self.controls = constrols
        self.joints = joints
        self.constraints = constraints

    def castModule(self, moduleGrp):
        self.controls= moduleGrp.ctrlGrp.listRelatives(allDescendents=True, type="nurbsCurve")
        self.joints = moduleGrp.jointsGrp.listRelatives(allDescendents=True, type="joint")
        self.constraints = moduleGrp.jointsGrp.listRelatives(allDescendents=True, type="constraint")

        self.controls.reverse()
        self.joints.reverse()
        self.constraints.reverse()


class Module(ModuleBase):
    def __init__(self, prefix="Module"):
        ModuleBase.__init__(self)
        self.module = None
        self.bodyAttach = None
        self.jntGrp = None
        self.ctrlGrp = None
        self.noTouch = None
        self.prefix = None
        self.subModule = None

        self.createModule(prefix)

    def createModule(self, prefix):
        self.prefix = prefix
        self.module = pm.group(n=prefix + Sufix.module, em=True)
        # self.subModule  = pm.group(n=prefix + "_subModule",   em=True, p=self.module)
        #self.bodyAttach = pm.group(n=prefix + Sufix.bodyAttach, em=True, p=self.module)
        # self.ctrlGrp    = pm.group(n= prefix + "_ctrlGrp",    em=True, p= self.module)
        # self.jntGrp     = pm.group(n= prefix + "_jntGrp",     em=True, p= self.module)
        # self.noTouch    = pm.group(n= prefix + "_doNotTouch", em=True, p= self.module)

        # pm.setAttr( self.noTouch    + '.it', 0, l=True )
        # pm.setAttr( self.jntGrp + '.it', 0, l=True )
        # pm.hide( self.jntGrp, self.noTouch )

    def castModule(self, moduleGrp):
        if moduleGrp and moduleGrp.name().endswith(Sufix.module):
            self.module = moduleGrp
            self.prefix = self.module.name().replace(Sufix.module, "")

            children= self.module.getChildren()
            if children:
                for child in children:
                    if child.name().endswith(Sufix.controlGroup):
                        self.ctrlGrp = child
                    elif child.name().endswith(Sufix.jointGroup):
                        self.jntGrp = child
                    elif child.name().endswith(Sufix.noTouch):
                        self.noTouch = child
                    elif child.name().endswith(Sufix.bodyAttach):
                        self.bodyAttach = child
                    elif child.name().endswith(Sufix.subModule):
                        self.subModule = child

    def setBasicGroups(self, controls=None, joints=None):
        if not self.ctrlGrp and controls:
            self.ctrlGrp = pm.group(n=self.prefix + Sufix.controlGroup, em=True, p=self.module)
        if not self.jntGrp and joints:
            self.jntGrp = pm.group(n=self.prefix + Sufix.jointGroup, em=True, p=self.module)
            #pm.setAttr(self.jntGrp + '.it', 0, l=True)
            pm.hide(self.jntGrp)

        if type(controls) != bool and controls:
            pm.parent(controls, self.ctrlGrp)
        if type(joints) != bool and joints:
            pm.parent(joints, self.jntGrp)

    def setNoTouch(self, *elements):
        if not self.noTouch:
            self.noTouch = pm.group(n=self.prefix + Sufix.noTouch, em=True, p=self.module)
        pm.setAttr(self.noTouch + '.it', 0, l=True)
        pm.hide(self.noTouch)

        for obj in elements:
            pm.parent(obj, self.noTouch)

    def setSubModule(self, newSubModule):
        if not self.subModule:
            self.subModule = pm.group(n=self.prefix + Sufix.subModule, em=True, p=self.module)
        pm.parent(newSubModule, self.subModule)

    def setBodyAttach(self, attachTo=None):
        if not self.bodyAttach:
            self.bodyAttach = pm.group(n=self.prefix + Sufix.bodyAttach, em=True, p=self.module)
        if type(attachTo) != bool and attachTo:
            pm.parentConstraint(attachTo, self.bodyAttach, mo=True)
            pm.scaleConstraint(attachTo, self.bodyAttach, mo=True)

    def setMeshGroup(self, mesh):
        if mesh:
            self.meshGrp = pm.group(n=self.prefix + Sufix.meshGrp, em=True, p=self.module)
        if type(mesh) != bool and mesh:
            pm.parent(mesh, self.meshGrp)