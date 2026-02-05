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
