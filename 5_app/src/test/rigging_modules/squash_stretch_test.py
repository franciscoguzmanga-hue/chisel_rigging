'''
################################################################################################################
Author: Francisco Guzmán

Content: Test file of the squash and stretch module.
Dependency: src.rigging_modules.squash_stretch
Maya Version tested: 2024

How to:
    - Use: Open in Maya's script editor and run.
    - Test: 
        - This test will create a sphere and apply the module.
        - This test will create a functional module of SS on the sphere.
        - The squash and stretch main module moves the module, but not the mesh. This way the animator can adjust the SS behavior.
        - 
################################################################################################################
'''


import importlib

import pymel.core as pm

importlib.reload(importlib.import_module("src.utility.transform_utils"))
importlib.reload(importlib.import_module("src.utility.attribute_utils"))
importlib.reload(importlib.import_module("src.utility.maya_nodes_utils"))
importlib.reload(importlib.import_module("src.core.control_lib"))
importlib.reload(importlib.import_module("src.utility.maya_nodes_utils"))
importlib.reload(importlib.import_module("src.rigging_modules.squash_stretch"))

from src.rigging_modules.squash_stretch import SquashStretch


# Create clean scene.
pm.mel.eval("file -f -new;")

sphere = pm.polySphere()[0]

squash_stretch = SquashStretch("SS", sphere)
squash_stretch.build()