
import time
from functools import wraps
import pymel.core as pm


class MessageType:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

def display_message(text: str, message_type=MessageType.INFO):
    if not text: 
        raise ValueError("Message text cannot be empty.")

    display_type = {MessageType.INFO: pm.displayInfo,
                    MessageType.WARNING: pm.displayWarning,
                    MessageType.ERROR: pm.displayError}
    
    if message_type in display_type:
        display_type[message_type](text)
        


def undo_chunk(name):
    def decorator(function):
        @wraps(function)
        def proxy(*args, **kwargs):
            start = time.perf_counter()
            pm.undoInfo(openChunk=True, cn=name)
            
            try:
                display_message(text=f"Executing: {name}", message_type=MessageType.INFO)
                func = function(*args, **kwargs)
                return func
            
            except Exception as ex:
                pm.undoInfo(closeChunk=True)
                error_message = f"{ex}.\n{name}'s Changes reversed"
                display_message(text=error_message, message_type=MessageType.ERROR)
                pm.undo()
                raise ex
            
            finally:
                if pm.undoInfo(q=True, openChunk=True):
                    pm.undoInfo(closeChunk=True)
                end = time.perf_counter()
                elapsed_time = end - start
                time_message = f"Time: {elapsed_time:.2f} seconds"
                display_message(text=time_message, message_type=MessageType.INFO)

        return proxy
    return decorator

