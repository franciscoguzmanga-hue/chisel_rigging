"""
content = assignment
course  = Python Advanced
 
date    = 14.11.2025
email   = contact@alexanderrichtertd.com
"""

"""
CUBE CLASS

1. CREATE an abstract class "Cube" with the functions:
   translate(x, y, z), rotate(x, y, z), scale(x, y, z) and color(R, G, B)
   All functions store and print out the data in the cube (translate, rotate, scale and color).

2. ADD an __init__(name) and create 3 cube objects.

3. ADD the function print_status() which prints all the variables nicely formatted.

4. ADD the function update_transform(ttype, value).
   "ttype" can be "translate", "rotate" and "scale" while "value" is a list of 3 floats.
   This function should trigger either the translate, rotate or scale function.

   BONUS: Can you do it without using ifs?

5. CREATE a parent class "Object" which has a name, translate, rotate and scale.
   Use Object as the parent for your Cube class.
   Update the Cube class to not repeat the content of Object.

"""



# I moved the update_transform function to Object class, 
# since I felt it made more sense to have it there with the other transform functions.

# I kept the print_status and set_color functions in the Cube class, assuming that are specific to Cube due the instructions, 
# but I think they could also be moved to Object.

# I renamed the functions as setters, due the clash of name with scale, so python can differentiate between the function and the variable.

# I like the definition of ABC to avoid another developer to instance directly the Object class, 
# although I'm not sure if it's what you meant by "abstract class" in the instructions, or simply create a base class.
from abc import ABC, abstractmethod
class Object(ABC):
   def __init__(self, name):
      self.name = name
      self.translation = (0, 0, 0)
      self.rotation = (0, 0, 0)
      self.scale = (1, 1, 1)

   def set_translation(self, x, y, z):
      self.translation = (x, y, z)
      print(f"Translated to: {self.translation}")

   def set_rotation(self, x, y, z):
      self.rotation = (x, y, z)
      print(f"Rotated to: {self.rotation}")

   def set_scale(self, x, y, z):
      self.scale = (x, y, z)
      print(f"Scaled to: {self.scale}")

   def update_transform(self, ttype, value):
      transform_functions = {
         "translate": self.set_translation,
         "t": self.set_translation,
         "rotate": self.set_rotation,
         "r": self.set_rotation,
         "scale": self.set_scale,
         "s": self.set_scale
      }
      try:
         transform_functions[ttype]( *value )
      except KeyError as ex:
         print(f"Unknown transform type: {ttype}")
         print(f"Valid types are: {', '.join(transform_functions.keys())}")

   @abstractmethod
   def print_status(self):
      pass


class Cube(Object):
   def __init__(self, name):
      super().__init__(name)
      self.color = (1, 1, 1)
   
   def set_color(self, R, G, B):
      self.color = (R, G, B)
      print(f"Color set to: {self.color}" )

   def print_status(self):
      status_str = (f"Cube: {self.name}\n"
                    f"Translation: {self.translation}\n"
                    f"Rotation: {self.rotation}\n"
                    f"Scale: {self.scale}\n"
                    f"Color: {self.color}\n")
      print(status_str)


# Call to classes.
cube_A = Cube("name_of_A")
cube_A.update_transform("translate", (1, 2, 3))
cube_A.set_color((1, 0, 0))

cube_B = Cube("name_of_B")
cube_B.update_transform("rotate", (45, 0, 0))
cube_B.set_color((0, 1, 0))

cube_C = Cube("name_of_C")
cube_C.update_transform("scale", (2, 2, 2))
cube_C.set_color((0, 0, 1))

cube_A.print_status()
cube_B.print_status()
cube_C.print_status()
