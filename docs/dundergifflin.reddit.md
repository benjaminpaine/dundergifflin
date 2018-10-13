Module dundergifflin.reddit
---------------------------

Classes
-------
CommentCrawler 
    A process that will crawl through comments on a given subreddit.

    Parameters
    ----------
    reddit : praw.Reddit
      The reddit instance.
    subreddit_name : string
      The name of the subreddit (without /r/).
    comment_function : function(praw.Comment) returns string
      The function to call against a new comment. If the function returns a string, 
      a reply will be sent with that string.
    reply_function : function(praw.Comment)
      The function to call when a comment is a reply to a comment made by the bot.
    vote_function : function(praw.Comment)
      The function to call when a comment is one made by the bot. Effectively this will
      only be called once, when the reddit crawler finds it's own comment immediately
      after it is posted.

    Ancestors (in MRO)
    ------------------
    dundergifflin.reddit.CommentCrawler
    multiprocessing.process.Process
    __builtin__.object

    Instance variables
    ------------------
    authkey

    comment_function

    daemon
        Return whether process is a daemon

    exitcode
        Return exit code of process or `None` if it has yet to stop

    ident
        Return identifier (PID) of process or `None` if it has yet to start

    name

    pid
        Return identifier (PID) of process or `None` if it has yet to start

    reddit

    reply_function

    subreddit_name

    user

    vote_function

    Methods
    -------
    __init__(self, reddit, subreddit_name, comment_function, reply_function, vote_function)

    is_alive(self)
        Return whether process is alive

    join(self, timeout=None)
        Wait until child process terminates

    run(self)
        The processes "run" function. The subreddit stream, on initialization, will return the
        the last ~100 comments made in the subreddit, then iterate infinitely.

        If a comment is made by the bot, it will call vote_function.
        If a comment is a response to a comment made by the bot, it will call both reply_function and comment_function.
        If a comment is new, it will call comment_function.

        comment_function will not be ran against a comment if the bot has already replied to this comment.

    start(self)
        Start child process

    terminate(self)
        Terminate process; sends SIGTERM signal or uses TerminateProcess()

CrawlerMonitor 
    A class that monitors the various processes used in a crawler, and restarts them
    if they die.

    Parameters
    ----------
    crawler : RedditCrawler
      The crawler to monitor on.

    Ancestors (in MRO)
    ------------------
    dundergifflin.reddit.CrawlerMonitor
    threading.Thread
    threading._Verbose
    __builtin__.object

    Class variables
    ---------------
    MONITOR_INTERVAL

    Instance variables
    ------------------
    crawler

    daemon
        A boolean value indicating whether this thread is a daemon thread (True) or not (False).

        This must be set before start() is called, otherwise RuntimeError is
        raised. Its initial value is inherited from the creating thread; the
        main thread is not a daemon thread and therefore all threads created in
        the main thread default to daemon = False.

        The entire Python program exits when no alive non-daemon threads are
        left.

    ident
        Thread identifier of this thread or None if it has not been started.

        This is a nonzero integer. See the thread.get_ident() function. Thread
        identifiers may be recycled when a thread exits and another thread is
        created. The identifier is available even after the thread has exited.

    name
        A string used for identification purposes only.

        It has no semantics. Multiple threads may be given the same name. The
        initial name is set by the constructor.

    restarts

    Methods
    -------
    __init__(self, crawler)

    getName(self)

    isAlive(self)
        Return whether the thread is alive.

        This method returns True just before the run() method starts until just
        after the run() method terminates. The module function enumerate()
        returns a list of all alive threads.

    isDaemon(self)

    is_alive(self)
        Return whether the thread is alive.

        This method returns True just before the run() method starts until just
        after the run() method terminates. The module function enumerate()
        returns a list of all alive threads.

    join(self, timeout=None)
        Wait until the thread terminates.

        This blocks the calling thread until the thread whose join() method is
        called terminates -- either normally or through an unhandled exception
        or until the optional timeout occurs.

        When the timeout argument is present and not None, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof). As join() always returns None, you must call
        isAlive() after join() to decide whether a timeout happened -- if the
        thread is still alive, the join() call timed out.

        When the timeout argument is not present or None, the operation will
        block until the thread terminates.

        A thread can be join()ed many times.

        join() raises a RuntimeError if an attempt is made to join the current
        thread as that would cause a deadlock. It is also an error to join() a
        thread before it has been started and attempts to do so raises the same
        exception.

    run(self)
        The threads "run" method. Monitors the processes on the crawler.

    setDaemon(self, daemonic)

    setName(self, name)

    start(self)
        Start the thread's activity.

        It must be called at most once per thread object. It arranges for the
        object's run() method to be invoked in a separate thread of control.

        This method will raise a RuntimeError if called more than once on the
        same thread object.

    stop(self)
        Internal. Stop the monitor thread.

    stopped(self)
        Internal. Whether or not the monitor thread has stopped.

MentionCrawler 
    A process that will crawl through a users' metnions.

    Parameters
    ----------
    reddit : praw.reddit
      The reddit instance
    mention_function : function(praw.Comment)
      The function to call on a mention that hasn't already been viewed.

    Ancestors (in MRO)
    ------------------
    dundergifflin.reddit.MentionCrawler
    multiprocessing.process.Process
    __builtin__.object

    Class variables
    ---------------
    EVALUATION_INTERVAL

    Instance variables
    ------------------
    authkey

    daemon
        Return whether process is a daemon

    exitcode
        Return exit code of process or `None` if it has yet to stop

    ident
        Return identifier (PID) of process or `None` if it has yet to start

    ignored_subreddits

    mention_function

    name

    pid
        Return identifier (PID) of process or `None` if it has yet to start

    reddit

    stopped

    user

    vote_function

    Methods
    -------
    __init__(self, reddit, vote_function, mention_function, ignored_subreddits=[])

    is_alive(self)
        Return whether process is alive

    join(self, timeout=None)
        Wait until child process terminates

    run(self)
        The processes "run" function.

    start(self)
        Start child process

    stop(self)
        Marks the crawler as stopped.

    terminate(self)
        Terminate process; sends SIGTERM signal or uses TerminateProcess()

RedditCrawler 
    The reddit crawler that a user should instantiate.

    Parametrs
    ---------
    client_id : string
      The client ID, as specified by reddit.
    client_secret : string
      The client secret, as specified by reddit.
    username : string
      The username to log into reddit with.
    password : string
      The password to log into reddit with.
    user_agent : string
      The user agent to instantiate the reddit instance with. Not useful, but required.
    comment_function : function(praw.Comment) returns string
      The function to call against new comments. If a string is returned, a comment will be made as a reply to this comment.
    vote_function : function(praw.Comment)
      The function to call against own comments. Likely _should_ update the local database.
    reply_function : function(praw.Comment)
      The function to call against replies to your comments.
    subreddits : *list
      All of the subreddits to monitor.

    Ancestors (in MRO)
    ------------------
    dundergifflin.reddit.RedditCrawler
    __builtin__.object

    Instance variables
    ------------------
    client_id

    client_secret

    comment_function

    crawled_subreddits

    ignored_subreddits

    mention_function

    password

    reply_function

    user_agent

    username

    vote_function

    Methods
    -------
    __init__(self, client_id, client_secret, username, password, user_agent, comment_function, vote_function, reply_function, mention_function, crawled_subreddits=[], ignored_subreddits=[])

VoteCrawler 
    A process that will periodically get the bots' comments.

    Does not specify a limit, but reddit API has its own limit of 1000. So, effectively,
    this will get the last 1,000 comments and then call the vote_function on them.

    Parameters
    ----------
    reddit : praw.Reddit
      The reddit instance.
    vote_function : function(praw.Comment)
      The function to call against each comment.

    Ancestors (in MRO)
    ------------------
    dundergifflin.reddit.VoteCrawler
    multiprocessing.process.Process
    __builtin__.object

    Class variables
    ---------------
    EVALUATION_INTERVAL

    Instance variables
    ------------------
    authkey

    daemon
        Return whether process is a daemon

    exitcode
        Return exit code of process or `None` if it has yet to stop

    ident
        Return identifier (PID) of process or `None` if it has yet to start

    name

    pid
        Return identifier (PID) of process or `None` if it has yet to start

    reddit

    stopped

    vote_function

    Methods
    -------
    __init__(self, reddit, vote_function)

    is_alive(self)
        Return whether process is alive

    join(self, timeout=None)
        Wait until child process terminates

    run(self)
        The processes "run" method. Grabs comments in order of creation (descending),
        then calls the supplied vote_function on them.

    start(self)
        Start child process

    stop(self)
        Marks the crawler as stopped.

    terminate(self)
        Terminate process; sends SIGTERM signal or uses TerminateProcess()
