import pymel.core as pm

import src.utility.inspect_utils as inspect_utils

def create_follicle(name: str) -> pm.nt.Transform:
    
    follicle_shape = pm.nt.Follicle()
    follicle_transform = follicle_shape.getParent()

    follicle_shape.outTranslate >> follicle_transform.translate
    follicle_shape.outRotate >> follicle_transform.rotate   

    follicle_transform.rename(name)
    follicle_transform.simulationMethod.set(0)
    follicle_transform.it.set(0)
    
    return follicle_transform

def create_closesPointOnSurface(transform: pm.nt.Transform, surface: pm.nt.NurbsSurface, floating_follicle=False) -> pm.nt.ClosestPointOnSurface:
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

def create_rivet(surface: pm.PyNode, transform: pm.nt.Transform, maintain_offset=True, is_orbital=False, is_constrained=True) -> pm.nt.Transform:
    
    surface_shape = surface if not inspect_utils.is_transform(surface) else surface.getShape()

    follicle = create_follicle(name=f"{transform.name()}_follicle")

    closest = None
    if inspect_utils.is_nurbs_surface(surface):
        closest = create_closesPointOnSurface(transform=transform, surface=surface_shape, floating_follicle=maintain_offset)
        surface.worldSpace[0] >> closest.inputSurface
    elif inspect_utils.is_mesh(surface):
        closest = create_closestPointOnMesh(transform=transform, mesh=surface_shape, floating_follicle=maintain_offset)
        surface.worldMesh[0] >> closest.inMesh
    else:
        pm.error("Surface must be a NURBS surface or a Mesh.")

    closest.parameterU >> follicle.getShape().parameterU
    closest.parameterV >> follicle.getShape().parameterV
    
    if is_constrained:
        pm.parentConstraint(follicle, transform, mo=maintain_offset)
    if not is_orbital:
        pm.delete(closest)

    return follicle

surface, locator = pm.selected()
follicle = create_follicle(name="test_follicle")
rivet = create_rivet(surface= surface, transform=locator)