Module dundergifflin.ffmpeg
---------------------------

Variables
---------
FONT

Classes
-------
Converter 
    A class to wrap around FFMpeg conversion from video to GIF.

    Parameters
    ----------
    input_file : string
      The input file. Can be absolute or relative to the cwd at execution.
    output_file : string
      The output file. Can be absolute or relative to the cwd at execution.
    overwrite : boolean
      Whether or not to overwrite the output file (if it exists). If this is false,
      this will ask for input when the file exists.

    Ancestors (in MRO)
    ------------------
    dundergifflin.ffmpeg.Converter
    __builtin__.object

    Descendents
    -----------
    dundergifflin.ffmpeg.SubtitleConverter

    Instance variables
    ------------------
    input_args

    input_file

    output_args

    output_file

    overwrite

    Methods
    -------
    __init__(self, input_file, output_file, overwrite=False)

    add_filter(self, **filter_args)
        Add a video filter. This is a special case for add_output_flag where the flag
        is always "-vf". This will allow multiple values for this particular flag.

        Parameters
        ----------
        **kwargs
          key : string
            The name of the filter.
          value : string
            The value passed into the filter.

    add_input_flag(self, flag, value)
        Add an input flag.

        Parameters
        ----------
        flag : string
          The input flag. Will overwrite existing flags.
        value : string
          The flag value to be passed to ffmpeg.

    add_output_flag(self, flag, value)
        Add an output flag.

        Parameters
        ----------
        flag : string
          The output flag. Will overwrite existing flags.
        value : string
          The flag value to be passed to ffmpeg.

    execute(self)
        Executes the conversion using the supplied input and output flags.

        Returns
        -------
        string
          The output of the command.

SubtitleConverter 
    A subclass of Converter used specifically for writing subtitles.

    Parameters
    ----------
    input_file : string
      The input file. Can be absolute or relative to the cwd at execution.
    output_file : string
      The output file. Can be absolute or relative to the cwd at execution.
    overwrite : boolean
      Whether or not to overwrite the output file (if it exists). If this is false,
      this will ask for input when the file exists.
    start : dundergifflin.util.Timestamp
      The timestamp the start the GIF from.
    end : dundergifflin.util.Timestamp
      The timestamp to end the GIF at.
    text : string
      The text to display.
    image_width : int
      The width of the image to generate. Will scale height proportionately.
    text_font : string
      The path to a .ttf font file to use.
    text_color : string
      The text color to pass into ffmpeg.
    text_size_max : int
      The maximum size of the text. Will attempt to scale text down based on how long it is.
    text_offset : int
      The offset for the base of the text, from the bottom, in pixels.
    text_stroke_width : int
      The thickness of the stroke around the text. Always black.

    Ancestors (in MRO)
    ------------------
    dundergifflin.ffmpeg.SubtitleConverter
    dundergifflin.ffmpeg.Converter
    __builtin__.object

    Instance variables
    ------------------
    input_args

    input_file

    output_args

    output_file

    overwrite

    Methods
    -------
    __init__(self, input_file, output_file, overwrite, start, end, text, image_width, text_font, text_color, text_size_max, text_offset, text_stroke_width)

    add_filter(self, **filter_args)
        Add a video filter. This is a special case for add_output_flag where the flag
        is always "-vf". This will allow multiple values for this particular flag.

        Parameters
        ----------
        **kwargs
          key : string
            The name of the filter.
          value : string
            The value passed into the filter.

    add_input_flag(self, flag, value)
        Add an input flag.

        Parameters
        ----------
        flag : string
          The input flag. Will overwrite existing flags.
        value : string
          The flag value to be passed to ffmpeg.

    add_output_flag(self, flag, value)
        Add an output flag.

        Parameters
        ----------
        flag : string
          The output flag. Will overwrite existing flags.
        value : string
          The flag value to be passed to ffmpeg.

    execute(self)
        Executes the conversion using the supplied input and output flags.

        Returns
        -------
        string
          The output of the command.
