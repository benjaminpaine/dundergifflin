Module dundergifflin.monitor
----------------------------

Functions
---------
import_bot(bot_path)
    Imports a module using its path.

    Will (hopefully) obscure import methods for python 2/3.

    Parameters
    ----------
    bot_path : string
      The path to a .py file to run as a bot.

    Returns
    -------
    module
      The imported module.

Classes
-------
BotMonitor 
    A monitoring process to run bots.

    A .pid file exists that should be used to ensure only one monitoring process runs.
    A .cfg file exists where individual bot paths are placed.

    Use command-line tools to interact with the process monitor.

    Parameters
    ----------
    directory : string
      The location to store the .pid and .cfg files.

    Ancestors (in MRO)
    ------------------
    dundergifflin.monitor.BotMonitor
    multiprocessing.process.Process
    __builtin__.object

    Class variables
    ---------------
    Bot

    BotProcess

    EventSink

    RequestListener

    Instance variables
    ------------------
    authkey

    bots

    configuration

    configuration_file

    daemon

    exitcode
        Return exit code of process or `None` if it has yet to stop

    ident
        Return identifier (PID) of process or `None` if it has yet to start

    killed

    logger

    name

    pid
        Return identifier (PID) of process or `None` if it has yet to start

    stopped

    Methods
    -------
    __init__(self, configuration_file=u'/home/thrall/dundergifflin.cfg')

    bot_status(self)
        Get the status of all bots and their peg counts.

        Returns
        -------
        string
          The status of the monitor, all bots, and their peg counts.

    check(self, *args)
        Runs each bots' "check" function.

    destroy_bot(self, bot_path=None)
        Stop a bot and remove it from the monitor.

        Parameters
        ----------
        bot_path : string
          The path to a .py file to run as a bot.

        Returns
        -------
        string
          The status of the command.

    dispatch_command(self, *command)
        Receive a command from the request listener, and attempt to dispatch it.

        Parameters
        ----------
        *command : *string
          The command, followed by arguments.

    find_named_bot(self, bot_name)
        Find a bot by name.

        Parameters
        ----------
        bot_name : string
          The name of a bot.

        Returns
        -------
        BotMonitor.Bot

    is_alive(self)
        Return whether process is alive

    join(self, timeout=None)
        Wait until child process terminates

    kill(self, *args)
        Shuts down the monitor and all bots.

    restart_bot(self, bot_path=None)
        Restart a bot by path.

        Parameters
        ----------
        bot_path : string
          The path to a .py file to run as a bot.

        Returns
        -------
        string
          The status of the command.

    run(self)
        The process to run. Will fork from the shell when creating.

        Traps SIGINT and SIGTERM to shutdown gracefully.
        Traps SIGHUP to force a configuration reload.

    shutdown(self, *args)
        Triggers the process monitor to exit its loop.

    start(self)
        Start child process

    start_bot(self, bot_path=None)
        Start a bot if it doesn't exist. If it exists and is stopped, restart it.

        Parameters
        ----------
        bot_path : string
          The path to a .py file to run as a bot.

        Returns
        -------
        string
          The status of the command.

    stop_bot(self, bot_path=None)
        Stop a bot, but keep it to be restarted later.

        Parameters
        ----------
        bot_path : string
          The path to a .py file to run as a bot.

        Returns
        -------
        string
          The status of the command.

    terminate(self)
        Terminate process; sends SIGTERM signal or uses TerminateProcess()

MonitorConfiguration 
    A metaclass for the monitor configuration that checks for required configuration keys.

    Ancestors (in MRO)
    ------------------
    dundergifflin.monitor.MonitorConfiguration
    dundergifflin.config.Configuration
    __builtin__.object

    Class variables
    ---------------
    REQUIRED_KEYS

    Methods
    -------
    __init__(self, configuration_filename)
