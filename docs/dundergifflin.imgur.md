Module dundergifflin.imgur
--------------------------

Variables
---------
AUTH_ENDPOINT

HTTP_ENDPOINT

Classes
-------
AuthorizationListener 
    A thread that will launch a TCP socket at the host/port specified.

    Will listen for an HTTP request that should come from imgur. It will take the specified URL
    and parse out the authorization code.

    This will likely only need to be done once, though if there is a
    significant time between authentications, it will need to run again.

    Launched from the Imgur client itself, so should not be instantiated directly.

    Parameters
    ----------
    host : string
      The host to listen on. 0.0.0.0 means listen to all connections.
    port : int
      The port to listen on.

    Ancestors (in MRO)
    ------------------
    dundergifflin.imgur.AuthorizationListener
    threading.Thread
    threading._Verbose
    __builtin__.object

    Class variables
    ---------------
    HTTP_RESPONSE

    Instance variables
    ------------------
    code

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

    name
        A string used for identification purposes only.

        It has no semantics. Multiple threads may be given the same name. The
        initial name is set by the constructor.

    port

    received

    Methods
    -------
    __init__(self, host, port)

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
        The threads "run" method.

    setDaemon(self, daemonic)

    setName(self, name)

    start(self)
        Start the thread's activity.

        It must be called at most once per thread object. It arranges for the
        object's run() method to be invoked in a separate thread of control.

        This method will raise a RuntimeError if called more than once on the
        same thread object.

Imgur 
    A context manager that handles an imgur client.

    This should manage its own authentication.

    Parameters
    ----------
    client_id : string
      The client ID supplied from imgur.
    client_secret : string
      The client secret supplied from imgur.
    authorization_listen_address : string
      When first authorizing, this is where the authorization should redirect to.
      See README for more information.
    authorization_listen_port : int
      When first authorizing, this is where the authorization should redirect to.
      See README for more information.
    refresh_token : string
      If already authorized, this token will allow us to get a new oauth2 bearer token.

    Ancestors (in MRO)
    ------------------
    dundergifflin.imgur.Imgur
    __builtin__.object

    Class variables
    ---------------
    AUTHORIZATION_TIMEOUT

    Instance variables
    ------------------
    authorization_listen_address

    authorization_listen_port

    client_id

    client_secret

    refresh_token

    Methods
    -------
    __init__(self, client_id, client_secret, authorization_listen_address, authorization_listen_port, refresh_token=None)

    authenticated_post_request(self, url, **data)
        Send a POST request with URLEncoded form data and the oauth2 bearer token.

        Parameters
        ----------
        url : string
          The URL to send the data to.
        data: **kwargs
          A set of key/value pairs that are URLEncoded into the POST body.

        Returns
        -------
        requests.Response
          The response from said URL.

    post_request(self, url, **data)
        Send a POST request with URLEncoded form data.

        Parameters
        ----------
        url : string
          The URL to send the data to.
        data: **kwargs
          A set of key/value pairs that are URLEncoded into the POST body.

        Returns
        -------
        requests.Response
          The response from said URL.

    upload(self, path, title, description)
        Uploads an image to imgur.

        Will base64 encode the image data.

        Parameters
        ----------
        path : string
          The path to the image file. Can be absolute or relative to the cwd at launch.
        title : string
          The title of the image.
        description : string
          The description of the image.

        Returns
        -------
        string
          The URL to the image, as returned from the imgur API.
