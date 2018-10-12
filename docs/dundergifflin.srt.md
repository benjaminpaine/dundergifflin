Module dundergifflin.srt
------------------------

Classes
-------
Subtitles 
    Reads a .srt subtitle file into a dictionary of three-tuples.
    Each three-tuple contains (start_time, end_time, text).

    This will read the entire .srt file into memory, so be careful
    with particularly large files - though even several-hour-long
    movies still have fairly small subtitles.

    Does not understand SSA / ASS. Does not remove tags or anything
    of the sort.

    Parameters
    ----------
    srt_filename : string
      The location of a .srt file. Can be relative or absolute.

    Ancestors (in MRO)
    ------------------
    dundergifflin.srt.Subtitles
    __builtin__.object

    Class variables
    ---------------
    Subtitle

    Instance variables
    ------------------
    subtitles

    Methods
    -------
    __init__(self, srt_filename)
