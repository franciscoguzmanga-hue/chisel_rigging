
from ui.builder_controller import BuilderController
from ui.edit_controller import EditController
from ui.surgery_controller import SurgeryController

class MainController:
    def __init__(self, view):
        self.view = view
        
        self.builder = BuilderController(self.view)
        self.edit    = EditController(self.view)
        self.surgery = SurgeryController(self.view)