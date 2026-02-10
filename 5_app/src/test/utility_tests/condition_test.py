
import importlib

importlib.reload(importlib.import_module("src.utility.attribute_utils"))
importlib.reload(importlib.import_module("src.utility.maya_nodes_utils"))

from src.utility.maya_nodes_utils import create_condition_node, create_multiplyDivide_node
import pymel.core as pm

# Create clean scene.
pm.mel.eval("file -f -new;")

cube = pm.polyCube()[0]
locator = pm.spaceLocator()
joint = pm.joint(None)

condition_node = create_multiplyDivide_node(first_term=cube.translateX, 
                           operation=">", 
                           second_term=5, 
                           if_true_value=[1,2,3], 
                           if_false_value=joint.t, 
                           name="test_condition")

multiply_node = create_multiplyDivide_node(input1=locator.translate, 
                               operation="*", 
                               input2=[2, 4, 6], 
                               name="test_multiply")