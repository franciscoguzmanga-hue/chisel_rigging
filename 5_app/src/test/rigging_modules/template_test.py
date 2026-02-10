'''
################################################################################################################
Author: Francisco Guzmán

Content: Test script for Template module.
Dependency: pymel.core, src.rigging_modules.template
Maya Version tested: 2024

How to:
    - Use: Execute the script in Maya's script editor to run the tests.
    - Test: 
        - The script creates a clean scene and sets up reference joints.
        - It tests the creation of a single template locator and a batch of template locators.
        - It tests moving objects to template locators and moving template locators back to original objects, checking for correct positioning.
################################################################################################################
'''


import importlib
import pymel.core as pm


import src.rigging_modules.template as template_module
importlib.reload(template_module)

from src.rigging_modules import template
from src.utility.math_utils import get_midpoint
# Create clean scene.
pm.mel.eval("file -f -new;")

# Create reference joints.
joints = [pm.nt.Joint(name=f"joint_{i}") for i in range(5)]
[joint.tx.set(1) for joint in joints[1:]]
joints[0].r.set([-30,30,30])
joints.reverse()

################################################################################################
# Create single locator.
single_locator = template.create_template_locator("single_locator")
pm.delete(single_locator)
print("Single locator created and deleted successfully.")

################################################################################################
# Create template locators.
template_locators = template.create_templates(joints)
compare = [locator.hasAttr(template.ATTR_ID) for locator in template_locators]
is_correct = all(compare)
if not is_correct:
    raise Exception("Error: Not all template locators have the original attribute.")

################################################################################################
# Move objects to test template locators.
template_locators[0].setTranslation((5,0,0), worldSpace=True)
template_locators[2].setTranslation((0,5,0), worldSpace=True)
template_locators[4].setTranslation((0,0,5), worldSpace=True)

template.move_objet_to_locator(template_locators)

for joint, locator in zip(joints, template_locators):
    jnt_mtx = joint.getMatrix(worldSpace=True)
    loc_mtx = locator.getMatrix(worldSpace=True)
    if jnt_mtx.isEquivalent(loc_mtx, tol=1e-5): continue
    
    print(print(f"Joint: {joint}, Locator: {locator}"))
    raise Exception("Error: Object did not move to template locator position correctly.")

print("Objects moved to Template locators successfully.")

################################################################################################
# Move locators to original objects.
template_locators[0].setTranslation((5,5,0), worldSpace=True)
template_locators[2].setTranslation((0,5,5), worldSpace=True)
template_locators[4].setTranslation((0,6,5), worldSpace=True)

template.move_locator_to_object(template_locators)


for joint, locator in zip(joints, template_locators):
    jnt_mtx = joint.getMatrix(worldSpace=True)
    loc_mtx = locator.getMatrix(worldSpace=True)
    if jnt_mtx.isEquivalent(loc_mtx, tol=1e-5): continue
    
    print(print(f"Joint: {joint}, Locator: {locator}"))
    raise Exception("Error: Object did not move to template locator position correctly.")

print("Template moved to original objects successfully.")

################################################################################################
# Test constraint to midpoint function.
locator_A = template_locators[0]
locator_B = template_locators[2]
mid_locator = template_locators[4]

template.constraint_to_midpoint(locator_A=locator_A, locator_B=locator_B, locator_mid=mid_locator)

locator_position = mid_locator.getTranslation(worldSpace=True)
expected_position = get_midpoint(locator_A.getTranslation(worldSpace=True), locator_B.getTranslation(worldSpace=True))

if not locator_position.isEquivalent(expected_position, tol=1e-5):
    print(f"Locator Position: {locator_position}, Expected Position: {expected_position}")
    raise Exception("Error: Midpoint constraint did not position the locator correctly.")
    
    
################################################################################################
# Test aim to function.
master_locator = locator_A
slave_locator = mid_locator

template.aim_to(master_locator=master_locator, slave_locator=slave_locator)

slave_orient = slave_locator.getRotation(ws=False)
expected_orient = pm.dt.Vector(-146.155, 21.771, -76.033)
if not slave_orient.isEquivalent(expected_orient, tol=1e-5):
    print(f"Slave Orient: {slave_orient}, Expected Orient: {expected_orient}")
    raise Exception("Error: Aim constraint did not orient the locator correctly.")
    
