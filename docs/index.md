# Module Documentation

- [dundergifflin](dundergifflin.md)
- [dundergifflin.util](dundergifflin.util.md)
- [dundergifflin.database](dundergifflin.database.md)
- [dundergifflin.imgur](dundergifflin.imgur.md)
- [dundergifflin.reddit](dundergifflin.reddit.md)
- [dundergifflin.ffmpeg](dundergifflin.ffmpeg.md)
- [dundergifflin.srt](dundergifflin.srt.md)
- [dundergifflin.color](dundergifflin.color.md)
- [dundergifflin.smtp_alert](dundergifflin.smtp_alert.md)
- [dundergifflin.config](dundergifflin.config.md)
- [dundergifflin.monitor](dundergifflin.monitor.md)

# Getting Started

## Prerequisites

A functioning installation of PostgreSQL is required. If you don't have it installed, `psycopg2` will fail to install.
In addition, GIF conversions uses FFmpeg, to use this portion of the library you will need to install it.

## Installation

Pull down the source code and run `python setup.py install` to install the library directly. You can also run `python setup.py sdist` to generate a `.tar.gz` source distribution and install that in the environment you wish.

# Usage

While this library provides some useful abstractions that may find their way into a variety of reddit bots, it's likely you'd want to use this in a similar manner to the bot this library was created for (dunder_gifflin).

## Preparation

### Media

dundergifflin expects a certain file structure to be in place to understand where media resources are, and the subtitles therein. Create a media directory wherever you please (details on configuration later), and build your files thusly:

```
<media>
 └--S<n>
     ├-- E<m>.<ext>
     └-- E<m>.srt
```

Where `n` is a season number, and `m` is an episode number. The extension can be anything (as long as ffmpeg can use it), but the `.srt` file must be in standard subtitle format. If you have `.mkv` files that have subtitles embedded in them, you can use ffmpeg to extract them.

### Database

Create a PostgreSQL database (you can use `createdb`) and a user (you can use `createuser`) and assign superuser rights to that user for that database.

### APIs

You will need to register your script/application with both Imgur and Reddit. For reddit, you'll need your `client_id`, `client_secret`, a username and a password. For imgur, you'll only need a `client_id` and `client_secret`, but you'll have to do some more work.

#### Imgur

After registering your application with imgur, you'll need to authenticate your user *at least once*. To do this, you'll need to direct a browser to the authorization endpoint (at the time of this writing, it's https://api.imgur.com/oauth2/authorize?client_id=$CLIENT_ID,response_type=code). You will be redirected to your configured redirect address with the authorization code in the GET parameters. dundergifflin provides a handy method for retrieving this information, if you configure your redirect address to an externally-accessible host/port on your machine, it can set up a TCP listener and receive that redirect request and automatically parse it. Using that authorization token, you can receive a refresh token, which you can use for the rest of the duration of your bots life (unless it expires between executions).

# Deployment

dundergifflin provides a command-line utility for launching and monitor reddit bots without the need for other system utilities. Once installed and configured, you can simply run:

```
dundergifflin start <my_script.py>
```

... and your script will be executing in the background. It's important to note the required structure of a script:

```python
def main(conn, logger):
  # To send an event to the monitor, do this:
  conn.send("my_event")
  
  # logger is same logger as configured in the monitor itself
  
  while True:
    logger.debug("I'm looping!")
    time.sleep(5)
```

Run `dundergifflin help` for all commands.

## Deployment Configuration

The default location dundergifflin will look for a configuration file is `$HOME/dundergifflin.cfg`. To use a different location, pass `-c/--config <config_file>` into the command.

The configuration looks like this:

```
# TCP Communication
# -----------------

LISTENER_HOST=0.0.0.0
# Required. This is the host the listen on for commands send via command-line, once the monitor
# has been detached.

LISTENER_PORT=<n>
# Required. Similarly, this is the port. If you want to send commands to the monitor from
# outside of the system, this should be externally accessible, otherwise, any
# free port will do.

# PID File
# -----------------

PIDFILE=/home/<myuser>/.dundergifflin.pid
# Required. This is simply the location of the pidfile.

# Logging
# -----------------

LOG_HANDLER=<handler>
# Optional. If not present, no logging will be done. Currently acceptable values are
# "syslog", "file", and "stream". 
# If "syslog", the following key is also optional:
# LOG_FACILITY=local<n>
# If "file", the following key is required:
# LOG_FILE=<file_path>
# If "stream", the following key is optional:
# LOG_STREAM=sys.stdout

LOG_LEVEL=<LOG_LEVEL>
# Optional. The level passed into the python logging module.

LOG_FORMAT=<format>
# Optional. The logging format.

# Autostart
# -----------------
AUTOSTART=/path/to/my/file
# Optional. Autostart this script when the monitor starts. Can also pass in multiple AUTOSTART= keys to launch more than one.
```

# Examples

See [the main dundergifflin bot's](https://github.com/benjaminpaine/dundergifflin/blob/master/impl/office.py) implementation for an example.

# Contributing
Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests to us.

# License
This project is licensed under the GNU Public License - see the LICENSE.md file for details.
