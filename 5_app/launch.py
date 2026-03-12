
import importlib

importlib.reload(importlib.import_module("ui"))
importlib.reload(importlib.import_module("ui.Qt"))
importlib.reload(importlib.import_module("ui.chisel"))
importlib.reload(importlib.import_module("core.control_framework"))
importlib.reload(importlib.import_module("utility.maya_lib"))
importlib.reload(importlib.import_module("utility.common"))
importlib.reload(importlib.import_module("utility.mesh_lib"))
importlib.reload(importlib.import_module("components.helpers"))
importlib.reload(importlib.import_module("components.squash_stretch"))
importlib.reload(importlib.import_module("components.ribbon"))


from ui.chisel import showUI
if __name__ == "__main__":
    chisel= showUI()

