Module dundergifflin.smtp_alert
-------------------------------

Classes
-------
SMTPAlert 
    A very small wrapper around SMTPLib that will send an "alert".
    Sends from yourself to yourself, with no subject or attachments.

    Parameters
    ----------
    host : string
      The host of the smtp server.
    port : string
      The port of the smtp server.
    username : string
      The user to login to the smtp server with.
    password : string
      The password to login to the smtp server with.
    use_tls : boolean
      Whether or not to use TLS when communicating with the server.

    Ancestors (in MRO)
    ------------------
    dundergifflin.smtp_alert.SMTPAlert
    __builtin__.object

    Instance variables
    ------------------
    host

    password

    port

    use_tls

    username

    Methods
    -------
    __init__(self, host, port, username, password, use_tls=True)

    send(self, message)
        Sends an alert using the supplied SMTP parameters.

        Parameters
        ----------
        message : string
          The message to send.
