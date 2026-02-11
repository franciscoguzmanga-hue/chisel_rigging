'''
Content: Collection of methods to simplify utility nodes creation to create more readable code.
Dependency: pymel.core, src.utility.attribute_utils, src.utility.inspect_utils
Maya Version tested: 2024

Author: Francisco Guzmán
Email: francisco.guzmanga@gmail.com

How to:
    - Use: Import the module and call the functions as needed.
'''

import pymel.core as pm
from src.utility.attribute_utils import connect_or_assign_value
from src.utility.inspect_utils import is_mesh, is_nurbs_surface


def create_condition_node(first_term=0, operation="==", second_term=0, if_true_value=[0, 0, 0], if_false_value=[1, 1, 1], name="condition") -> pm.nt.Condition:
    """
        Coded simplification of the use of Condition node in Node Editor to work more visually in text editor.
        Examples: condition(miNode.translateX, ">", yourNode.customAttribute, ifTrue= thatNode.scale, ifFalse=[1,1,1] )
        Args:
            firstTerm: 	int, float or Attribute,	first term of the condition, if is Attribute, will be connected, else will be assigned. (DEFAULT: 0)
            operation: 	string, 					conditional operation, might be: ==, !=, >,  >=, <, <=. (DEFAULT: "==")
            secondTerm:	int, float or Attribute,	second term of the condition, if is Attribute, will be connected, else will be assigned. (DEFAULT: 0)
            ifTrue: 	int, float or Attribute, 	resulting value if condition gives TRUE, if is Attribute, will be connected, else will be assigned. (DEFAULT: [0,0,0])
            ifFalse: 	int, float or Attribute, 	resulting value if condition gives FALSE, if is Attribute, will be connected, else will be assigned. (DEFAULT: [1,1,1])
            name: 		string, 					name that will be given to the condition node. (DEFAULT: "")

        Returns: node, condition node.
	"""
    operation_dict = {"==": 0, "!=": 1, ">": 2, ">=": 3, "<": 4, "<=": 5}

    condition_node = pm.nt.Condition(n=name) if name else pm.nt.Condition()
    condition_node.operation.set(operation_dict[operation])

    # Set first term. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(first_term, condition_node.firstTerm)
    
    # Set second term. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(second_term, condition_node.secondTerm)

    # Set ifTrue value. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(if_true_value, condition_node.colorIfTrue)    
    
    # Set ifFalse value. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(if_false_value, condition_node.colorIfFalse)

    return condition_node

def create_multiply_divide_node(input1=[0, 0, 0], operation="*", input2=[1, 1, 1], name="multiplyDivide") -> pm.nt.MultiplyDivide:
    """
        Coded simplification of the use of MultiplyDivide node in Node Editor.
        Inputs could be int, float, Attribute, nt.Vector or list(number, number, number).
        If the input is Attribute, it will be connected, else the value will be assigned to the input.
        
        Usage Example: create_multiply_divide_node(miNode.translateX, "/", yourNode.customAttribute, name="activator_MULT" )

	"""
    # MultiplyDivide node creation.
    operation_dict = {"": 0, "*": 1, "/": 2, "**": 3}
    multiply_node = pm.nt.MultiplyDivide(n=name) if name else pm.nt.MultiplyDivide()
    multiply_node.operation.set(operation_dict[operation])

    # Set input1. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(input1, multiply_node.input1)
    
    # Set input2. If it's an attribute, connect it, else set the value.
    connect_or_assign_value(input2, multiply_node.input2)
    
    return multiply_node

def create_remapValue_node(input_min=0, input_max=1, output_min=0, output_max=0, name="remapValue") -> pm.nt.RemapValue:
    """Coded simplification of the use of remapValue node in Node Editor.
        Inputs could be int, float, Attribute.
        If the input is Attribute, it will be connected, else the value will be assigned to the input.
    Args:
        input_min (int, float): Minimum value of the input range. (DEFAULT: 0)
        input_max (int, float): Maximum value of the input range. (DEFAULT: 1)
        output_min (int, float): Minimum value of the output range. (DEFAULT: 0)
        output_max (int, float): Maximum value of the output range. (DEFAULT: 0)
        name (str): Name that will be given to the remapValue node. (DEFAULT: "")
    
    """
    remap_node = pm.shadingNode("remapValue", asUtility=True, n=name)

    connect_or_assign_value(input_min, remap_node.inputMin)
    connect_or_assign_value(input_max, remap_node.inputMax)

    connect_or_assign_value(output_min, remap_node.outputMin)
    connect_or_assign_value(output_max, remap_node.outputMax)
    return remap_node

def create_reverse(input: pm.Attribute, *outputs: pm.Attribute, name="reverse") -> pm.nt.Reverse:
    """Code simplification of the use of reverse node in Node Editor."""
    name = name if name else input.node().name() + "_reverse"
    reverse = pm.nt.Reverse(n=name)
    connect_or_assign_value(input, reverse.input)
    for output in outputs:
        connect_or_assign_value(reverse.outputX, output)
    return reverse

def create_blend_matrix(master:pm.nt.Transform, ws=True, *weights: pm.nt.Transform, name="blendMatrix") -> pm.nt.BlendMatrix:
    """Code simplification of the use of blendMatrix node in Node Editor to work more visually in text editor."""
    name = name if name else master.name() + "_blendMatrix"
    blend_matrix = pm.nt.BlendMatrix(n=name)

    matrix_at = master.worldMatrix if ws else master.matrix
    matrix_at >> blend_matrix.inputMatrix
    influence = 1 / (len(weights) + 1) if len(weights) > 0 else 0
    for index, weight in enumerate(weights):
        weight.worldMatrix >> blend_matrix.target[index].targetMatrix
        blend_matrix.target[index].weight.set(influence)
    return blend_matrix

def create_decompose_matrix(source_matrix: pm.Attribute, name="decomposeMatrix") -> pm.nt.DecomposeMatrix:
    """Code simplification of the use of decomposeMatrix node in Node Editor to work more visually in text editor."""
    name = name if name else source_matrix.node().name() + "_decomposeMatrix"
    node = pm.nt.DecomposeMatrix(n=name)

    source_matrix >> node.inputMatrix
    return node

def create_follicle(name="follicle") -> pm.nt.Transform:
    """Code simplification of the use of follicle node in Node Editor to work more visually in text editor.
    Args:
        name (str): Name that will be given to the follicle node and its transform parent.
    Return:
        pm.nt.Transform: follicle transform node.
    """
    name = name if name else "follicle"
    follicle_shape = pm.nt.Follicle(n=name)
    follicle_shape.simulationMethod.set(0)
    transform_node = follicle_shape.getParent()
    transform_node.rename(name)

    follicle_shape.outTranslate >> transform_node.t
    follicle_shape.outRotate >> transform_node.r

    return transform_node

def create_closest_point_on_mesh(name: str, mesh_transform: pm.nt.Transform, reference_object: pm.nt.Transform,) -> pm.nt.Transform:
    """Code simplification of the use of closestPointOnMesh node in Node Editor to work more visually in text editor."""
    closest_node = pm.nt.ClosestPointOnMesh(n=name)
    mesh_transform.getShape().worldMesh >> closest_node.inMesh

    decompose = create_decompose_matrix(reference_object.worldMatrix)
    decompose.outputTranslate >> closest_node.inPosition

    return closest_node

def create_closest_point_on_surface(name: str, surface_transform: pm.nt.Transform, reference_object: pm.nt.Transform) -> pm.nt.Transform:
    """Code simplification of the use of closestPointOnSurface node in Node Editor to work more visually in text editor."""
    closest_node = pm.nt.ClosestPointOnSurface(n=name)
    surface_transform.getShape().worldSpace >> closest_node.inputSurface

    decompose = create_decompose_matrix(reference_object.worldMatrix)
    decompose.outputTranslate >> closest_node.inPosition

    return closest_node

def create_rivet(name: str, surface: pm.nt.Transform, position_object: pm.nt.Transform) -> pm.nt.Transform:
        follicle = create_follicle(name)

        decompose = create_decompose_matrix(position_object.worldMatrix)

        if is_mesh(surface):
            closest_node = create_closest_point_on_mesh(f"{name}_closestPointOnMesh", surface, position_object)
            surface.getShape().worldMesh >> follicle.getShape().inputMesh
        if is_nurbs_surface(surface):
            closest_node = create_closest_point_on_surface(f"{name}_closestPointOnSurface", surface, position_object)
            surface.getShape().worldSpace >> follicle.getShape().inputSurface

        decompose.outputTranslate >> closest_node.inPosition
        follicle.parameterU.set(closest_node.parameterU.get())
        follicle.parameterV.set(closest_node.parameterV.get())

        pm.delete(closest_node, decompose)
        return follicle

