Module dundergifflin.cmd
------------------------

Variables
---------
parser

subparser_destroy

subparser_restart

subparser_shutdown

subparser_start

subparser_status

subparser_stop

subparsers

Functions
---------
color_failure(msg)
    Returns a message colored red.

color_info(msg)
    Returns a message colored cyan.

color_success(msg)
    Returns a message colored green.

color_warn(msg)
    Returns a message colored yellow.

destroy(args)
    Destroy a bot.

main()

monitor_running(configuration_file)
    Return whether or not the monitor is running.

restart(args)
    Restart a bot.

send_message(configuration_file, timeout, *message)
    Uses the MessageSender to send a message to a TCP socket.

shutdown(args)
    Shutdown all bots and the monitor.

start(args)
    Start the monitor, then start a bot.

start_monitor(configuration_file)
    Starts the monitor.

status(args)
    Return the status of the monitor and all bots.

stop(args)
    Stop a bot.

Classes
-------
MessageSender 
    A small thread that will send a message over a socket,
    and timeout if one is passed.

    Ancestors (in MRO)
    ------------------
    dundergifflin.cmd.MessageSender
    threading.Thread
    threading._Verbose
    __builtin__.object

    Instance variables
    ------------------
    daemon
        A boolean value indicating whether this thread is a daemon thread (True) or not (False).

        This must be set before start() is called, otherwise RuntimeError is
        raised. Its initial value is inherited from the creating thread; the
        main thread is not a daemon thread and therefore all threads created in
        the main thread default to daemon = False.

        The entire Python program exits when no alive non-daemon threads are
        left.

    host

    ident
        Thread identifier of this thread or None if it has not been started.

        This is a nonzero integer. See the thread.get_ident() function. Thread
        identifiers may be recycled when a thread exits and another thread is
        created. The identifier is available even after the thread has exited.

    message

    name
        A string used for identification purposes only.

        It has no semantics. Multiple threads may be given the same name. The
        initial name is set by the constructor.

    port

    Methods
    -------
    __init__(self, configuration_file, *message)

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

    kill(self)

    received(self)

    run(self)

    setDaemon(self, daemonic)

    setName(self, name)

    start(self)
        Start the thread's activity.

        It must be called at most once per thread object. It arranges for the
        object's run() method to be invoked in a separate thread of control.

        This method will raise a RuntimeError if called more than once on the
        same thread object.
