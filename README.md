# dundergifflin
A library for subtitle-based GIF-generating reddit bots

## Getting Started

### Prerequisites

A functioning installation of PostgreSQL is required. If you don't have it installed, `psycopg2` will fail to install.
In addition, GIF conversions uses FFmpeg, to use this portion of the library you will need to install it.

### Installation

Pull down the source code and run `python setup.py install` to install the library directly. You can also run `python setup.py sdist` to generate a `.tar.gz` source distribution and install that in the environment you wish.

# Usage

While this library provides some useful abstractions that may find their way into a variety of reddit bots, it's likely you'd want to use this in a similar manner to the bot this library was created for (dunder_gifflin).

## Preparation

dundergifflin expects a certain file structure to be in place to understand where media resources are, and the subtitles therein. Create a media directory wherever you please (details on configuration later), and build your files thusly:

```
-- <media>
   +-- S<n>
       +--- E<m>.<ext>
       +--- E<m>.srt
```

# Contributing
Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests to us.

#License
This project is licensed under the GNU Public License - see the LICENSE.md file for details.
