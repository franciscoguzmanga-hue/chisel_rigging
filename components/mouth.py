'''
################################################################################################################
Author: Francisco Guzmán

Content: Rigging module for the mouth.
Dependency: pymel.core
Maya Version tested: 2024

How to:
    - Use: Instructions to use the module
    - Test: Instructions to test the module

TODO: IMPLEMENT.
################################################################################################################
'''

import pymel.core as pm



class Zipper(RigModule):
    def __init__(self):
        pass

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



