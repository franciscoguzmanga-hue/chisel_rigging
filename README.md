# Welcome to Chisel
As riggers, we all rely on auto-rigs to handle the heavy lifting. They are essential for speed, yet they often leave us with a significant amount of manual "cleanup" or custom refinement. Many of the functions needed for these tasks already exist deep within the auto-rig's code, but they aren't always exposed for direct user interaction.

Chisel is designed to bridge that gap. It is a toolset built to accelerate the rigging workflow while remaining agnostic of the specific auto-rigging system you are using. Whether you need to add custom modules, dissect an existing rig, or diagnose structural issues for improvement, Chisel puts the "hidden" power of rigging logic directly into your hands.

## Core Philosophy
If the auto-rig is a hammer that builds the frame, Chisel is the sculpting tool used for the refinement. Our core development is driven by three principles:

* **Contextual Efficiency:** Keeping the most important and frequently used functions within immediate reach.
* **Minimal Friction:** Executing complex, multi-step rigging actions with as few clicks as possible.
* **Non-Destructive:** Only acts on selection to avoid accidents.

## Features
- Auto-rig agnostic.
- **Surgery center:** rename deformers, find drivers or inputs, unlock nodes, etc.
- **Smart filters:** Isolate or clean selection by object type.
- **Helpers:** Visual aid for pivots, bend volumes or save pivots.
- **Control Curve management:** Create, connect, edit or reset any control curve.
- **Quick Setups:** create Proxy attributes, Rivets, Orbitals, Squash & Stretch and Ribbons with ease.
- Fast workflow!
- **_More._**

# Quick start
## Requirements
* Maya 2024+
* Python 3.10.8
* Pymel 11.5.051.5.00

## Installing Pymel
- Open CMD.
- Go to maya python source: `C:\Program Files\Autodesk\Maya202X\bin\` or find the folder that contains `mayapy.exe`
- Execute: `mayapy -m pip install pymel`
- Test Pymel inside Maya's script editor: `import pymel.core as pm`

_Reference: [Autodesk Documentation](https://help.autodesk.com/view/MAYAUL/2025/ENU/?guid=GUID-2AA5EFCE-53B1-46A0-8E43-4CD0B2C72FB4)_

## Installing Chisel
1. Copy the content inside Maya Document's folder: 
`C:\Users\[USER]\Documents\maya\202X\scripts`
2. Run:
```
import chisel_rigging.launch as chisel
chisel.run()
```

# Core Interface
<img width="1247" height="683" alt="image" src="https://github.com/user-attachments/assets/018f8882-1e37-4fc0-92a2-3331cc72a453" />

|  |  |
| - | - |
| **Edit** | Utility belt for object creation, heararchy cleanup and alignment.
| **Controls** | Control shapes management, mirroring, sizes, automated connections and offset on creation.
| **Components** | Complex node-network generators (Ribbons, Rivets, Squash & Stretch).
| **Surgery** | The diagnostic hub and forensic tools for debugging and auditing existing rigs.
| **Filters (footer)** | Selection power-tools to isolate or filter out Joints, Locators, Meshes, Nurbs Curves or leaf nodes in hierarchy.

# Try Chisel
## Example 01: Tail FK
![maya_TFN6NhKZaN](https://github.com/user-attachments/assets/eefc9098-a7f8-4319-a57b-b0ed6f72d874)

1. Create a Cylinder with height=10 and height subdivisions=30. 
> I suggest to rotate to be horizontal to work with the second case as well.
2. Open Chisel. In the **Edit tab**, under _Create On_ set the mode to _Cente._ Then select an edge or vertex Loop and press the **Joint** button to create a Joint at the center. Do this as many times as you like.
3. When you are ready with the joint creation, select every joint in order of hierarchy and press on **Build Hierarchy** and adjust orientation if you like.
4. Now we can move on to _Controls tab_, there choose **Connect Constraint** and **Zero Out Root** and pick any control from the options.

Now you have an FK chain with all the required connections to work properly and ready to animate, no matter if the skinning was created before or not.

**Tail FK benchmark:**
* Manual: 3 minutes.
* Chisel: 40 seconds.


## Example 02: Quick Ribbon.
![maya_JDA8eZS4hp](https://github.com/user-attachments/assets/ded190cf-11fd-4df2-a496-f4ee7caa2d62)

1. Go to **Components tab > Ribbon Component.**
2. Select every joint from the previous example.
3. Change the module name to something more interesting. I will choose `Tail`.
4. Under Ribbon Creation press **Create.**
> Or create a surface like I did in the GIF. Then select the nurb surface and press **Create** on ribbon creation.
5. Done, we have a ribbon! 

Not that impresive yet, though. Now, let's connect it to the skinning.

6. On the outliner, find the selection set of the module, mine is `Tail_sets` and select `Tail_skin_proxy`
7. Go to **Component tab > Quick Setups** pick a source Mesh with the **<<** button, select the previous `Cylinder` and finally click on **Copy**
> You could refine the skinning in the proxy and then copy to the `Cylinder`, then it will have cleaner deformation.

Done. We have a Simple Ribbon setup with it's skin assigned. You may try to transform the controls into an FK chain, or add an FK chan over the ribbon controls.

Ribbon Benchkmark:
* Manual: 30+ minutes.
* Chisel: 46 seconds.

## ⏱️ Performance Benchmarks
| Task | Manual Time | Chisel Time | Improvement |
|  -   | -           | -           | -           |
| Tail FK chain | ~3 minutes | 40 seconds | 4.5x Faster
| Ribbon Setup | 30+ minutes | 46 seconds | 39x Faster

# Feedback & Support
Chisel is constantly evolving. If you find a bug, have a feature request, or just want to show what you've built:

🟢 Report an Issue: [GitHub Issues](https://github.com/franciscoguzmanga-hue/chisel_rigging/issues/new/choose)  
🟢 Documentation: Check the full [User Guide](https://github.com/franciscoguzmanga-hue/chisel_rigging/wiki/User-Guide) for more details.
