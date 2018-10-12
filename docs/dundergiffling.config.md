Module dundergifflin.config
---------------------------

Classes
-------
Configuration 
    Reads a configuration file of key=value pairs.

    Ignores lines starting with # (comments)
    Will convert values into types, if possible.

    Parameters
    ----------
    configuration_filename : string
      The location of a configuration file. Can be relative or absolute.

    Ancestors (in MRO)
    ------------------
    dundergifflin.config.Configuration
    __builtin__.object

    Methods
    -------
    __init__(self, configuration_filename)
