'''
Content: Testing script for Ribbon module.
Dependency: pymel.core, src.rigging_modules.ribbon
Maya Version tested: 2024

Author: Francisco Guzmán
Email: francisco.guzmanga@gmail.com

How to:
    - Use: Call the script in Maya's script editor to execute the test.
    - Test: 
        - The script creates a ribbon setup using the Ribbon module.
        - Functionality can be tested moving controls.
'''

import importlib
import pymel.core as pm

import src.rigging_modules.ribbon as ribbon_module
importlib.reload(ribbon_module)

from src.rigging_modules.ribbon import Surface, SurfaceOrient, Ribbon

# Create clean scene.
pm.mel.eval("file -f -new;")

# Create reference joints.
joints = [pm.nt.Joint(name=f"joint_{i}") for i in range(5)]
[joint.tx.set(1) for joint in joints[1:]]
joints[0].r.set([-30,30,30])

# Create surface to be used as ribbon base.
surface = Surface(name="test_surface")
surface.create(joints=joints, width=1.0, normal=SurfaceOrient.Y_UP)

# Build ribbon.
pm.delete(joints)
joints_quantity = len(joints)
ribbon = Ribbon(name="lizard_tail", surface=surface.transform, section_joints=2, ctrl_quantity=joints_quantity)
ribbon.build()