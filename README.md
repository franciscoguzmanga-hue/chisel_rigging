# 🪚 Chisel – Maya Rigging Productivity Tool (In Development)

**Chisel** is a precision rigging toolkit designed to handle the "surgery" of rig setup. 

While an **autorig** is the hammer that does the heavy lifting, **Chisel** is the scalpel. It focuses on eliminating the repetitive clicks and manual overhead involved in modifying, refining, and polishing rigs—whether they were built in-house or received from external studios.

---

## 🚀 Features

### 🏗️ Creation & Hierarchy
* **Smart Creation:** Generate Locators, Joints, and Groups exactly at selection points, could be joints, transforms or any component.
* **Auto-Hierarchy:** Build complex parent-child structures based on your selection order in a single click.

### 🧬 Deformation & Skinning
* **Joint Extraction:** Quickly identify and extract skinned joints from any mesh.
* **Mass Skin Copy:** Transfer skinning data from a source object to multiple selections (supports both transforms and components).
* **Renaming deformers:** When diagnosing is useful to have every deformer named after the mesh, surface that they are influencing.

### 🎮 Control Rigging
* **Advanced Controls:** Create controls with automatic offsets and constraints.
* **Direct Connections:** Streamline the process of connecting attributes or driving transforms.
* **Customization:** Visual tools to modify control shapes, orientation, and color coding.

### 🤖 Automated Setups
* **Modules:** Instant creation of 
    - Limb FK / IK chains.
    - Ribbon setups.
    - Squash & Stretch setups.
* **Blendshapes:** Automatic target assignment to save time on facial or corrective rigging.
* **Local Rigs:** Rapid setup of localized transform systems.

### 🧪 The "Surgery" Module
* **Node Management:** Powerful tools to rename, find, and manage `constraints`, `skinClusters`, and `blendshape` nodes.
* **Attribute Tools:** Batch create proxy attributes and modify default values across multiple nodes.

### 🧹 Cleanup & Filtering
* **Rig Sanitization:** Unlock nodes, remove "unknown" or unused nodes, and toggle axis/joint visibility.
* **Advanced Filtering:** Select specifically by type (Joint, Locator, Mesh, Nurbs) or by hierarchy position (Leaf nodes vs. Parent nodes).

