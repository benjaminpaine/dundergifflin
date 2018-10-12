# dundergifflin
A python library for subtitle-based GIF-generating reddit bots

## Getting Started

### Prerequisites

A functioning installation of PostgreSQL is required. If you don't have it installed, `psycopg2` will fail to install.
In addition, GIF conversions uses FFmpeg, to use this portion of the library you will need to install it.

### Installation

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

# Contributing
Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests to us.

#License
This project is licensed under the GNU Public License - see the LICENSE.md file for details.
