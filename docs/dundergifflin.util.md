Module dundergifflin.util
-------------------------

Variables
---------
logger

Functions
---------
flatten(*lists)
    Flattens multiple lists into one list.

    Parameters
    ----------
    *lists : list<T>
      A list of items. If any item is a list, will recursively call flatten().

    Returns
    -------
    list
      All items in the list, flattened into one list.

md5sum(path)
    Determine the md5sum of a file.

    Parameters
    ----------
    path : string
      The path to the file. Can be absolute or relative to the cwd at execution.

    Returns
    -------
    string
      The hex string that is the md5 hash of the file.

process_is_alive(pid)

url_encode(**kwargs)
    Encodes keys and values into form / parameter strings.

    Obscures python 2/3 implementations.

    Parameters
    ----------
    **kwargs
      Key/value pairs.

    Returns
    -------
    string
      The URL-encoded string of all kwargs.

url_join(*args)
    Joins arguments together into a URL. Similar to os.path.join.

    Parameters
    ----------
    *args : list<string>
      A list of arguments to join into a URL.

    Returns
    -------
    string
      The joined URL.

Classes
-------
Timestamp 
    A "timestamp" object, similar to datetime.time.
    Permits addition and subtraction of timestampts to get durations.

    Parameters
    ----------
    milliseconds : int
      The number of milliseconds in this timestamp.
    seconds : int
      The number of seconds in this timestamp.
    minutes : int
      The number of minutes in this timestamp.
    hours : int
      The number of hours in this timestamp.

    Ancestors (in MRO)
    ------------------
    dundergifflin.util.Timestamp
    __builtin__.object

    Static methods
    --------------
    from_string(string)
        Builds a timestamp object from a string.

        Parameters
        ----------
        string : string
          A string in the form of "HH:MM:SS.ff". Can omit from right to left.

    Instance variables
    ------------------
    hours

    milliseconds

    minutes

    seconds

    Methods
    -------
    __init__(self, milliseconds=0, seconds=0, minutes=0, hours=0)

    total_seconds(self)
        The total seconds in a timestamp.

        Returns
        -------
        float
          The total number of seconds represented by a timestamp.
