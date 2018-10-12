Module dundergifflin.database
-----------------------------

Classes
-------
Database 
    A small database wrapper around a PostgreSQL database.

    Builds only one database connection, not a pool.
    Uses a context manager to open/close the connection on enter/exit.

    Parameters
    ----------
    host : string
      The host of the database. If deployed on the same machine, localhost.
    port : int
      The port to access the database. The default PostgreSQL port is 5432.
    database_name : string
      The name of the database to connect to.
    username : string
      The username of the user. Should be a superuser of the target database.
    password : string
      The password for said user.

    Ancestors (in MRO)
    ------------------
    dundergifflin.database.Database
    __builtin__.object

    Descendents
    -----------
    dundergifflin.database.SubtitleDatabase

    Instance variables
    ------------------
    database_name

    host

    password

    port

    username

    Methods
    -------
    __init__(self, host, port, database_name, username, password)

    get_connection(self)
        Retrieve a connection to the database.

        Will test the connection if one already exists, or recreate it if it has been closed.

        Returns
        -------
        psycopg2.connection
          A psycopg2 connection object to the database.

    test_connection(self)
        Tests a connection by executing a simple query.

        Returns
        -------
        boolean
          Whether or not the connection is working.

DunderDatabase 
    A wrapper around the database used for the main dunder gifflin bot.

    Parameters are the same as above, but also creates tables for tracking users and comments,
    as well as a generic key-value store.

    Ancestors (in MRO)
    ------------------
    dundergifflin.database.DunderDatabase
    dundergifflin.database.SubtitleDatabase
    dundergifflin.database.Database
    __builtin__.object

    Class variables
    ---------------
    DUNDER_MIGRATION

    SUBTITLE_MIGRATION

    Instance variables
    ------------------
    concatenation_depth

    database_name

    directory

    host

    password

    port

    username

    Methods
    -------
    __init__(self, host, port, database_name, username, password, directory, concatenation_depth=2)

    find_subtitles(self, text, limit=10)
        Find the closest subtitles to a line of text.

        Returns in descending order of likeness, where likeness is 1 minus the pg_trgrm operation "<->".
        A likeness of 1 represents a 100% match (excluding punctuation and capitalization).

        Parameters
        ----------
        text : string
          The text to search for.
        limit : int
          The number of rows to return.

        Returns
        -------
        list
          season : int
            The season this subtitle is from.
          episode : int
            The episode this subtitle is from.
          start_index : int
            The starting index of the line.
          end_index : int
            The ending index of the line.
          start_time : string
            The start time of the line, in the form HH:MM:SS.ff
          end_time : string
            The end time of the line, in the form HH:MM:SS.ff
          subtitle : string
            The actual subtitle, including punctuation.
          likeness : float
            The likeness of this line, between 1 (~exact match) and 0 (no match).
          comment_count : int
            The number of times this/these line(s) has/have been referenced.
          comment_score : float
            The average comment score of this/these line(s).

    get_connection(self)
        Retrieve a connection to the database.

        Will test the connection if one already exists, or recreate it if it has been closed.

        Returns
        -------
        psycopg2.connection
          A psycopg2 connection object to the database.

    get_key(self, key)
        Get the value from the key/value store.

        Parameters
        ----------
        key : string
          An unbounded key to search against.

        Returns
        -------
        list
          value : string
            The value stored in the database. Can be None.
          exp_time : datetime.datetime
            The expiration time, if set. Can be None.
          mod_time : datetime.datetime
            The last time this value was modified. Can be None.

    get_user_ignored(self, username)
        Get whether or not a user has requested to be ignored.

        Parameters
        ----------
        username : string
          The username of the requested user.

        Returns
        -------
        boolean
          Whether or not the user has requested to be ignored.

    get_user_uses(self, username)
        Get the number of time a user has used the service.

        Parameters
        ----------
        username : string
          The username of the requested user.

        Returns
        -------
        int
          How many times the user has used the service.

    ignore_user(self, username)
        Set a user to be ignored.

        Parameters
        ----------
        username : string
          The username of the requested user.

    increment_user_uses(self, username)
        Increment a users' uses of the service.

        Parameters
        ----------
        username : string
          The username of the requested user.

    test_connection(self)
        Tests a connection by executing a simple query.

        Returns
        -------
        boolean
          Whether or not the connection is working.

    upsert_comment(self, comment_id, score, season, episode, start_index, end_index)
        Insert or update a comment into the comment database.

        Parameters
        ----------
        comment_id : string
          The comment ID returned from Reddit. Primary key.
        score : int
          The score of the comment from Reddit.
        season : int
          The season of the responded image / comment.
        episode : int
          The episode of the responded image / comment.
        start_index : int
          The starting line index of the responded image / comment.
        end_index : int
          The ending line index of the responded image / comment.

    upsert_key(self, key, value, exp_time=None)
        Set a key/value pair in the key/value store.

        Parameters
        ----------
        key : string
          An unbounded key - the primary key.
        value : string
          An unbounded value - what to store.
        exp_time : datetime.datetime:
          The time to expire this key. Purely for informational purposes, does not
          influence the store itself. Can be None.

SubtitleDatabase 
    A wrapper around a subtitle database.

    Will ensure the database is migrated, then crawl the configured directory for .srt files.
    If the .srt file is not in the database, or has changed since the last crawl, will upsert its data.

    Parameters
    ----------
    host : string
      The host of the database. If deployed on the same machine, localhost.
    port : int
      The port to access the database. The default PostgreSQL port is 5432.
    database_name : string
      The name of the database to connect to.
    username : string
      The username of the user. Should be a superuser of the target database.
    password : string
      The password for said user.
    directory : string
      The directory in which to find .srt files. There is an expected structure
      of the directory:
        -- <top_directory>
           +-- S<n>
               +-- E<m>.srt
      For each S<n>, a "season" will be parsed, and each E<m> represents an episode.
    concatenation_depth : int
      Determines how deep to concatenate lines into the database. 
      
      Concatenating lines will take multiple subtitles and concatenate them together (with newlines),
      then set the start time to be the start of the first line, and the end time to the end of
      the last time.

      This will multiply the storage required and lookup time of each episode by the number
      passed in.

    Ancestors (in MRO)
    ------------------
    dundergifflin.database.SubtitleDatabase
    dundergifflin.database.Database
    __builtin__.object

    Descendents
    -----------
    dundergifflin.database.DunderDatabase

    Class variables
    ---------------
    SUBTITLE_MIGRATION

    Instance variables
    ------------------
    concatenation_depth

    database_name

    directory

    host

    password

    port

    username

    Methods
    -------
    __init__(self, host, port, database_name, username, password, directory, concatenation_depth=2)

    find_subtitles(self, text, limit=10)
        Find the closest subtitles to a line of text.

        Returns in descending order of likeness, where likeness is 1 minus the pg_trgrm operation "<->".
        A likeness of 1 represents a 100% match (excluding punctuation and capitalization).

        Parameters
        ----------
        text : string
          The text to search for.
        limit : int
          The number of rows to return.

        Returns
        -------
        list
          season : int
            The season this subtitle is from.
          episode : int
            The episode this subtitle is from.
          start_index : int
            The starting index of the line.
          end_index : int
            The ending index of the line.
          start_time : string
            The start time of the line, in the form HH:MM:SS.ff
          end_time : string
            The end time of the line, in the form HH:MM:SS.ff
          subtitle : string
            The actual subtitle, including punctuation.
          likeness : float
            The likeness of this line, between 1 (~exact match) and 0 (no match).

    get_connection(self)
        Retrieve a connection to the database.

        Will test the connection if one already exists, or recreate it if it has been closed.

        Returns
        -------
        psycopg2.connection
          A psycopg2 connection object to the database.

    test_connection(self)
        Tests a connection by executing a simple query.

        Returns
        -------
        boolean
          Whether or not the connection is working.
