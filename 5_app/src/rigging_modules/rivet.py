'''
################################################################################################################
Author: Francisco Guzmán

Content: Rigging module to pin a transform to a surface or create a sliding follicle over a mesh or nurbs surface.
Dependency: pymel.core, src.utility.inspect_utils
Maya Version tested: 2024

How to:
    - Use: Execute the create_river function with the desired parameters.
    - Extend: Add more rivet-related functions as needed.
    - Test: Use pymel.core to create transform nodes and test the functions interactively in Maya.

TODO: IMPLEMENT.
################################################################################################################
'''


import pymel.core as pm

import src.utility.inspect_utils as inspect_utils

def create_follicle(name: str) -> pm.nt.Transform:
    """Follicle creation.

    Args:
        name (str): Name of the follicle.

    Returns:
        pm.nt.Transform: The follicle transform node.
    """
    follicle_shape = pm.nt.Follicle()
    follicle_transform = follicle_shape.getParent()

    follicle_shape.outTranslate >> follicle_transform.translate
    follicle_shape.outRotate >> follicle_transform.rotate   

    follicle_transform.rename(name)
    follicle_transform.simulationMethod.set(0)
    follicle_transform.it.set(0)
    
    return follicle_transform

def create_closesPointOnSurface(transform: pm.nt.Transform, surface: pm.nt.NurbsSurface, floating_follicle=False) -> pm.nt.ClosestPointOnSurface:
    """Create node closestPointOnSurface with its initial setup.

    Args:
        transform (pm.nt.Transform): transform to attach the rivet to.
        surface (pm.nt.NurbsSurface): surface to attach the rivet to.
        floating_follicle (bool, optional): Whether the follicle should float. Defaults to False.

    Returns:
        pm.nt.ClosestPointOnSurface: The closestPointOnSurface node created.
    """
    ## CLOSEST POINT ON SURFACE SETUP.
    closestPointOnSurface_node = pm.createNode("closestPointOnSurface", n=f"{transform.name()}_closestPointOnSurface")
    surface.worldSpace[0] >> closestPointOnSurface_node.inputSurface

    if floating_follicle:
        # FOLLICLE SLIDES OVER SURFACE.
        decompose_matrix_node = pm.createNode("decomposeMatrix", n=f"{transform.name()}_decomposeMatrix")
        transform.worldMatrix >> decompose_matrix_node.inputMatrix
        decompose_matrix_node.outputTranslate >> closestPointOnSurface_node.inPosition
    else:
        # FOLLICLE IS PINNED TO SURFACE.
        position = pm.xform(transform, q=True, ws=True, t=True)
        closestPointOnSurface_node.inPosition.set(position)

    return closestPointOnSurface_node

def create_closestPointOnMesh(transform: pm.nt.Transform, mesh: pm.nt.Mesh, floating_follicle=False) -> pm.nt.ClosestPointOnMesh:
    """Create node closestPointOnMesh with its initial setup.

    Args:
        transform (pm.nt.Transform): transform to attach the rivet to.
        mesh (pm.nt.Mesh): mesh to attach the rivet to.
        floating_follicle (bool, optional): Whether the follicle should float. Defaults to False.

    Returns:
        pm.nt.ClosestPointOnMesh: The closestPointOnMesh node created.
    """
    ## CLOSEST POINT ON MESH SETUP.
    closestPointOnMesh_node = pm.createNode("closestPointOnMesh", n=f"{transform.name()}_closestPointOnMesh")
    mesh.worldMesh[0] >> closestPointOnMesh_node.inMesh

    if floating_follicle:
        decompose_matrix_node = pm.createNode("decomposeMatrix", n=f"{transform.name()}_decomposeMatrix")
        transform.worldMatrix >> decompose_matrix_node.inputMatrix
        decompose_matrix_node.outputTranslate >> closestPointOnMesh_node.inPosition
    else:
        position = pm.xform(transform, q=True, ws=True, t=True)
        closestPointOnMesh_node.inPosition.set(position)

    return closestPointOnMesh_node

def create_NearestPointOnCurve(transform: pm.nt.Transform, curve: pm.nt.NurbsCurve, floating_follicle=False) -> pm.nt.NearestPointOnCurve:
    """Create node nearestPointOnCurve with its initial setup.

    Args:
        transform (pm.nt.Transform): transform to attach the rivet to.
        curve (pm.nt.NurbsCurve): curve to attach the rivet to.
        floating_follicle (bool, optional): Whether the follicle should float. Defaults to False.

    Returns:
        pm.nt.NearestPointOnCurve: The nearestPointOnCurve node created.
    """
    ## NEAREST POINT ON CURVE SETUP.
    nearestPointOnCurve_node = pm.createNode("nearestPointOnCurve", n=f"{transform.name()}_nearestPointOnCurve")
    curve.worldSpace[0] >> nearestPointOnCurve_node.inputCurve

    if floating_follicle:
        decompose_matrix_node = pm.createNode("decomposeMatrix", n=f"{transform.name()}_decomposeMatrix")
        transform.worldMatrix >> decompose_matrix_node.inputMatrix
        decompose_matrix_node.outputTranslate >> nearestPointOnCurve_node.inPosition
    else:
        position = pm.xform(transform, q=True, ws=True, t=True)
        nearestPointOnCurve_node.inPosition.set(position)

    return nearestPointOnCurve_node

def create_rivet(surface: pm.PyNode, transform: pm.nt.Transform, is_orbital=False, is_constrained=True) -> pm.nt.Transform:
    """Create follicle over a Mesh or NurbsSurface to the closest point from the given transform. 
    This function allow th follicle to slide over the surface (orbital mode) or stay pinned, depending on the is_orbital parameter. 
    Optionally, it can constrain the transform to the rivet, depending on the value of the is_constrained parameter.

    Args:
        surface (pm.PyNode): Surface (Mesh or NurbsSurface) to attach the rivet to.
        transform (pm.nt.Transform): Transform to attach the rivet to.
        is_orbital (bool, optional): Whether the follicle should float. Defaults to False.
        is_constrained (bool, optional): Whether the transform should be constrained to the rivet. Defaults to True.

    Returns:
        pm.nt.Transform: The follicle transform created.
    """
    
    surface_shape = surface if not inspect_utils.is_transform(surface) else surface.getShape()

    # Create closest point node depending on the surface type, create a closestPointOnSurface or closestPointOnMesh.
    closest = None
    if inspect_utils.is_nurbs_surface(surface):
        closest = create_closesPointOnSurface(transform=transform, surface=surface_shape, floating_follicle=maintain_offset)
    elif inspect_utils.is_mesh(surface):
        closest = create_closestPointOnMesh(transform=transform, mesh=surface_shape, floating_follicle=maintain_offset)
    else:
        pm.error("Surface must be a NURBS surface or a Mesh.")

    follicle = create_follicle(name=f"{transform.name()}_follicle")
    closest.parameterU >> follicle.getShape().parameterU
    closest.parameterV >> follicle.getShape().parameterV
    
    if is_constrained and not is_orbital:
        pm.parentConstraint(follicle, transform, mo=True)
    if not is_orbital:
        pm.delete(closest)

    return follicle

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

