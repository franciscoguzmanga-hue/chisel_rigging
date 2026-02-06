import pymel.core as pm


class Sticky:
    def __init__(self, start, end, name):
        self.name = name
        self.start = start
        self.end = end
        self.mid = None

        self.sticky_attr_name = "stick"
        self.create_mid_space(start, end)
        self.start_sticky   = self.create_sticky(self.start, self.mid, f"{self.name}_A")
        self.end_sticky     = self.create_sticky(self.end,   self.mid, f"{self.name}_B")
        
    def create_mid_space(self, point_A, point_B):
        mid_name = f"{self.name}_mid"
        mid = pm.nt.Transform(mid_name) if pm.objExists(mid_name) else pm.spaceLocator(n= mid_name)
            
        blend = pm.nt.BlendMatrix(n= f"{self.name}_blend")
        point_A.worldMatrix >> blend.inputMatrix
        point_B.worldMatrix >> blend.target[0].targetMatrix
        blend.target[0].weight.set(0.5)
        blend.outputMatrix >> mid.offsetParentMatrix
        self.mid = mid

    def create_sticky(self, point_A, point_B, name):
        mid_name = f"{name}_sticky"
        mid = pm.nt.Transform(mid_name) if pm.objExists(mid_name) else pm.spaceLocator(n=mid_name)

        blend_name = f"{name}_blendSticky"
        blend = pm.nt.BlendMatrix(n=blend_name)
        point_A.worldMatrix >> blend.inputMatrix
        point_B.worldMatrix >> blend.target[0].targetMatrix
        blend.outputMatrix >> mid.offsetParentMatrix

        if not point_B.hasAttr(self.sticky_attr_name):
            pm.addAttr(point_B, ln=self.sticky_attr_name, max=1, min=0, dv=0, k=True)
        point_B.attr(self.sticky_attr_name) >> blend.target[0].weight
        return mid
        #blend.target[0].weight.set(0.5)


class Zipper:
    def __init__(self, zipper_control, *points):
        self.points = points
        self.n_joints = len(points[0])
        self.horizontal_delta = 10/(self.n_joints+1)
        self.slope = self.calculate_slope()
        self.zipper_control = zipper_control

    def calculate_slope(self):
        """
        slope = (Y0-Y1)/X0-X1
        """
        return 1/self.horizontal_delta

    def calculate_intercept(self, x_pos):
        """
        Y= slope*X + intercept
        intercept = Y - slope * X
        """
        return 1 - self.slope * x_pos

    def set_zipper_behavior(self, x_position, sticky_attr, zipper_attr, zipper_spread_attr, name):
        """
            variable: float. Value when Y=1.
            Y = mX + b
        """
        object_set = pm.nt.ObjectSet("test_set")
        slope_mult_X = pm.nt.Multiply(n=f"{name}_slope_X")
        zipper_attr >> slope_mult_X.input[0]
        slope_mult_X.input[1].set(x_position)
        
        add_intersect = pm.nt.Multiply(n=f"{name}_add_intersect")
        slope_mult_X.output >> add_intersect.input[0]
        zipper_spread_attr >> add_intersect.input[1]
        #add_intersect.input[1].set(1)

        clamp_node = pm.nt.Clamp(n=f"{name}_clamp_sdk")
        add_intersect.output >> clamp_node.inputR
        clamp_node.minR.set(0)
        clamp_node.maxR.set(1)

        if "012" in name:
            object_set.addMember(slope_mult_X)
            object_set.addMember(add_intersect)
            object_set.addMember(clamp_node)

        inputs = sticky_attr.inputs(plugs=True)
        if len(inputs)==0:
            clamp_node.outputR >> sticky_attr

        else:
            print(f"ASDF: {sticky_attr.inputs(plugs=True)} >> {sticky_attr}")
            equalize_mult = pm.nt.Sum(n=f"{name}_equalize")
            equalize_mult.output >> sticky_attr

            if "012" in name:
                object_set.addMember(equalize_mult)

            for index, input in enumerate(inputs):
                input >> equalize_mult.input[index]
            clamp_node.outputR >> equalize_mult.input[len(inputs)]


        #add_intersect.output >> sticky_attr

    def set_zipper_behavior_SDK(self, driver_attr, driven_attr, driver_value, driven_value, step):
        pm.setDrivenKeyframe(driven_attr, currentDriver= driver_attr, dv= driver_value,      v= 0)
        pm.setDrivenKeyframe(driven_attr, currentDriver= driver_attr, dv= driver_value+step*4, v= 1)


    def build_zipper(self, array_A, array_B, zipper_attr, zipper_spread_attr):
        for start, end in zip(array_A, array_B):
            index = self.points[0].index(start)
            name = f"{start.name()}"
            sticky = Sticky(start, end, name)

            sticky_attr = sticky.mid.attr(sticky.sticky_attr_name)
            self.set_zipper_behavior_SDK(driver_attr  = zipper_attr,
                                         driven_attr  = sticky_attr,
                                         driver_value = index * self.horizontal_delta,
                                         driven_value = 0,
                                         step         = self.horizontal_delta)
            """self.set_zipper_behavior(x_position=index * self.horizontal_delta,
                                     sticky_attr=sticky_attr,
                                     zipper_attr=zipper_attr,
                                     zipper_spread_attr=zipper_spread_attr,
                                     name=name)"""


    def build(self):
        attr_A = "zipper_A"
        attr_B = "zipper_B"
        attr_zipper_spread = "zipper_spread"
        if not self.zipper_control.hasAttr(attr_A):
            pm.addAttr(self.zipper_control, ln=attr_A, min=0, dv=0, k=True)
        if not self.zipper_control.hasAttr(attr_B):
            pm.addAttr(self.zipper_control, ln=attr_B, min=0, dv=0, k=True)
        if not self.zipper_control.hasAttr(attr_zipper_spread):
            pm.addAttr(self.zipper_control, ln=attr_zipper_spread, min=0, dv=1, k=True)


        upp_joints = self.points[0]
        dwn_joints = self.points[1]

        self.build_zipper(upp_joints, dwn_joints, self.zipper_control.zipper_A, self.zipper_control.zipper_spread)

        upp_joints.reverse()
        dwn_joints.reverse()

        self.build_zipper(upp_joints, dwn_joints, self.zipper_control.zipper_B, self.zipper_control.zipper_spread)



        """stickys = []
        for start, end in zip(upp_joints, dwn_joints):
            index = self.points[0].index(start)
            name = f"{start.name()}_{str(index).zfill(3)}"
            sticky = Sticky(start, end, name)
            stickys.append(sticky)


            print(sticky.sticky_attr_name)
            attr_name = sticky.sticky_attr_name
            sticky_attr = sticky.mid.attr("stick")

            self.set_zipper_behavior(index*self.horizontal_delta, sticky_attr, transform.zipper_spread)"""

        

        





upp_joints = pm.nt.ObjectSet("upp_joints_set").members()
dwn_joints = pm.nt.ObjectSet("dwn_joints_set").members()

upp_joints.sort()
dwn_joints.sort()

zipper_control = pm.nt.Transform("zipper_control")
zipper = Zipper(zipper_control, upp_joints, dwn_joints)
zipper.build()


