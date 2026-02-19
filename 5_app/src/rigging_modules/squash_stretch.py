'''
################################################################################################################
Author: Francisco Guzmán

Content: Class to manage creation of Squash and Stretch module.
Dependency: pymel.core, 
            src.core.module_core, 
            src.core.control_lib, 
            src.utility.maya_nodes_utils, 
            src.utility.transform_utils
Maya Version tested: 2024

How to:
    - Use: 
        - Import the module and create an instance of the SquashStretch class, passing the name and components (deformable object).
        - Call the build method to create the module.
        - This module is designed to be used in conjunction with other deformers, 
            such as skin clusters or blendshapes, and not have double transforms.

            e.g:
                from src.rigging_modules.squash_stretch import SquashStretch
                import pymel.core as pm

                sphere = pm.polySphere()[0]
                squash_stretch = SquashStretch("SS", sphere)
                squash_stretch.build()

    - Test: execute the test file in src.test.rigging_modules.squash_stretch_test to see the module in action.
################################################################################################################
'''

import pymel.core as pm

from src.core.control_lib import Sphere, Circle, ColorIndex
from src.core.module_core import RigModule
from src.utility.maya_nodes_utils import create_multiplyDivide_node
from src.utility.transform_utils import create_offset


class SquashStretch(RigModule):
    def __init__(self, name, *components):
        super().__init__(name)
        self.components = components

    def stretch_ratio(self, point_A: pm.nt.Transform, point_B: pm.nt.Transform, mid_point: pm.nt.Transform) -> pm.nt.MultiplyDivide:
        """Generates the setup needed to squash the deformable object when the distance increases or vice versa.

        Args:
            point_A (pm.nt.Transform): First point to measure distance.
            point_B (pm.nt.Transform): Second point to measure distance.
            mid_point (pm.nt.Transform): Point that will be scaled with the stretch ratio.

        Returns:
            pm.nt.MultiplyDivide: The multiplyDivide node that outputs the stretch ratio.
        """
        distance_node = pm.nt.DistanceBetween(n=f"{self.name}_stretch_distance")
        point_A.t >> distance_node.point1
        point_B.t >> distance_node.point2

        stretch_ratio = create_multiplyDivide_node(distance_node.distance.get(), 
                                                   "/", 
                                                   distance_node.distance,
                                                   name= f"{self.name}_stretch_ratio")

        
        stretch_ratio.outputX >> mid_point.sx
        stretch_ratio.outputX >> mid_point.sy
        stretch_ratio.outputX >> mid_point.sz

    def create_lattice(self, components: list) -> pm.nt.Lattice:
        """creates and setup the lattice node that will drive the deformation.

        Args:
            components (list): List of components or deformable objects.

        Returns:
            pm.nt.Lattice: The lattice node created and set up.
        """
        shape, lattice, lattice_base = pm.lattice(components, n=f"{self.name}_lattice", oc=True, dv=[2, 3, 2])
        lattice.it.set(0)
        shape.outsideLattice.set(1)
        shape.local.set(1)
        shape.localInfluenceS.set(3)
        shape.localInfluenceT.set(3)
        shape.localInfluenceU.set(3)

        lattice_grp = pm.group(n=f"{self.name}_lattice_grp", em=True)
        pm.parent(lattice, lattice_base, lattice_grp)
        
        self.register_sub_system(lattice_grp, visible=False)
        self.register_deformers(lattice)
        self.register_deformers(lattice_base)

        return lattice

    def create_clusters(self, lattice_points: list) -> list[pm.nt.Cluster]:
        """Creates and setup the clusters that will drive the lattice deformation.
        Args:
            lattice_points (list): List of the lattice points to create the clusters on.
        Returns:
            list[pm.nt.Cluster]: List of the cluster nodes created and set up.
        """
        clusters_grp = pm.group(n=f"{self.name}_clusters_grp", em=True)
        clusters = []
        for index, points in enumerate(lattice_points):
            name = f"{self.name}_{str(index + 1).zfill(2)}"
            cluster_shape, cluster_transform = pm.cluster(points, n=f"{name}_cls")
            cluster_shape.rename(name + "_clsShape")
            cluster_transform.rename(name + "_cls")
            
            clusters.append(cluster_transform)
        
        self.register_deformers(*clusters)
        pm.parent(clusters, clusters_grp)
        self.register_sub_system(clusters_grp, visible=False)
        return clusters

    def create_controls(self, clusters: list[pm.nt.Cluster]) -> list[Sphere]:
        """Creation of controls to drive clusters.

        Args:
            clusters (list[pm.nt.Cluster]): List of cluster nodes to create controls for.

        Returns:
            list[Sphere]: List of control objects created to drive the clusters.
        """
        controls = []
        for cluster in clusters:
            raw_name = cluster.name().replace("_cls", "") 
            name = f"{raw_name}_ctrl"
            control = Sphere(name)
            control.create()
            control.align_to(cluster)            
            
            pm.parentConstraint(control.transform, cluster.getParent(), mo=True)
            pm.scaleConstraint(control.transform, cluster.getParent(), mo=True)
            
            self.register_controls(control.transform)
            control.create_offset("_root")

            controls.append(control)
        
        return controls

    def create_main_control(self, reference_position: pm.nt.Transform) -> pm.nt.Transform:
        """Creates the main control to drive the module and organizes the hierarchy.
        Args:
            reference_position (pm.nt.Transform): Transform node to align the main control to.
        Returns:
            pm.nt.Transform: The main control transform node.
        """
        main_control = Circle(f"{self.name}_main_ctrl")
        main_control.create(normal=[0, 1, 0])
        main_control.align_to(reference_position)
        main_control.create_offset("_root")
        main_control.shape_scale([2,2,2])
        main_control.shape_line_thick()
        main_control.shape_color_index(ColorIndex.YELLOW)
        pm.parent(main_control.offset, self.grp_vis)

        self.register_controls(main_control.transform)
        self.register_sub_system(main_control.offset, visible=True)
        return main_control
 
    def build(self):
        super().build()

        # Create lattice deformer with the given components and set it up.
        lattice = self.create_lattice(self.components)
        lattice_points = [ lattice.pt[:][index][:] for index in range(3) ]

        clusters = self.create_clusters(lattice_points)
        clusters_offset = [ create_offset(cluster, "_root") for cluster in clusters ]
        controls = self.create_controls(clusters)

        # Main control creation.
        main_control = self.create_main_control(controls[1].transform)
        [pm.parent(control.offset, main_control.transform) for control in controls]

        
        # Constrain mid control to extreme controls.
        pm.pointConstraint(controls[0].transform, controls[2].transform, controls[1].offset, mo=True)
        pm.scaleConstraint(controls[0].transform, controls[2].transform, controls[1].offset, mo=True)        

        # To move module and avoid double transform.
        pm.parentConstraint(main_control.transform, self.grp_hid, mo=True)
        pm.scaleConstraint(main_control.transform, self.grp_hid, mo=True)

        
        self.stretch_ratio(clusters_offset[0], clusters_offset[2], clusters_offset[1])
        
        
        
