'''
################################################################################################################
Author: Francisco Guzmán

Content: Core functions to build a Ribbon module.
Dependency: pymel.core
Maya Version tested: 2024

How to:
    - Use:  TODO
    - Test: TODO

TODO: Split, clean and refactor code.
################################################################################################################
'''


import pymel.core as pm



class FakeNode:
    def __init__(self, n, name):
        self.name = n

    def name(self):
        return self.name


class MayaBackend:
    ########    OBJECT CREATION         ########
    @staticmethod
    def create_transform(name=None, parent=None):
        transform = pm.nt.Transform(n=name) if name else pm.group(em=True)
        if parent:
            pm.parent(transform, parent)
        return transform

    @staticmethod
    def create_joint(name=None, parent=None, position=None):
        joint = pm.joint(None, p=position or (0, 0, 0), n=name)
        if parent:
            pm.parent(joint, parent)
        return joint

    @staticmethod
    def create_control_curve(name, shape="circle", points=None, normal=(1, 0, 0), radius=1.0):
        if shape == "circle":
            return pm.circle(n=name, normal=normal, r=radius, ch=False)[0]
        elif shape == "custom" and points:
            return pm.curve(p=points, d=3, n=name)
        raise ValueError(f"Shape {shape} not supported")

    @staticmethod
    def decompose_matrix(source_matrix_attr):
        node = pm.nt.DecomposeMatrix()
        source_matrix_attr >> node.inputMatrix
        return node

    @staticmethod
    def blend_matrix(weights=None, name="blendMatrix", *inputs):
        node = pm.nt.BlendMatrix(n=name)
        for i, input in enumerate(inputs):
            input >> node.target[i].targetMatrix
            if weights:
                node.target[i].weight.set(weights[i])
        return node

    @staticmethod
    def create_follicle(name):
        fol_shape = pm.nt.Follicle(n=name)
        fol_shape.simulationMethod.set(0)
        transform_node = fol_shape.getParent()
        transform_node.rename(name)

        fol_shape.outTranslate >> transform_node.t
        fol_shape.outRotate >> transform_node.r

        return transform_node

    @staticmethod
    def create_rivet(name, surface, position_object):
        follicle = MayaBackend.createFollicle(name)

        decompose = pm.nt.DecomposeMatrix()
        position_object.worldMatrix >> decompose.inputMatrix

        if isinstance(surface.getShape(), pm.nt.Mesh):
            closest = pm.nt.ClosestPointOnMesh()
            surface.getShape().worldMesh >> closest.inMesh
            surface.getShape().worldMesh >> fol_shape.inputMesh

        elif isinstance(surface.getShape(), pm.nt.NurbsSurface):
            closest = pm.nt.ClosestPointOnSurface()
            surface.getShape().worldSpace >> closest.inputSurface
            surface.getShape().worldSpace >> fol_shape.inputSurface

        decompose.outputTranslate >> closest.inPosition
        follicle.parameterU.set(closest.parameterU.get())
        follicle.parameterV.set(closest.parameterV.get())

        pm.delete(closest, decompose)
        return follicle

    ########    OBJECT CONNECTIONS      ########
    @staticmethod
    def connect(source_attr, target_attr):
        source_attr >> target_attr

    @staticmethod
    def set_matrix(node, matrix, ws=True):
        node.setMatrix(matrix, ws=ws)

    @staticmethod
    def get_matrix(node, ws=True):
        return node.getMatrix(ws=ws)

    @staticmethod
    def parent_constraint(master, slave, mo=True):
        return pm.parentConstraint(master, slave, mo=mo)

    @staticmethod
    def scale_constraint(master, slave, mo=True):
        return pm.scaleConstraint(master, slave, mo=mo)

    @staticmethod
    def orient_constraint(master, slave, mo=True):
        return pm.orientConstraint(master, slave, mo=mo)

    ########    OBJECT EDITION      ########
    @staticmethod
    def rebuild_surface(surface, spans):
        pm.rebuildSurface(surface, du=3, dir=0, su=spans)
        pm.select(surface)
        pm.mel.eval('doBakeNonDefHistory( 1, {"prePost" });')

    @staticmethod
    def build_hierarchy(*objects):
        for i, obj in enumerate(objects):
            if i > 0:
                pm.parent(obj, objects[i - 1])


def check_types(var_name, expected_type, *vars):
    """
    Verifies that all given variables match the expected type.

    This function checks whether each element in *vars is an instance of the type
    specified in expected_type. If any value doesn't match, a TypeError is raised
    with a detailed error message.

    Parameters:
    -----------
    var_name : str
        The name of the variable being checked, used in the error message.

    expected_type : type or tuple of types
        The expected type for the variables, or a tuple of allowed types. If a variable does
        not match any of the specified types, an error will be raised.

    *vars : variables
        The variables whose types will be checked. These can be of any type.

    Exceptions:
    -----------
    TypeError
        If any of the variables is not an instance of the expected type, a TypeError will be raised
        with a message indicating the expected type and the actual type of the mismatched variable.

    Example:
    --------
    check_types("number", (int, float), 10, 3.5)  # No exception raised
    check_types("number", (int, float), 10, "text")  # Raises TypeError
    """
    for v in vars:
        if not isinstance(v, expected_type):
            raise TypeError(
                f"{var_name} expected {expected_type}, but got {type(v)}."
            )


def rebuildSurface(surface, spans):
    bc.rebuild_surface(surface, spans)


def create_rivet(surface, position_object):
    bc.create_rivet(position_object.name(), surface, position_object)


def build_hierarchy(*objects):
    bc.build_hierarchy(*objects)


def tie_offset(master, slave, ws=True, mo=True):
    check_types("In tie_offset", pm.nt.Transform, master, slave)
    attr = master.worldMatrix if ws == True else master.matrix
    matrix = slave.getMatrix(ws=True)

    attr >> slave.offsetParentMatrix
    if mo:
        slave.setMatrix(matrix, ws=True)


def constrain(master, *slaves):
    constrains = []
    for slave in slaves:
        parent = bc.parent_constraint(master, slave, mo=True)
        scale = bc.scale_constraint(master, slave, mo=True)

        constrains.append((parent, scale))
    return constrains


def create_blendMatrix(master, ws=True, *weights):
    check_types("In Create_blendMatrix", pm.nt.Transform, master, *weights)

    name = master.name()
    blend_matrix = pm.nt.BlendMatrix(n=f"{name}_blendMatrix")
    matrix_at = master.worldMatrix if ws else master.matrix
    matrix_at >> blend_matrix.inputMatrix
    influence = 1 / (len(weights) + 1) if len(weights) > 0 else 0
    for i, weight in enumerate(weights):
        weight.worldMatrix >> blend_matrix.target[i].targetMatrix
        blend_matrix.target[i].weight.set(influence)
    return blend_matrix


def create_reverse(input, *outputs):
    check_types("Input in create reverse", pm.Attribute, input, *outputs)

    name = input.name()
    reverse = pm.nt.Reverse(n=f"{name}_reverse")
    input >> reverse.inputX
    for output in outputs:
        reverse.outputX >> output
    return reverse


def align_to(master, *slaves):
    check_types("In align_to ", pm.nt.Transform, master, *slaves)
    for slave in slaves:
        slave.setMatrix(master.getMatrix(ws=True), ws=True)


class Surface:
    def __init__(self, arg=None):
        self.name = f"{arg}"
        self.cast()

        self.get_spans()

    def cast(self):
        try:
            self.transform = pm.nt.Transform(self.name)
            self.shape = self.transform.getShape()
        except:
            self.transform = None
            self.shape = None

    def create_curve(self, width=1.0, normal=[0, 1, 0]):
        pos = width / 2.0
        points_vt = pm.dt.Vector([pos, pos, pos])
        normal_vt = pm.dt.Vector(normal)
        point_A = [points_vt.x * normal_vt.x, points_vt.y * normal_vt.y, points_vt.z * normal_vt.z]
        point_B = [points_vt.x * normal_vt.x * -1, points_vt.y * normal_vt.y * -1, points_vt.z * normal_vt.z * -1]

        crv = pm.curve(point=[point_A, point_B], d=1)
        return crv

    def create(self, joints, width=1.0, normal=[0, 1, 0]):
        if self.transform:
            return None
        crvs = []
        for joint in joints:
            crv = self.create_curve(width, normal)
            crv.setMatrix(joint.getMatrix(ws=True), ws=True)
            crvs.append(crv)
        surface = pm.loft(crvs, n=self.name)[0]
        pm.delete(crvs)
        self.transform = surface
        self.get_spans()

    def get_spans(self):
        if self.transform:
            self.spans = self.transform.numSpansInU()
        else:
            self.spans = 0

    def rebuild(self, spans):
        pm.rebuildSurface(self.transform, du=3, dir=0, su=spans)
        pm.select(self.transform)
        pm.mel.eval('doBakeNonDefHistory( 1, {"prePost" });')


class Rig:
    def __init__(self, name=""):
        self.name_main = f"{name}_rig"
        self.name_geometry = "Geometry"
        self.name_rig_modules = "rig_modules"
        self.name_visible_modules = "visible_modules"
        self.name_hidden_modules = "hidden_modules"
        self.name_set = f"{self.name_main}_sets"

        self.group_main = self.create_internal_group(self.name_main, None)
        self.group_geometry = self.create_internal_group(self.name_geometry, self.group_main)
        self.group_rig_modules = self.create_internal_group(self.name_rig_modules, self.group_main)
        self.group_visible_modules = self.create_internal_group(self.name_visible_modules, self.group_rig_modules)
        self.group_hidden_modules = self.create_internal_group(self.name_hidden_modules, self.group_rig_modules)

        self.set = self.create_rig_set(self.name_set)

        self.visible_modules = []
        self.hidden_modules = []

    def create_internal_group(self, name, parent):
        group = pm.nt.Transform(name) if pm.objExists(name) else pm.nt.Transform(n=name)
        pm.parent(group, parent)
        return group

    def create_rig_set(self, name):
        return pm.nt.ObjectSet(self.name_set) if pm.objExists(self.name_set) else pm.nt.ObjectSet(n=self.name_set)

    def add_visible_module(self, module_grp):
        pm.parent(module_grp, self.group_visible_modules)

    def add_hidden_module(self, module_grp):
        pm.parent(module_grp, self.group_hidden_modules)


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


class Control:
    def __init__(self, name: str, normal=[1, 0, 0], reference=None, scale=[1, 1, 1], is_constrained=False):
        self.name = ""
        self.root = None
        self.offset = None
        self.transform = None
        self.shapes = None

        self.cast(name)

        self.normal = pm.dt.Vector(normal)
        self.size = pm.dt.Vector(scale)
        self.reference = reference
        self.parent = self.reference.getParent().name() + "_ctrl" if self.reference and self.reference.getParent() else ""
        self.is_constrained = is_constrained

    def cast(self, name):
        try:
            self.transform = pm.nt.Transform(name)
            if not isinstance(self.transform.getShape(), pm.nt.NurbsCurve):
                raise Exception()
            self.name = self.transform.name()

            self.shapes = self.transform.getShapes()
            self.root = pm.nt.Transform(self.name + "_root") if pm.objExists(self.name + "_root") else None
            self.offset = pm.nt.Transform(self.name + "_offset") if pm.objExists(self.name + "_offset") else None

            if self.root:
                self.parent = self.root.getParent()
            elif self.offset:
                self.parent = self.offset.getParent()
            else:
                self.parent = self.transform.getParent()
        except:
            self.transform = None
            self.name = f"{name}_ctrl"
            self.shapes = None
            self.root = None
            self.offset = None

    def zeroOut(self, name):
        new_name = f"{self.transform.name()}_{name}"
        if pm.objExists(new_name):
            return pm.nt.Transform(new_name)

        group = pm.nt.Transform(n=new_name)
        group.setMatrix(self.transform.getMatrix(ws=True), ws=True)
        pm.parent(group, self.transform.getParent())
        pm.parent(self.transform, group)
        return group

    def set_root(self):
        self.root = self.zeroOut("root")
        return self.root

    def set_offset(self):
        self.offset = self.zeroOut("offset")
        return self.offset

    def create(self):
        self.shapes = self.transform.getShapes()
        self.scale(self.size)

        if self.reference:
            self.transform.setMatrix(self.reference.getMatrix(ws=True), ws=True)

        if self.is_constrained:
            self.constrain(self.reference)

    def constrain(self, target):
        pm.parentConstraint(self.transform, target, mo=True)
        pm.scaleConstraint(self.transform, target, mo=True)

    def scale(self, scale=[1, 1, 1]):
        cvs = [pm.ls(shape + ".cv[*]", fl=True) for shape in self.shapes]
        pm.xform(cvs, scale=scale, r=True)

    def rotate(self, angle=(0, 0, 0)):
        cvs = [pm.ls(shape + ".cv[*]", fl=True) for shape in self.shapes]
        pm.xform(cvs, ro=angle, r=True)

    def translate(self, angle=(0, 0, 0)):
        cvs = [pm.ls(shape + ".cv[*]", fl=True) for shape in self.shapes]
        pm.xform(cvs, t=angle, r=True)

    def reparent(self):
        if self.offset:
            pm.parent(self.transform, self.offset)
        elif self.root:
            pm.parent(self.transform, self.root)
        elif self.parent:
            pm.parent(self.transform, self.parent)

    def thick(self):
        for shape in self.shapes:
            shape.lineWidth.set(2)

    def color(self, index=None, rgb=None):
        """
        Colors control shapes using either an RGB value or a Maya color index.

        If `rgb` is provided, it overrides the shape color using RGB values (0.0 to 1.0).
        If `rgb` is not provided, the shape will use the given Maya color index.

        Args:
            index (int, optional): Maya color index (used if `rgb` is not given).
            rgb (tuple[float, float, float], optional): RGB color values in the range [0.0, 1.0].

        Returns:
            None
        """
        for shape in self.shapes:
            if rgb:
                shape.ovrbg.set(1)
                shape.ovrgbc.set(rgb)
            else:
                shape.ove.set(1)
                shape.ovc.set(index)

    def yellow(self):
        self.color(17)

    def red(self):
        self.color(13)

    def blue(self):
        self.color(6)


class Circle(Control):
    def create(self):
        if not self.transform:
            self.transform = pm.circle(n=self.name, normal=self.normal, ch=False)[0]

            super().create()


class Semicircle(Circle):
    def __init__(self, name: str, normal=[1, 0, 0], reference=None, scale=[1, 1, 1], is_constrained=False):
        super().__init__(name, normal, reference, scale, is_constrained)

    def create(self):
        super().create()

        cvs = pm.ls(self.transform + ".cv[*]", fl=True)

        # self.rotate([-90,0,0])
        if self.normal == pm.dt.Vector(1, 0, 0):
            pm.xform(cvs[4:7], s=[1, 0, 1])
        elif self.normal == pm.dt.Vector(0, 1, 0):
            # self.rotate([0,90,0])
            pm.xform(cvs[4:7], s=[1, 1, 0])
        elif self.normal == pm.dt.Vector(0, 0, 1):
            self.rotate([0, 0, 90])
            pm.xform(cvs[2:5], s=[1, 0, 1])


class Sphere(Control):
    def __init__(self, name: str, normal=[1, 0, 0], reference=None, scale=[1, 1, 1], is_constrained=False):
        super().__init__(name, normal, reference, scale, is_constrained)
        self.create()

    def create(self):
        if not self.transform:
            points = [[0.0, 0.0, 1.000750770419927],
                      [-4.6656110086473745e-09, -0.15655193766544784, 0.9884298898051642],
                      [-9.216338803241797e-09, -0.30924903323204056, 0.951770565130279],
                      [-1.354012990617548e-08, -0.45433142134880455, 0.8916754706773912],
                      [-1.753051659392213e-08, -0.5882265954118875, 0.809624388617307],
                      [-2.108924501698084e-08, -0.7076377035802839, 0.7076376439308896],
                      [-2.4128686604285576e-08, -0.8096245079160962, 0.588226535762493],
                      [-2.6573999889478728e-08, -0.8916755899761792, 0.4543313616994111],
                      [-2.8364973481131983e-08, -0.9517706844290679, 0.30924897358264647],
                      [-2.9457506656171972e-08, -0.9884300091039524, 0.1565518183666596],
                      [-2.98246973784444e-08, -1.0007508897187165, 0.0],
                      [-2.9457506656171972e-08, -0.9884300091039524, -0.1565518183666596],
                      [-2.8364973481131983e-08, -0.9517706844290679, -0.30924897358264647],
                      [-2.6573999889478728e-08, -0.8916755899761792, -0.4543313616994111],
                      [-2.4128686604285576e-08, -0.8096245079160962, -0.588226535762493],
                      [-2.108924501698084e-08, -0.7076377035802839, -0.7076376439308896],
                      [-1.753051659392213e-08, -0.5882265954118875, -0.809624388617307],
                      [-1.354012990617548e-08, -0.45433142134880633, -0.8916754706773912],
                      [-9.216338803241797e-09, -0.30924903323204056, -0.951770565130279],
                      [-4.6656110086473745e-09, -0.15655193766544784, -0.9884298898051642],
                      [0.0, 0.0, -1.000750770419927], [0.0, 0.1565519973148426, -0.9884298898051642],
                      [0.0, 0.3092491525308283, -0.951770565130279], [0.0, 0.45433157047228967, -0.8916754706773912],
                      [0.0, 0.588226834009463, -0.809624388617307], [0.0, 0.7076380018272541, -0.7076376439308896],
                      [0.0, 0.8096247465136717, -0.588226535762493], [0.0, 0.8916758882231495, -0.4543313616994111],
                      [0.0, 0.9517710423254329, -0.30924897358264647], [0.0, 0.9884303670003174, -0.1565518183666596],
                      [0.0, 1.0007512476150815, 0.0], [0.0, 0.9884303670003174, 0.1565518183666596],
                      [0.0, 0.9517710423254329, 0.30924897358264647], [0.0, 0.8916758882231512, 0.4543313616994111],
                      [0.0, 0.8096247465136717, 0.588226535762493], [0.0, 0.7076380018272541, 0.7076376439308896],
                      [0.0, 0.5882268340094647, 0.809624388617307], [0.0, 0.45433157047229145, 0.8916754706773912],
                      [0.0, 0.3092491525308283, 0.951770565130279], [0.0, 0.1565519973148426, 0.9884298898051642],
                      [0.0, 0.0, 1.000750770419927], [-0.15655196749014522, 0.0, 0.9884298898051642],
                      [-0.30924906305673794, 0.0, 0.951770565130279], [-0.4543314809981993, 0.0, 0.8916754706773912],
                      [-0.5882266550612814, 0.0, 0.809624388617307], [-0.7076378228790725, 0.0, 0.7076376439308896],
                      [-0.8096245675654901, 0.0, 0.588226535762493], [-0.8916757092749679, 0.0, 0.4543313616994111],
                      [-0.9517708037278556, 0.0, 0.30924897358264647], [-0.988430128402741, 0.0, 0.1565518183666596],
                      [-1.0007510090175042, 0.0, 0.0], [-0.988430128402741, 0.0, -0.1565518183666596],
                      [-0.9517708037278556, 0.0, -0.30924897358264647], [-0.8916757092749679, 0.0, -0.4543313616994111],
                      [-0.8096245675654901, 0.0, -0.588226535762493], [-0.7076378228790725, 0.0, -0.7076376439308896],
                      [-0.5882266550612814, 0.0, -0.809624388617307], [-0.4543314809981993, 0.0, -0.8916754706773912],
                      [-0.30924906305673794, 0.0, -0.951770565130279], [-0.15655196749014522, 0.0, -0.9884298898051642],
                      [0.0, 0.0, -1.000750770419927], [0.15655192275309915, 0.0, -0.9884298898051642],
                      [0.3092490034073432, 0.0, -0.951770565130279], [0.4543313616994107, 0.0, -0.8916754706773912],
                      [0.5882265357624927, 0.0, -0.809624388617307], [0.7076376439308891, 0.0, -0.7076376439308896],
                      [0.8096243886173067, 0.0, -0.588226535762493], [0.8916754706773915, 0.0, -0.4543313616994111],
                      [0.9517705651302792, 0.0, -0.30924897358264647], [0.9884298898051647, 0.0, -0.1565518183666596],
                      [1.000750770419927, 0.0, 0.0], [0.9884298898051647, 0.0, 0.1565518183666596],
                      [0.9517705651302792, 0.0, 0.30924897358264647], [0.8916754706773915, 0.0, 0.4543313616994111],
                      [0.8096243886173067, 0.0, 0.588226535762493], [0.7076376439308891, 0.0, 0.7076376439308896],
                      [0.5882265357624927, 0.0, 0.809624388617307], [0.4543313616994107, 0.0, 0.8916754706773912],
                      [0.3092490034073432, 0.0, 0.951770565130279], [0.15655192275309915, 0.0, 0.9884298898051642],
                      [0.0, 0.0, 1.000750770419927], [0.0, 0.1565519973148426, 0.9884298898051642],
                      [0.0, 0.3092491525308283, 0.951770565130279], [0.0, 0.45433157047229145, 0.8916754706773912],
                      [0.0, 0.5882268340094647, 0.809624388617307], [0.0, 0.7076380018272541, 0.7076376439308896],
                      [0.0, 0.8096247465136717, 0.588226535762493], [0.0, 0.8916758882231512, 0.4543313616994111],
                      [0.0, 0.9517710423254329, 0.30924897358264647], [0.0, 0.9884303670003174, 0.1565518183666596],
                      [0.0, 1.0007512476150815, 0.0], [0.3092491525308292, 0.9517710423254329, 0.0],
                      [0.5882268936588577, 0.8096248658124612, 0.0], [0.809624925461855, 0.5882268936588577, 0.0],
                      [0.9517711616242206, 0.3092491823555257, 0.0], [1.000750770419927, 0.0, 0.0],
                      [0.9517705651302792, -0.3092490034073432, 0.0], [0.8096243886173067, -0.5882265954118875, 0.0],
                      [0.5882265357624927, -0.8096244482667014, 0.0], [0.3092489735826467, -0.9517706247796731, 0.0],
                      [-2.98246973784444e-08, -1.0007508897187165, 0.0],
                      [-0.30924906305673794, -0.9517706844290679, 0.0], [-0.5882266550612814, -0.8096245079160962, 0.0],
                      [-0.8096245675654901, -0.5882266550612805, 0.0], [-0.9517708037278556, -0.30924906305673794, 0.0],
                      [-1.0007510090175042, 0.0, 0.0], [-0.9517708037278556, 0.30924906305673794, 0.0],
                      [-0.8096246272148839, 0.5882267147106752, 0.0], [-0.58822677436007, 0.8096246868642787, 0.0],
                      [-0.3092491525308292, 0.9517709826760381, 0.0], [0.0, 1.0007512476150815, 0.0]]
            self.transform = pm.curve(p=points, n=self.name, d=1)
            super().create()


class Ribbon(RigModule):
    def __init__(self, name, surface, section_joints: int, n_ctrl: int):
        super().__init__(name)

        self.surface = pm.nt.Transform(surface)
        spans = self.surface.numSpansInU()

        self.n_joints = (spans * section_joints + spans if section_joints != 0 else spans) + 1
        self.n_ctrl = n_ctrl if n_ctrl != 0 else self.surface.numSpansInU() + 1

        self.controls = []
        self.joints = []

        self.proxy = None

    def createFollicle(self, surface, uv_position, name):
        fol_shape = pm.createNode("follicle", n=name)
        fol_shape.getParent().rename(name)

        surface.ws >> fol_shape.inputSurface
        fol_shape.outTranslate >> fol_shape.getParent().t
        fol_shape.outRotate >> fol_shape.getParent().r
        fol_shape.parameterV.set(uv_position[0])
        fol_shape.parameterU.set(uv_position[1])
        pm.hide(fol_shape)
        return fol_shape

    def setScaleRelativeToDistance(self, driver1, driver2, driven):
        distance_node = pm.createNode("distanceBetween", n=f"{driven.name()}_distance")
        driver1.worldMatrix >> distance_node.inMatrix1
        driver2.worldMatrix >> distance_node.inMatrix2

        mult_node = pm.createNode("multiplyDivide", n=f"{driven.name()}_MD")
        mult_node.operation.set(2)
        distance_node.distance >> mult_node.input1X
        mult_node.input2X.set(distance_node.distance.get())
        mult_node.outputX >> driven.sx
        mult_node.outputX >> driven.sy
        mult_node.outputX >> driven.sz

        return (distance_node, mult_node)

    def getRibbon(self, n_joints):
        # surf = pm.selected()[0].getShape()
        # n_joints = 10

        skn_grp = pm.group(em=True, n=f"{self.name}_skinning")
        fol_grp = pm.group(em=True, n=f"{self.name}_follicles")
        fol_scale_grp = pm.group(em=True, n=f"{self.name}_FOL_static", p=fol_grp)
        fol_ref_grp = pm.group(em=True, n=f"{self.name}_FOL_dynamic", p=fol_grp)
        fol_scale_grp.it.set(0)
        fol_ref_grp.it.set(0)

        percentage = 1.0 / (n_joints - 1)
        factor = 0

        skinning = []
        for i in range(n_joints):
            base_name = f"{self.name}_{str(i).zfill(3)}"
            fol_skn = self.createFollicle(self.surface, [0.5, factor], f"{base_name}_fol")
            fol_dst = self.createFollicle(self.surface, [1.0, factor], f"{base_name}_ref_scale")

            scale_offset = pm.group(em=True, n=f"{base_name}_scale", p=fol_skn.getParent())

            # self.setScaleRelativeToDistance(fol_skn, fol_dst, fol_skn.getParent())
            self.setScaleRelativeToDistance(fol_skn, fol_dst, scale_offset)

            jnt = pm.joint(None, n=f"{base_name}_skn")
            skinning.append(jnt)
            scale_offset.worldMatrix >> jnt.offsetParentMatrix

            factor += percentage

            pm.parent(fol_skn.getParent(), fol_scale_grp)
            pm.parent(fol_dst.getParent(), fol_ref_grp)

        pm.hide(fol_grp)
        pm.parent(skinning, skn_grp)
        self.joints = skinning
        return (skn_grp, fol_grp)

    def getRibbonDrivers(self, n_drv):
        grp = pm.group(em=True, n=f"{self.name}_drivers")
        grp.it.set(0)
        fol_temp = self.createFollicle(self.surface, [0.5, 0], "temp")
        percentage = 1.0 / (n_drv - 1)
        factor = 0
        drivers = []
        for i in range(n_drv):
            fol_temp.parameterU.set(factor)
            drv = pm.joint(None, radius=2.0, n=f"{self.name}_{str(i).zfill(3)}_drv")
            pm.delete(pm.parentConstraint(fol_temp.getParent(), drv))

            factor += percentage
            drivers.append(drv)
        pm.parent(drivers, grp)
        pm.hide(grp)
        pm.delete(fol_temp.getParent())
        return (grp, drivers)

    def getRibbonControl(self, drivers):
        grp = pm.group(em=True, n=f"{self.name}_controls")
        controls = []

        for drv in drivers:
            ctrl = pm.circle(n="{}_ctrl".format(drv.name()[:-4]), r=1.0, normal=[1, 0, 0])[0]
            offset = pm.group(ctrl, n="{}_root".format(ctrl.name()))
            pm.delete(pm.parentConstraint(drv, offset))

            ctrl.worldMatrix >> drv.offsetParentMatrix
            pm.xform(drv, t=[0, 0, 0], ro=[0, 0, 0], s=[1, 1, 1])
            # pm.parentConstraint(ctrl, drv, mo=True)
            # pm.scaleConstraint(ctrl, drv, mo=True)
            controls.append(offset)
            self.controls.append(ctrl)

        pm.parent(controls, grp)
        return grp, controls

    def create_proxy(self):
        pm.select(self.surface)
        nurb_to_poly = pm.mel.eval(
            f'nurbsToPoly -mnd 1  -ch 1 -f 0 -pt 1 -pc 400 -chr 0.9 -ft 0.01 -mel 0.001 -d 0.1 -ut 1 -un 3 -vt 1 -vn 3 -uch 0 -ucr 0 -cht 0.2 -es 0 -ntr 0 -mrt 0 -uss 1 "{self.surface}";')
        proxy = pm.nt.Transform(nurb_to_poly[0])
        self.proxy = proxy
        pm.delete(proxy, ch=True)
        pm.skinCluster(self.joints, proxy, sm=0, mi=5)
        proxy.rename(f"{self.name}_proxy")
        pm.parent(proxy, self.group_hidden)

    def build(self):
        ####    CREAR RIBBONS   ####
        skn_group, fol_grp = self.getRibbon(self.n_joints)
        drv_group, drivers = self.getRibbonDrivers(self.n_ctrl)
        ctr_group, controls = self.getRibbonControl(drivers)

        ####    CREATE MODULE STRUCTURE.
        super().build()
        pm.parent(skn_group, drv_group, fol_grp, self.surface, self.group_hidden)
        pm.parent(ctr_group, self.group_visible)

        ####    CREATE PROXY    ####
        pm.skinCluster(self.surface, drivers, mi=1)
        self.create_proxy()

        pm.displayInfo(f"\n\n{self.name} build finished.")


class Orbital(RigModule):
    """
    SUMMARY:
       Crea folliculos orbitales que siguen a los objetos seleccionados.
       Seleccionar:
           Primero Surface.
           Luego cualquier cantidad de objetos Transform que guiaran a los foliculos.
    """

    def __init__(self, name, surface, *follow_at):
        super().__init__(name)
        self.surface = surface
        self.follow_at = follow_at

    def build(self):
        ##    SELECCIONA PRIMERO EL SURFACE Y LUEGO LOS OBJETOS QUE SEGUIRÁN LOS FOLLICULOS.
        # surface, *follow_at = pm.selected()

        ##    SEGUIR SOLO SI LA SELECCION ES UN SURFACE.
        if isinstance(self.surface.getShape(), pm.nt.NurbsSurface):
            ##    ASEGURAR QUE EL SURFACE ESTA CONFIGURADO DE 0 A 1.
            pm.rebuildSurface(self.surface, rpo=1, rt=0, end=1, kr=0, kcp=1, kc=0, su=4, du=3, sv=4, dv=3, tol=0.01,
                              fr=0, dir=2)
            pm.select(self.surface)
            pm.mel.eval('doBakeNonDefHistory( 1, {"prePost" });')
            surface_shape = [shape for shape in self.surface.getShapes() if shape.intermediateObject.get() == 0][0]

            super().build()
            ##    CREAR ORBITAL POR CADA OBJECO GUIA.
            for obj in self.follow_at:
                closest = pm.nt.ClosestPointOnSurface(n=f"{obj.name()}_closestNode")
                surface_shape.worldSpace >> closest.inputSurface

                ##    OBTENER UBICACION DE LOS OBJETOS RESPECTO AL MUNDO.
                decompose_matrix = pm.nt.DecomposeMatrix(n=f"{obj.name()}_decomposeMatrix")
                obj.worldMatrix >> decompose_matrix.inputMatrix
                decompose_matrix.outputTranslate >> closest.inPosition

                ##    CREAR FOLICULO.
                fol_shape = pm.nt.Follicle()
                fol = fol_shape.getParent()
                fol.rename(f"{obj.name()}_orbitalFollicle")

                ##    CONECTAR PARAMETROS A SHAPE DEL FOLICULO.
                surface_shape.worldSpace >> fol_shape.inputSurface
                closest.parameterU >> fol_shape.parameterU
                closest.parameterV >> fol_shape.parameterV

                ##    CONECTAR TRANSFORMACIONES A FOLICULO. ESCALA SERA LA ESCALA DEL OBJETO GUIA.
                fol_shape.outTranslate >> fol.t
                fol_shape.outRotate >> fol.r
                decompose_matrix.outputScale >> fol.s

                pm.parent(fol, self.group_hidden)


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


class Zipper(RigModule):
    def __init__(self):
        pass


class SquashStretch(RigModule):
    def __init__(self, name, *components):
        super().__init__(name)
        self.components = components

    def build(self):
        shape, lattice, lattice_base = pm.lattice(self.components, n=f"{self.name}_lattice", oc=True, dv=[2, 3, 2])

        clusters = []
        locators = []
        controls = []

        for index in range(3):
            name = f"{self.name}_{str(index + 1).zfill(2)}"
            cluster = pm.cluster(lattice.pt[:][index][:], n=f"{name}_cls")[1]
            locator = pm.spaceLocator(n=f"{name}_loc")

            pm.delete(pm.parentConstraint(cluster, locator))
            pm.parent(cluster, locator)
            control = Sphere(f"{name}", reference=locator)

            clusters.append(cluster)
            locators.append(locator)
            controls.append(control)

            if index == 0 or index == 2:
                pm.parentConstraint(control.transform, locator, mo=True)
                pm.scaleConstraint(control.transform, locator, mo=True)
            else:
                pm.parentConstraint(control.transform, cluster, mo=True)
                pm.parentConstraint(locator, control.set_offset(), mo=True)

        pm.pointConstraint(locators[0], locators[2], locators[1], mo=True)

        distance = pm.nt.DistanceBetween(n=f"{self.name}_distance")
        locators[0].t >> distance.point1
        locators[2].t >> distance.point2

        multiply = pm.nt.MultiplyDivide(n=f"{self.name}_multiply")
        multiply.operation.set(2)
        multiply.input1X.set(distance.distance.get())
        distance.distance >> multiply.input2X

        multiply.outputX >> locators[1].sx
        multiply.outputX >> locators[1].sy
        multiply.outputX >> locators[1].sz

        ###     MODULE ORDER    ###
        super().build()
        [self.controls.append(control.transform) for control in controls]
        pm.parent(controls[0].transform, controls[2].transform, controls[1].offset, self.group_visible)
        pm.parent(lattice, lattice_base, locators, self.group_hidden)

        controls[0].set_offset()
        controls[2].set_offset()

        self.group_hidden.it.set(1)
        lattice.it.set(0)
        shape.outsideLattice.set(1)
        shape.local.set(1)


class Mouth(RigModule):
    def __init__(self, name, skull=None, jaw=None):
        super().__init__(name)
        self.anchor = None
        self.surfaces = None

        self.skull = pm.nt.Transform(skull)
        self.jaw = pm.nt.Transform(jaw)

        self.main_surfaces = []
        self.scale = pm.dt.Vector(1, 1, 1)
        self.control_displacement = pm.dt.Vector(0, 0, 0)

    def create_proxy(self):
        ########    create anchor       ########
        loc_name = f"{self.name}_anchor"
        self.anchor = pm.spaceLocator(n=loc_name) if not pm.objExists(loc_name) else pm.PyNode(loc_name)

        if not self.anchor.hasAttr("divisions"):
            pm.addAttr(self.anchor, ln="divisions", at="long", k=True, dv=6)
        if not self.anchor.hasAttr("width"):
            pm.addAttr(self.anchor, ln="width", at="double", k=True, dv=10)
        if not self.anchor.hasAttr("depth"):
            pm.addAttr(self.anchor, ln="depth", at="double", k=True, dv=0.2)

        ########        create surface      ########
        surfaces = []
        for prefix in ["upp", "dwn"]:
            name = f"{prefix}_lip_surface"
            if not pm.objExists(name):
                surface_transform, surface_nurb = pm.nurbsPlane(n=name, axis=[0, 1, 0])
                surface_nurb.rename(f"{name}MakeNurb")
            else:
                surface_transform = pm.PyNode(name)
                surface_nurb = pm.PyNode(name + "MakeNurb")
            surfaces.append((surface_transform, surface_nurb))
        self.surfaces = surfaces

        ########        connect deforms     ########
        self.create_proxy_flare(surfaces[0][0], surfaces[1][0])
        self.create_proxy_bend(surfaces[0][0], surfaces[1][0])

        mult_name = f"{self.name}_lengthNormalization"
        mult_neutralize = pm.nt.MultiplyDivide(n=mult_name) if not pm.objExists(mult_name) else pm.PyNode(mult_name)
        self.anchor.width >> mult_neutralize.input2X
        self.anchor.depth >> mult_neutralize.input1X
        mult_neutralize.operation.set(2)

        for surface in surfaces:
            self.anchor.width >> surface[1].width
            mult_neutralize.outputX >> surface[1].lengthRatio
            self.anchor.divisions >> surface[1].patchesU

        pm.parent(surfaces[0][0], surfaces[1][0], self.anchor)
        pm.displayInfo("Proxy created.")

    def create_proxy_bend(self, *surface_transform):
        ########    CREATE ATTRIBUTES IN LOCATOR    ########
        curve_attr = "curve"
        height_bound_attr = "height_bound"
        if not self.anchor.hasAttr(curve_attr):
            pm.addAttr(self.anchor, ln=curve_attr, at="double", k=True, dv=4, min=-10, max=10)

        if not self.anchor.hasAttr(height_bound_attr):
            pm.addAttr(self.anchor, ln=height_bound_attr, at="double", k=True, dv=1, min=0, max=1)

        ########    CREATE DEFORMER                 ########
        bend_name = f"{self.name}_bend"
        bend_deformer, bend_transform = pm.nonLinear(surface_transform, type="bend", n=bend_name) if not pm.objExists(
            bend_name) else (pm.PyNode(bend_name), None)

        ########    CONNECT CURVATURE ATTRIBUTE     ########
        unitConversion_curve = pm.nt.UnitConversion(n=f"{self.name}_uConversion_curve")
        unitConversion_curve.conversionFactor.set(0.3)
        self.anchor.attr(curve_attr) >> unitConversion_curve.input
        unitConversion_curve.output >> bend_deformer.curvature

        # self.anchor.attr(curve_attr) >> bend_deformer.curvature

        mult_name = f"{self.name}_amplifyBend"
        mult_amplify = pm.nt.MultiplyDivide(n=mult_name) if not pm.objExists(mult_name) else pm.PyNode(mult_name)
        mult_amplify.operation.set(2)
        self.anchor.width >> mult_amplify.input1X
        mult_amplify.input2X.set(-2)

        ########    SET BOUND HEIGHT            ########
        unitConversion = pm.nt.UnitConversion(n=f"{self.name}_unitConversion")
        unitConversion.conversionFactor.set(-1)
        self.anchor.attr(height_bound_attr) >> unitConversion.input
        unitConversion.output >> bend_deformer.lowBound
        self.anchor.attr(height_bound_attr) >> bend_deformer.highBound

        ########    ORIENT DEFORMER             ########
        if bend_transform:
            bend_transform.r.set([90, -90, 0])

            self.anchor.width >> bend_transform.sx
            self.anchor.width >> bend_transform.sy
            self.anchor.width >> bend_transform.sz

            mult_amplify.outputX >> bend_transform.sx
            mult_amplify.outputX >> bend_transform.sy
            mult_amplify.outputX >> bend_transform.sz

            pm.parent(bend_transform, self.anchor)
            pm.hide(bend_transform)

    def create_proxy_flare(self, *surface_transform):
        if not self.anchor.hasAttr("flare"):
            pm.addAttr(self.anchor, ln="flare", at="double", k=True, dv=3)

        flare_name = f"{self.name}_flare"
        flare_deformer, flare_transform = pm.nonLinear(surface_transform, type="flare",
                                                       n=flare_name) if not pm.objExists(flare_name) else (
        pm.PyNode(flare_name), None)

        self.anchor.flare >> flare_deformer.curve

        mult_name = f"{self.name}_amplifyFlare"
        mult_amplify = pm.nt.MultiplyDivide(n=mult_name) if not pm.objExists(mult_name) else pm.PyNode(mult_name)
        mult_amplify.operation.set(2)
        self.anchor.width >> mult_amplify.input1X
        mult_amplify.input2X.set(2)

        if flare_transform:
            flare_transform.r.set([90, -90, 0])
            mult_amplify.outputX >> flare_transform.sx
            mult_amplify.outputX >> flare_transform.sy
            mult_amplify.outputX >> flare_transform.sz

            pm.parent(flare_transform, self.anchor)
            pm.hide(flare_transform)

    def create_main_layer(self):
        controls = []
        drivers = []
        control_displacement = pm.dt.Vector(0, self.control_displacement.y * .4, 0)
        positions = {"UPP": [pm.dt.Matrix(), pm.dt.Vector(-90, 0, 0)],
                     "DWN": [pm.dt.Matrix(), pm.dt.Vector(90, 0, 0)],
                     "L": [pm.dt.Matrix(), pm.dt.Vector(90, 90, 0)],
                     "R": [pm.dt.Matrix(), pm.dt.Vector(90, 90, 0)]
                     }

        ########    use follicle to find location for frontal controls.
        def create_follicle():
            follicle_shape = pm.nt.Follicle(n="delete")
            follicle_shape.getParent().rename("delete")
            follicle_shape.parameterU.set(0.5)
            follicle_shape.parameterV.set(0.5)
            follicle_shape.outTranslate >> follicle_shape.getParent().t
            follicle_shape.outRotate >> follicle_shape.getParent().r
            return follicle_shape.getParent()

        def create_control(name, rotate=(0, 0, 0)):
            control = Semicircle(name, [0, 0, 1])
            control.create()
            control.set_root()
            control.set_offset()
            control.yellow()
            control.thick()

            control.rotate(rotate)
            control.translate(control_displacement)
            controls.append(control)

            driver = pm.joint(control.transform, n=f"{name}_drv")
            pm.hide(driver)
            drivers.append(driver)
            return control, driver

        def get_control_positions(follicle):
            ####    UPP & DWN VECTORS     ####
            for surface_tuple in self.surfaces:
                surface = surface_tuple[0]
                surface.worldSpace >> follicle.inputSurface
                if "UPP" in surface.name().upper():
                    positions["UPP"][0] = follicle.getMatrix(ws=True)
                if "DWN" in surface.name().upper():
                    positions["DWN"][0] = follicle.getMatrix(ws=True)

            #### LEFT VECTORS           ####
            follicle.parameterU.set(1.0)
            positions["L"][0] = follicle.getMatrix(ws=True)

            #### RIGHT VECTORS          ####
            inverted_tm = pm.dt.TransformationMatrix()
            inverted_tm.scale = (-1, 1, 1)
            inverted_matrix = follicle.getMatrix(ws=True) * inverted_tm
            positions["R"][0] = inverted_matrix
            return positions

        ########        CONTROL CREATION        ########
        follicle_aux = create_follicle()
        positions = get_control_positions(follicle_aux)
        pm.delete(follicle_aux.getParent())
        for index, vectors in positions.items():
            matrix = vectors[0]
            shape_rotation = vectors[1]
            control, driver = create_control(f"{self.name}_{index}", shape_rotation)
            control.root.setMatrix(matrix)

        #######         SURFACES SETUP    ########
        lip_upp_surface = self.surfaces[0][0].duplicate(n=f"{self.surfaces[0][0].name()}_main")
        lip_dwn_surface = self.surfaces[1][0].duplicate(n=f"{self.surfaces[1][0].name()}_main")
        pm.makeIdentity(lip_upp_surface, lip_dwn_surface, a=True)
        rebuildSurface(lip_upp_surface, 3)
        rebuildSurface(lip_dwn_surface, 3)

        drivers_upp = [driver for driver in drivers if any(suffix in driver.name() for suffix in ("_L", "_R", "_UPP"))]
        drivers_dwn = [driver for driver in drivers if any(suffix in driver.name() for suffix in ("_L", "_R", "_DWN"))]
        pm.skinCluster(drivers_upp, lip_upp_surface, toSelectedBones=True, bindMethod=1, skinMethod=0)
        pm.skinCluster(drivers_dwn, lip_dwn_surface, toSelectedBones=True, bindMethod=1, skinMethod=0)

        ########        BUILD MAIN MODULE                   ########
        module = RigModule("lip_main")
        module.build()
        pm.parent(lip_upp_surface, lip_dwn_surface, module.group_hidden)
        control_roots = [control.root for control in controls]
        pm.parent(control_roots, module.group_visible)

        module.controls = controls
        module.joints = drivers
        self.main_surfaces = [lip_upp_surface, lip_dwn_surface]

        return module

    def create_layer(self, name, surface, section_joints, n_ctrl, surface_guide=None, control_scale=1):
        ########    PREPARE SURFACE BEFORE BUILD    ########
        surface = surface.duplicate(n=f"{name}_layer")[0]
        rebuildSurface(surface, n_ctrl)
        pm.makeIdentity(surface, a=True, t=True, r=True, s=True)
        pm.delete(surface, ch=True)
        ribbon = Ribbon(name=name, surface=surface, section_joints=section_joints, n_ctrl=n_ctrl)
        ribbon.build()

        ########    SHRINK LAYER'S CONTROLS     ########
        for control in ribbon.controls:
            ct = Control(control)
            ct.set_root()
            ct.rotate(pm.dt.Vector(0, 0, 90))
            ct.scale([control_scale, control_scale, control_scale])
            ct.translate(self.control_displacement)

            ########    IF SURFACE GUIDE IS GIVEN, THEN PIN CONTROLS TO IT     ########
            if surface_guide:
                fol = create_rivet(surface_guide, control)
                pm.parentConstraint(fol, control.getParent(), mo=True)
                fol.it.set(0)
                pm.parent(fol, ribbon.group_hidden)

        return ribbon

    def setup_anchors(self, main_module):
        anchor_upp = pm.spaceLocator(n=f"{self.name}_anchor_upp")
        anchor_dwn = pm.spaceLocator(n=f"{self.name}_anchor_dwn")

        anchor_upp_offset = pm.group(anchor_upp, n=f"{anchor_upp.name()}_offset")
        anchor_dwn_offset = pm.group(anchor_dwn, n=f"{anchor_dwn.name()}_offset")
        anchor_upp_offset.setMatrix(main_module.controls[2].transform.getMatrix(ws=True), ws=True)
        anchor_dwn_offset.setMatrix(main_module.controls[3].transform.getMatrix(ws=True), ws=True)
        return anchor_upp, anchor_dwn

    def setup_corner_height(self, anchor_upp, anchor_dwn, corner_L_driven, corner_R_driven):
        # corner_height_grp = pm.group(n="corners_height_grp", em=True)
        corner_sides = []
        local_anchor_upp = pm.spaceLocator(n=f"{self.name}_local_anchor_upp")
        local_anchor_dwn = pm.spaceLocator(n=f"{self.name}_local_anchor_dwn")
        anchor_upp.matrix >> local_anchor_upp.offsetParentMatrix
        anchor_dwn.matrix >> local_anchor_dwn.offsetParentMatrix
        pm.hide(local_anchor_upp, local_anchor_dwn)

        control_group = set([corner.root.getParent() for corner in [corner_L_driven, corner_R_driven]])
        for corner in [corner_L_driven, corner_R_driven]:
            name = corner.name
            worldMatrix = corner.transform.getMatrix(ws=True)
            corner_offset = pm.group(n=f"{name}_height_offset", em=True)
            loc_upp = pm.spaceLocator(n=f"{name}_height_UPP")
            loc_dwn = pm.spaceLocator(n=f"{name}_height_DWN")
            loc_mid = pm.spaceLocator(n=f"{name}_height")
            pm.hide(loc_upp.getShapes(), loc_dwn.getShapes(), loc_mid.getShapes())

            pm.parent(loc_upp, loc_dwn, loc_mid, corner_offset)
            corner_offset.setMatrix(corner.transform.getMatrix(ws=True), ws=True)
            pm.parentConstraint(local_anchor_upp, loc_upp, mo=True)
            pm.parentConstraint(local_anchor_dwn, loc_dwn, mo=True)

            pm.parent(corner_offset, control_group)
            pm.parent(corner.root, loc_mid)

            ####    SETUP ATTRIBUTE &  AUTOMATE CORNERS        ########
            parentConstraint = pm.pointConstraint(loc_upp, loc_dwn, loc_mid, mo=True)
            # scaleConstraint  = pm.scaleConstraint(loc_upp, loc_dwn, loc_mid, mo=True)

            pm.addAttr(corner.transform, ln="height", at="double", k=True, min=0, max=1, dv=0.5)
            corner.transform.height >> parentConstraint.w0
            reverse = create_reverse(corner.transform.height, parentConstraint.w1)
            corner_sides.append(loc_mid)

        pm.parent(local_anchor_upp, local_anchor_dwn, control_group)
        # return corner_height_grp, corner_sides[0], corner_sides[1]
        return None, corner_sides[0], corner_sides[1]

    def setup_front_control(self, anchor_upp, anchor_dwn, *controls):
        ########    CREATE MAIN CONTROLS    ########
        def create_control(name, scale, parent_to=None):
            control = Circle(name, [0, 0, 1])
            control.create()
            control.scale(self.scale * scale)
            control.yellow()
            control.set_root()
            control.set_offset()
            return control

        mouth_main_ctrl = create_control(f"{self.name}_M", 1)
        mouth_secc_ctrl = create_control(f"{self.name}", 0.8)
        pm.parent(mouth_secc_ctrl.root, mouth_main_ctrl.transform)

        ########    PLACE CONTROLS                      ########
        def place_control():
            pm.delete(pm.parentConstraint(anchor_upp, anchor_dwn, mouth_main_ctrl.root))
            mid_vector = mouth_main_ctrl.transform.getTranslation(ws=True)
            upp_vector = anchor_upp.getTranslation(ws=True)
            dwn_vector = anchor_dwn.getTranslation(ws=True)
            jaw_vector = self.jaw.getTranslation(ws=True)

            z_axis = max(upp_vector.z, dwn_vector.z)
            distance = pm.dt.Vector(0, 0, z_axis).distanceTo(pm.dt.Vector(0, 0, jaw_vector.z))
            move_vector = pm.dt.Vector(mid_vector.x, mid_vector.y, distance * .5)
            delta = pm.dt.Vector(0, 0, self.control_displacement.y * -1.5)
            mouth_main_ctrl.root.setTranslation(move_vector + delta, ws=True)

        place_control()

        ########    CONNECT ANCHORS TO FRONT CONTROLS   ########
        blendMatrix = create_blendMatrix(anchor_upp, False, anchor_dwn)
        decompose = pm.nt.DecomposeMatrix(n=f"{self.name}_M_decompose")
        blendMatrix.target[0].rotateWeight.set(0)
        blendMatrix.outputMatrix >> decompose.inputMatrix
        decompose.outputTranslate >> mouth_main_ctrl.offset.t
        decompose.outputRotate >> mouth_main_ctrl.offset.r
        decompose.outputScale >> mouth_main_ctrl.offset.s

        ########    CREATE LOCATORS         ########
        def create_locator(name):
            locator = pm.spaceLocator(n=name)
            locator_offset = pm.group(locator, n=f"{name}_offset")
            locator.getShape().hide()
            align_to(control_grp, locator_offset)
            return locator, locator_offset

        control_grp = list(set([control.root.getParent() for control in controls]))[0]
        locals_locators = []

        ########    LOCAL LOCATOR OVER CONTROL                  ########
        loc_local, loc_local_offset = create_locator(f"{control_grp.name()}_local")
        loc_world, loc_world_offset = create_locator(f"{control_grp.name()}_world")

        loc_world.t >> loc_local.t
        loc_world.r >> loc_local.r
        loc_world.s >> loc_local.s

        for control in controls:
            if control.root.getParent() == control_grp:
                build_hierarchy(control_grp, loc_local_offset, loc_local, control.root)

        pm.parent(loc_world_offset, mouth_main_ctrl.offset)
        constrain(mouth_secc_ctrl.transform, loc_world)

        locals_locators.append(loc_local)

        return mouth_main_ctrl, *locals_locators

    def build(self):
        self.scale = pm.dt.Vector(self.anchor.getScale())
        self.control_displacement = pm.dt.Vector(0, self.anchor.depth.get() * -10, 0)
        ########    LAYER A                 ########
        main_module = self.create_main_layer()
        [control.scale(self.scale) for control in main_module.controls]
        corner_L_ctrl, corner_R_ctrl, front_upp_ctrl, front_dwn_ctrl = main_module.controls
        anchor_upp, anchor_dwn = self.setup_anchors(main_module)
        front_upp_ctrl.set_offset()
        front_dwn_ctrl.set_offset()

        constrain(self.skull, anchor_upp.getParent())
        constrain(self.skull, anchor_dwn.getParent())
        constrain(self.jaw, anchor_dwn)

        anchor_dwn.t >> front_dwn_ctrl.offset.t
        anchor_dwn.r >> front_dwn_ctrl.offset.r
        anchor_dwn.s >> front_dwn_ctrl.offset.s

        ########    SETUP MAIN MOUTH        ########
        main_mouth_ctrl, *local_locators = self.setup_front_control(anchor_upp, anchor_dwn, front_upp_ctrl,
                                                                    front_dwn_ctrl, corner_L_ctrl, corner_R_ctrl)
        # pm.parentConstraint(anchor_upp, main_module.group_visible, mo=True)
        # pm.scaleConstraint (anchor_upp, main_module.group_visible, mo=True)

        #########    SETUP CORNER HEIGHT     ########
        # corner_height_grp, corner_height_L_loc, corner_height_R_loc = self.setup_corner_height(anchor_upp, anchor_dwn, corner_L_ctrl, corner_R_ctrl)

        ########    LAYER B                 ########
        # lip_upp_B = self.create_layer("lip_upp", self.surfaces[0][0], 0, 0, self.main_surfaces[0][0], self.scale.x * 0.5)
        # lip_dwn_B = self.create_layer("lip_dwn", self.surfaces[1][0], 0, 0, self.main_surfaces[1][0], self.scale.x * 0.5)

        ########    LAYER DETAILS           ########
        # n_details = lip_upp_B.n_ctrl * 2 + 1
        # lip_upp_B_details = self.create_layer("lip_upp_details", self.surfaces[0][0], 0, n_details, lip_upp_B.surface, self.scale.x * 0.25)
        # lip_dwn_B_details = self.create_layer("lip_dwn_details", self.surfaces[1][0], 0, n_details, lip_dwn_B.surface, self.scale.x * 0.25)

        ####    clean up setup  ####
        super().build()
        hidden_groups = [main_module.group_hidden,
                         # lip_upp_B.group_hidden,
                         # lip_dwn_B.group_hidden,
                         # lip_upp_B_details.group_hidden,
                         # lip_dwn_B_details.group_hidden,
                         # corner_height_grp,
                         anchor_upp.getParent(),
                         anchor_dwn.getParent()
                         ]
        pm.parent(hidden_groups, self.group_hidden)

        visible_groups = [main_module.group_visible,
                          # lip_upp_B.group_visible,
                          # lip_dwn_B.group_visible,
                          # lip_upp_B_details.group_visible,
                          # lip_dwn_B_details.group_visible,
                          # main_mouth_ctrl.root
                          ]
        pm.parent(visible_groups, self.group_visible)

        # pm.delete(main_module.group_main, lip_upp_B.group_main, lip_dwn_B.group_main, lip_upp_B_details.group_main, lip_dwn_B_details.group_main)


"""skull = pm.nt.Transform("Head_M") if pm.objExists("Head_M") else pm.nt.Transform("head_01_ctrl")
jaw   = pm.nt.Transform("Jaw_M")  if pm.objExists("Jaw_M")  else pm.nt.Transform("jaw_01_ctrl")


mouth = Mouth("mouth", skull= skull, jaw= jaw)
mouth.create_proxy()
mouth.build()
"""

# pm.parentConstraint("head_01_ctrl", "mouth_anchor_upp", mo=True)
# pm.scaleConstraint("head_01_ctrl", "mouth_anchor_upp", mo=True)
# pm.parentConstraint("jaw_01_ctrl", "mouth_anchor_dwn", mo=True)
# pm.scaleConstraint("jaw_01_ctrl", "mouth_anchor_dwn", mo=True)

# pm.selected()[0].setRotation([15,0,0], r=True, local=True)


"""
selection = pm.selected()
surface = pm.selected()[0]
name = "modulo"
modulo = Ribbon(   name= name, surface= surface, section_joints=1, n_ctrl=2)
modulo = Orbital(  name= name, surface= surface, *selection)
modulo = FK(       name= name, joints = selection)
modulo = IK(       name= name, joints = selection)
modulo = Appendage(name= name, joints = selection, quantity=5)
modulo = IkSpline( name= name, joints = selection, n_controls=3)
modulo = SquashStretch(name=name, *selection)

modulo.create_joints()
modulo.build()
"""


class GUI:
    def __init__(self):
        self.name = ""
        self.selection = []
        self.spans = 0
        self.normal = [0, 0, 1]
        self.width = 0.5
        self.controls = 2
        self.joint_per_span = 1

        self.build_ui()

    def build_ui(self):
        window_name = "Ribbon_Window"
        if pm.window(window_name, exists=True):
            pm.deleteUI(window_name)
        with pm.window(window_name, title="Rig Setup") as win:
            with pm.columnLayout():
                with pm.frameLayout("Module Setup", marginWidth=15, marginHeight=5, width=310):
                    with pm.horizontalLayout(ratios=[3, 5, 1, 1]):
                        lbl_name = pm.text("Name")
                        self.txt_name = pm.textField()
                        self.btn_set_name = pm.button("<<", command=lambda x: self.set_name_command())
                        self.btn_clean_name = pm.button("CL", command=lambda x: self.txt_name.setText(""))
                    with pm.horizontalLayout(ratios=[3, 5, 1, 1]):
                        lbl_name = pm.text("Selection")
                        self.txt_selection = pm.textField()
                        self.btn_set_selection = pm.button("<<", command=lambda x: self.set_selection_command())
                        self.btn_clean_selection = pm.button("CL", command=lambda x: self.txt_selection.setText(""))
                with pm.frameLayout("Limbs Setup", marginWidth=15, marginHeight=5, width=310):
                    with pm.horizontalLayout():
                        self.btn_build_fk = pm.button("Build FK", command=lambda x: self.fk_command())
                        self.btn_build_ik = pm.button("Build IK", command=lambda x: self.ik_command())
                        self.btn_build_SS = pm.button("Build SS", command=lambda x: self.squashStretch_command())

                with pm.frameLayout("Surface Setup", marginWidth=15, marginHeight=5, width=310):
                    with pm.horizontalLayout():
                        with pm.verticalLayout():
                            lbl_name = pm.text("# Spans")
                            self.txt_spans = pm.textField()
                            # btn_rebuild = pm.button("Rebuild")

                        with pm.verticalLayout():
                            # lbl_name = pm.text("Create")
                            with pm.horizontalLayout():
                                self.chk_x = pm.checkBox("X", changeCommand=lambda x: self.checker_x_onChange())
                                self.chk_y = pm.checkBox("Y", changeCommand=lambda x: self.checker_y_onChange())
                                self.chk_z = pm.checkBox("Z", changeCommand=lambda x: self.checker_z_onChange())
                                self.txt_width = pm.textField()
                            with pm.horizontalLayout():
                                self.btn_create_surface = pm.button("Create",
                                                                    command=lambda x: self.surface_create_command())
                with pm.frameLayout("Ribbon Setup", marginWidth=15, marginHeight=5, width=310):
                    with pm.horizontalLayout():
                        with pm.verticalLayout():
                            lbl_name = pm.text("# Controls")
                            self.txt_n_controls = pm.textField()
                        with pm.verticalLayout():
                            lbl_name = pm.text("# Joint / Span")
                            self.txt_joint_per_span = pm.textField()
                    with pm.horizontalLayout():
                        self.btn_build_ribbon = pm.button("Build Ribbon", command=lambda x: self.ribbon_command())
                        self.btn_build_orbital = pm.button("Build Orbital", command=lambda x: self.orbital_command())
                        self.btn_build_appendage = pm.button("Build Appendage",
                                                             command=lambda x: self.appendage_command())

            self.txt_width.setText(0.5)
            self.chk_z.setValue(True)
            win.show()

    ###############        BEHAVIORS         ##############
    def update_info(self):
        self.name = self.txt_name.getText()
        ###     CAST INFO   ###
        names = self.txt_selection.getText().split(", ") if self.txt_selection.getText() else []
        self.selection = [pm.PyNode(name) for name in names]
        self.spans = self.txt_spans.getText()

        ### SET NORMALS ###
        x = self.chk_x.getValue()
        y = self.chk_y.getValue()
        z = self.chk_z.getValue()
        self.normal = [int(x), int(y), int(z)]

        self.width = float(self.txt_width.getText())
        self.controls = self.txt_n_controls.getText()
        self.joint_per_span = self.txt_joint_per_span.getText()

    def set_name_command(self):
        name = pm.selected()[0].name() if pm.selected() else ""
        self.txt_name.setText(name)

    def set_selection_command(self):
        selection = pm.selected()
        names = [obj.name() for obj in selection]
        txt_selection = ", ".join(names)
        self.txt_selection.setText(txt_selection)
        if not self.txt_name.getText():
            self.txt_name.setText(selection[0].name())

        self.update_info()

        if self.is_only_component(self.selection):
            self.btn_build_fk.setEnable(0)
            self.btn_build_ik.setEnable(0)
            self.btn_build_SS.setEnable(1)

            self.txt_spans.setEnable(0)
            self.btn_create_surface.setEnable(0)

            self.btn_build_ribbon.setEnable(0)
            self.btn_build_orbital.setEnable(0)
            self.btn_build_appendage.setEnable(0)

            self.txt_n_controls.setEnable(0)
            self.txt_spans.setEnable(0)
            self.txt_joint_per_span.setEnable(0)

        elif self.is_only_surfaces(self.selection):
            self.btn_build_fk.setEnable(0)
            self.btn_build_ik.setEnable(0)
            self.btn_build_SS.setEnable(1)

            self.txt_spans.setEnable(1)
            self.btn_create_surface.setEnable(1)

            self.btn_build_ribbon.setEnable(1)
            self.btn_build_orbital.setEnable(1)
            self.btn_build_appendage.setEnable(1)

            surface = Surface(self.selection[0])
            self.txt_spans.setText(surface.spans)

            self.txt_n_controls.setEnable(1)
            self.txt_spans.setEnable(1)
            self.txt_joint_per_span.setEnable(1)

        elif self.is_only_joint(self.selection):
            self.btn_build_fk.setEnable(1)
            self.btn_build_ik.setEnable(1)
            self.btn_build_SS.setEnable(0)

            self.txt_spans.setEnable(1)
            self.btn_create_surface.setEnable(1)

            self.btn_build_ribbon.setEnable(0)
            self.btn_build_orbital.setEnable(0)
            self.btn_build_appendage.setEnable(1)

            self.txt_n_controls.setEnable(1)
            self.txt_spans.setEnable(0)
            self.txt_joint_per_span.setEnable(0)

        elif self.is_transform_or_surface(self.selection):
            self.btn_build_fk.setEnable(1)
            self.btn_build_ik.setEnable(1)
            self.btn_build_SS.setEnable(1)

            self.txt_spans.setEnable(1)
            self.btn_create_surface.setEnable(1)

            self.btn_build_ribbon.setEnable(1)
            self.btn_build_orbital.setEnable(1)
            self.btn_build_appendage.setEnable(1)

        elif not selection:
            self.btn_build_fk.setEnable(0)
            self.btn_build_ik.setEnable(0)
            self.btn_build_SS.setEnable(0)

            self.txt_spans.setEnable(0)
            self.btn_create_surface.setEnable(0)

            self.btn_build_ribbon.setEnable(0)
            self.btn_build_orbital.setEnable(0)
            self.btn_build_appendage.setEnable(0)

            self.txt_n_controls.setEnable(0)
            self.txt_spans.setEnable(0)
            self.txt_joint_per_span.setEnable(0)

    def clean_selection_command(self):
        self.txt_selection.setText("")

    def checker_x_onChange(self):
        value = self.chk_x.getValue()
        if value:
            self.chk_y.setValue(False)
            self.chk_z.setValue(False)
            self.update_info()

    def checker_y_onChange(self):
        value = self.chk_y.getValue()
        if value:
            self.chk_x.setValue(False)
            self.chk_z.setValue(False)
            self.update_info()

    def checker_z_onChange(self):
        value = self.chk_z.getValue()
        if value:
            self.chk_x.setValue(False)
            self.chk_y.setValue(False)
            self.update_info()

    ###############        FUNCTIONS         ##############
    def ribbon_command(self):
        self.update_info()
        modulo = Ribbon(name=self.name, surface=self.selection[0], section_joints=int(self.joint_per_span),
                        n_ctrl=int(self.controls))
        modulo.build()

    def orbital_command(self):
        self.update_info()
        surfaces = [obj for obj in self.selection if isinstance(obj.getShape(), pm.nt.NurbsSurface)]
        locators = [obj for obj in self.selection if obj not in surfaces]
        for surface in surfaces:
            modulo = Orbital(self.name, surface, *locators)
            modulo.build()

    def fk_command(self):
        self.update_info()
        modulo = FK(name=self.name, joints=self.selection)
        modulo.build()

    def ik_command(self):
        self.update_info()
        modulo = IK(name=self.name, joints=self.selection)
        modulo.build()

    def appendage_command(self):
        self.update_info()
        if len(self.selection) == 1:
            modulo = Appendage(name=self.name, joints=[], quantity=int(self.controls))
        else:
            modulo = Appendage(name=self.name, joints=self.selection, quantity=int(self.controls))
        modulo.build()

    def ikSpline_command(self):
        self.update_info()
        modulo = IkSpline(name=self.name, joints=self.selection, n_controls=self.controls)
        modulo.build()

    def squashStretch_command(self):
        self.update_info()
        print(self.name)
        modulo = SquashStretch(self.name, *self.selection)
        modulo.build()

    def create_joints_command(self):
        self.update_info()
        for obj in self.selection:
            modulo = Limb("a")
            modulo.create_joints(self.spans)
            pm.delete(pm.parentConstraint(obj, modulo.joints[0]))

    def surface_create_command(self):
        self.update_info()
        surface = Surface(self.name)
        surface.create(self.selection, self.width, self.normal)
        self.txt_spans.setText(surface.spans)

    def surface_rebuild_command(self):
        self.update_info()
        surface = Surface(self.selection[0])
        surface.rebuild(self.spans)

    ###############        UTILITIES         ##############
    def is_only_component(self, selection):
        valid_types = (pm.MeshVertex, pm.MeshEdge, pm.MeshFace, pm.NurbsSurfaceCV)
        invalid_items = [item for item in selection if not isinstance(item, valid_types)]
        has_invalid_items = bool(invalid_items)
        return not has_invalid_items

    def is_only_surfaces(self, selection):
        for obj in selection:
            if isinstance(obj, pm.nt.Transform) and not isinstance(obj.getShape(), pm.nt.NurbsSurface):
                return False
        return True

    def is_only_joint(self, selection):
        for obj in selection:
            if not isinstance(obj, pm.nt.Joint):
                return False
        return True

    def is_transform_or_surface(self, selection):
        for obj in selection:
            if not isinstance(obj, pm.nt.Transform) and not isinstance(obj.getShape(), pm.nt.NurbsSurface):
                return False  # Early exit on invalid object
        return True  # All objects are either Transform or NurbsSurface

gui = GUI()
