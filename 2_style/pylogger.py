"""
content = assignment
course  = Python Advanced
 
date    = 14.11.2025
email   = contact@alexanderrichtertd.com
"""

# Modified: logging.init.py


# EDIT TO WORK UNDER THE CONTEXT OF THE MODULE WHERE IT WAS ORIGINALLY WRITTEN,
# I assumed I can't modify the original attributes of the class returned by currentframe() or it's call name. 
def find_caller():
    """
    Find the stack frame of the caller so that we can note the source
    file name, line number and function name.
    """
    current_frame = currentframe()
    #On some versions of IronPython, currentframe() returns None if
    #IronPython isn't run with -X:Frames.
    if current_frame:
        current_frame = current_frame.f_back
    caller_info = ("(unknown file)", 0, "(unknown function)")

    while hasattr(current_frame, "f_code"):
        frame_code = current_frame.f_code
        file_name = os.path.normcase(frame_code.co_filename)
        
        if not file_name == _srcfile: continue
        
        current_frame = current_frame.f_back
        caller_info = (frame_code.co_filename, current_frame.f_lineno, frame_code.co_name)
        break
    return caller_info

# How can we make this code better?
