'''
################################################################################################################
Author: Francisco Guzmán

Content: Core functions to build a Ribbon module.
Dependency: pymel.core
Maya Version tested: 2024

How to:
    - Use:  
        - Create an instance of the Ribbon class with the desired parameters and call the build() method.
        - Example:
            surface = pm.nt.Transform("surface1") # Surface to use as base for the ribbon. Must be a nurbs surface's transform.
            ribbon_module = Ribbon(name="myRibbon", surface=surface, section_joints=2, ctrl_quantity=5)
            ribbon_module.build()

    - Test: Use module in src.test.rigging_modules.ribbon_test to see an example of how to use the module and test it interactively in Maya.

################################################################################################################
'''

import pymel.core as pm

from src.core.control_lib import Circle
from src.core.module_core import RigModule
from src.utility.inspect_utils import is_nurbs_surface
from src.utility.transform_utils import align_transform, freeze_transform, reset_transform

class SurfaceOrient:
    # Vectors to create curves to use as base fot a surface with loft.
    X_UP = [pm.dt.Vector(0, 0, 0.5), pm.dt.Vector(0, 0, -0.5)]
    Y_UP = [pm.dt.Vector(0, 0, 0.5), pm.dt.Vector(0, 0, -0.5)]
    Z_UP = [pm.dt.Vector(0, 0.5, 0), pm.dt.Vector(0, -0.5, 0)]

class Surface:
    def __init__(self, name: str=""):
        self.name = name
        
        self.transform = None
        self.shape = None
        self.spans = 0
        
        self.cast()

    def cast(self):
        if pm.objExists(self.name):
            self.transform = pm.nt.Transform(self.name)
            if is_nurbs_surface(self.transform):
                self.shape = self.transform.getShape()
                self.spans = self.transform.numSpansInU()
        else:
            self.shape = None
            self.spans = 0

    def _create_proxy_curve(self, width=1.0, normal: SurfaceOrient= SurfaceOrient.Y_UP) -> pm.nt.Transform:
        """Creates a perpendicular line curve to use as proxy to later create a Surface using Loft.

        Args:
            width (float, optional): Width of the curve. Defaults to 1.0.
            normal (SurfaceOrient, optional): Normal vector to orient the curve. Defaults to SurfaceOrient.Y_UP.
        Returns:
            pm.nt.Transform: The created curve transform.
        """        
        point_A, point_B = normal
        curve = pm.curve(point=[point_A*width, point_B*width], d=1)
        return curve

    def create(self, joints: list[pm.nt.Transform], width: float=1.0, normal=[0, 1, 0]) -> pm.nt.Transform:
        """Create a nurbs surface along a transform list selection.

        Args:
            joints (list[pm.nt.Transform]): List of transforms to create the surface along.
            width (float, optional): Width of the surface. Defaults to 1.0.
            normal (list, optional): Normal vector for the surface orientation. Defaults to [0, 1, 0].

        Returns:
            pm.nt.Transform: The created nurbs surface transform.
        """
        if self.transform:
            return self.transform
        
        proxy_curves = []
        for joint in joints:
            proxy_curve = self._create_proxy_curve(width, normal)
            proxy_curve.setMatrix(joint.getMatrix(ws=True), ws=True)
            proxy_curves.append(proxy_curve)
        surface = pm.loft(proxy_curves, n=self.name)[0]
        pm.delete(proxy_curves)
        
        self.name = surface.name() # Reassigned name in case there was a name conflict and Maya renamed the surface.
        self.cast()

    def rebuild(self, spans: int):
        """Rebuild surface to have the required spans.

        Args:
            spans (int): Number of spans in U direction for the surface.
        """
        pm.rebuildSurface(self.transform, du=3, dir=0, su=spans)
        pm.select(self.transform)
        pm.mel.eval('doBakeNonDefHistory( 1, {"prePost" });')
        pm.delete(self.transform, ch=True)

class Ribbon(RigModule):
    def __init__(self, name:str, surface: pm.nt.Transform, section_joints: int, ctrl_quantity: int):
        """Class to generate a ribbon rig module.

        Args:
            name (str): Name of the module.
            surface (pm.nt.Transform): Surface to us as base for the ribbon. Must be a nurbs surface's transform.
            section_joints (int): number of joints to put inside each span section of the surface. If 0, it will only create joints in the spans.
            ctrl_quantity (int): number of control objects to create. If 0, it will create a control for each span.
        """
        super().__init__(name)

        self.surface = pm.nt.Transform(surface)
        spans = self.surface.numSpansInU()

        self.n_joints = (spans * section_joints + spans if section_joints != 0 else spans) + 1
        self.n_ctrl = ctrl_quantity if ctrl_quantity != 0 else spans + 1

        self.controls = []
        self.joints = []
        self.skin_proxy = None

    def create_follicle(self, surface: pm.nt.Transform, uv_position: list[float], name: str) -> pm.nt.Transform:
        follicle_shape = pm.createNode("follicle", n=name)
        follicle_transform = follicle_shape.getParent()
        follicle_transform.rename(name)

        surface.ws >> follicle_shape.inputSurface
        follicle_shape.outTranslate >> follicle_transform.t
        follicle_shape.outRotate >> follicle_transform.r
        follicle_shape.parameterV.set(uv_position[0])
        follicle_shape.parameterU.set(uv_position[1])
        pm.hide(follicle_shape)
        return follicle_transform
    
    def setup_stretch_scaling(self, 
                            driver_A: pm.nt.Transform, 
                            driver_B: pm.nt.Transform, 
                            driven_transform: pm.nt.Transform) -> tuple[pm.nt.DistanceBetween, pm.nt.MultiplyDivide]:
        """Creates a setup to scale driven based on the distance between driver_A and driver_B

        Args:
            driver_A (pm.nt.Transform): _description_
            driver_B (pm.nt.Transform): _description_
            driven_transform (pm.nt.Transform): _description_

        Returns:
            _type_: _description_
        """
        distance_node = pm.createNode("distanceBetween", n=f"{driven_transform.name()}_distance")
        driver_A.worldMatrix >> distance_node.inMatrix1
        driver_B.worldMatrix >> distance_node.inMatrix2

        stretch_ratio_node = pm.createNode("multiplyDivide", n=f"{driven_transform.name()}_MD")
        stretch_ratio_node.operation.set(2)
        distance_node.distance >> stretch_ratio_node.input1X
        stretch_ratio_node.input2X.set(distance_node.distance.get())
        stretch_ratio_node.outputX >> driven_transform.sx
        stretch_ratio_node.outputX >> driven_transform.sy
        stretch_ratio_node.outputX >> driven_transform.sz

        return (distance_node, stretch_ratio_node)

    def create_ribbon(self, joint_quantity:int):

        # Creation of main groups.
        skn_grp = pm.group(em=True, n=f"{self.name}_skinning")
        follicles_grp = pm.group(em=True, n=f"{self.name}_follicles")
        fol_ref_grp = pm.group(em=True, n=f"{self.name}_ref_follicles",  p=follicles_grp)
        fol_skin_grp   = pm.group(em=True, n=f"{self.name}_skin_follicles", p=follicles_grp)
        fol_ref_grp.it.set(0)
        fol_skin_grp.it.set(0)

        # Register sub-systems in the module.
        self.register_sub_system(skn_grp,       visible=False)
        self.register_sub_system(follicles_grp, visible=False)

        percentage = 1.0 / (joint_quantity - 1)
        factor = 0

        skinning_joints = []
        for i in range(joint_quantity):
            base_name = f"{self.name}_{str(i).zfill(3)}"
            follicle_skn = self.create_follicle(self.surface, [0.5, factor], f"{base_name}_fol_skin")
            follicle_ref = self.create_follicle(self.surface, [1.0, factor], f"{base_name}_fol_ref") # Reference for stretch.

            scale_offset = pm.group(em=True, n=f"{base_name}_scale", p=follicle_skn)
            self.setup_stretch_scaling(follicle_skn, follicle_ref, scale_offset)
            
            skin_joint = pm.joint(None, n=f"{base_name}_skn")
            skinning_joints.append(skin_joint)
            scale_offset.worldMatrix >> skin_joint.offsetParentMatrix

            factor += percentage

            pm.parent(follicle_skn, fol_skin_grp)
            pm.parent(follicle_ref, fol_ref_grp)

        pm.hide(follicles_grp)
        pm.parent(skinning_joints, skn_grp)
        self.register_joints(*skinning_joints)

    def create_ribbon_drivers(self, driver_quantity:int) -> list[pm.nt.Joint]:
        """Creation of joints that will drive the surface movement.

        Args:
            driver_quantity (int): Number of driver joints to create.

        Returns:
            list[pm.nt.Joint]: List of created driver joints.
        """
        #Drivers root group.
        driver_root = pm.group(em=True, n=f"{self.name}_drivers")
        driver_root.it.set(0)
        self.register_sub_system(driver_root, visible=False)

        # Driver creation.
        fol_temp = self.create_follicle(self.surface, [0.5, 0], "temp")
        percentage = 1.0 / (driver_quantity - 1)
        factor = 0
        drivers = []
        for index in range(driver_quantity):
            fol_temp.parameterU.set(factor)
            name = f"{self.name}_{str(index).zfill(3)}_drv"
            driver = pm.joint(None, radius=2.0, n=name)
            
            align_transform(master_transform=fol_temp, slave_transform=driver)
            freeze_transform(driver)
            pm.parent(driver, driver_root)
            
            drivers.append(driver)            
            factor += percentage
        
        pm.delete(fol_temp)
        skinCluster = pm.skinCluster(self.surface, drivers, mi=1)
        skinCluster.rename(f"{self.name}_surface_skinCluster")
        self.register_deformers(skinCluster)
        return drivers

    def create_ribbon_controls(self, drivers: list[pm.nt.Transform]) -> list[pm.nt.Transform]:
        
        # Control root group.
        control_root = pm.group(em=True, n=f"{self.name}_controls")
        self.register_sub_system(control_root, visible=True)
        
        for driver in drivers:
            name = f"{driver.name()[:-4]}_ctrl"
            control = Circle(control_name=name)
            control.create(normal=[1, 0, 0])
            control.align_to(parent=driver)
            control.create_offset(suffix="_root")

            matrix = driver.getMatrix(ws=True)
            control.transform.worldMatrix >> driver.offsetParentMatrix
            driver.setMatrix(matrix, ws=True)
            self.register_controls(control)
            pm.parent(control.offset, control_root)

    def create_skinning_proxy(self) -> None:
        """Creation of skinning proxy to simplify connection with mesh.
        """
        # Skin proxy creation.
        pm.select(self.surface)
        nurb_to_poly = pm.mel.eval(
            f'nurbsToPoly -mnd 1  -ch 1 -f 0 -pt 1 -pc 400 -chr 0.9 -ft 0.01 -mel 0.001 -d 0.1 -ut 1 -un 3 -vt 1 -vn 3 -uch 0 -ucr 0 -cht 0.2 -es 0 -ntr 0 -mrt 0 -uss 1 "{self.surface}";')
        proxy = pm.nt.Transform(nurb_to_poly[0])        
        proxy.rename(f"{self.name}_skin_proxy")
        pm.delete(proxy, ch=True)
        
        # Skin the proxy to the joints in the skinning sub-system.
        skinCluster_name = f"{self.name}_proxy_skinCluster"
        skinCluster = pm.skinCluster(self.joints, proxy, sm=0, mi=5, n=skinCluster_name)
        
        self.skin_proxy = proxy
        self.register_sub_system(proxy, visible=False)        
        self.register_deformers(skinCluster)
        self.root_set.addMember(proxy)

    def build(self):
        super().build()

        ####    CREAR RIBBONS   ####
        self.create_ribbon(self.n_joints)
        drivers = self.create_ribbon_drivers(self.n_ctrl)
        self.create_ribbon_controls(drivers)

        ####    CREATE PROXY    ####
        self.create_skinning_proxy()
        pm.parent(self.surface, self.grp_hid)

        pm.displayInfo(f"\n\n{self.name} build finished.")



