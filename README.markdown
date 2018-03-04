[![Build Status](https://travis-ci.org/seanh/flitter.svg)](https://travis-ci.org/seanh/flitter)
[![Coverage Status](https://img.shields.io/coveralls/seanh/flitter.svg)](https://coveralls.io/r/seanh/flitter)
[![Latest Version](https://img.shields.io/pypi/v/flitter.svg)](https://pypi.python.org/pypi/flitter/)
[![Downloads](https://img.shields.io/pypi/dm/flitter.svg)](https://pypi.python.org/pypi/flitter/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/flitter.svg)](https://pypi.python.org/pypi/flitter/)
[![Development Status](https://img.shields.io/pypi/status/flitter.svg)](https://pypi.python.org/pypi/flitter/)
[![License](https://img.shields.io/pypi/l/flitter.svg)](https://pypi.python.org/pypi/flitter/)


Flitter
=======

Flitter makes launching apps and switching between windows as fast and easy
as possible:

* F1 launches Firefox, or focuses the Firefox window if Firefox is already
  running.
* If there's more than one Firefox window open, repeatedly hitting F1 cycles
  through them.
* F2 does the same for gVim.
* And so on, binding all your most-frequently used apps to the function keys
  or other keyboard shortcuts (you configure the apps and shortcuts yourself).
* I have F1..F10 bound to my 10 most frequently used apps, and F11 cycling
  through all other windows that don't belong to my top ten apps.
* When moving between apps Flitter raises each app's most recently used window
  first, and when cycling through an app's windows it goes through them in
  most-recently-used-first order.

Compared to using the mouse or traditional fast window switching shortcuts
(like Alt-Tab), with Flitter:

* You don't need to keep track of which apps are open and closed.
  Let the computer do that. F1 just takes you to Firefox, opening it if
  necessary. You can only Alt-Tab to an app if it's open, if not you have to
  do something else to launch it.
* You never need to use the mouse to open apps or switch windows.
* You never need to use two hands or two finger contortions to press multiple
  keys at once (Alt+Tab, Tab, Tab...). Just hit one function key.
* You only need to use one key (perhaps hitting it
  repeatedly) to get to a window, no Alt+Tab,Tab,Tab to get to an app then
  Alt+\`,\`,\` or Alt+down,left,left to get to the window.
* You don't need to look at or think about anything on screen other than the
  app windows themselves as they're focused (no finding the right icon in an
  Alt-Tab dialog)
* Very finger memory compatible, your hands will quickly memorize F1 for
  Firefox, F5 for Thunderbird, F8 for Skype, and you'll be switching apps at
  the speed of thought.

Repeatedly hitting F1 to cycle through Firefox windows doesn't scale well if
you have dozens of Firefox windows open.
But personally I usually have just one, and never more than three or four,
windows per app (and then sometimes several tabs within each window) and
Flitter works great for me (focusing the most recently used windows first makes
a big difference).

Binding each function key to an app doesn't scale when you have more apps than
function keys. You can just fall back on Alt-Tab for apps outside of your top
12, but `flitter --others` (see below) gives you a key for cycling through
windows that don't belong to any of your bound apps. I find this lets me avoid
Alt-Tab entirely.


Requirements
------------

Flitter requires Python 2.7, [wmctrl](http://tomas.styblo.name/wmctrl/) and
works with any WMH/NetWM compatible X Window Manager (Gnome, Unity, Openbox...)

It doesn't work on Windows, OS X, or non-WMH/NetWM linux environments yet,
although porting should be possible (just replace
[wmctrl.py](flitter/wmctrl.py)
with something capable of interacting with your desktop's windows).


Installation
------------

First install wmctrl. On Debian or Ubuntu, just:

    $ sudo apt-get install wmctrl

Then install Flitter:

    $ pip install flitter

You should now be able to run the `flitter` command in your shell.
Run `flitter -h` for help.


Configuration & Usage
---------------------

Copy the [default configuration file](flitter/flitter.json)
to `~/.flitter.json`. This is a [JSON](http://json.org/) file containing a list
of _window specs_. Window specs are how Flitter knows which windows belong to
which app. Each spec has a name, such as `Firefox`, and a number of properties
that are matched against the properties of your open windows to decide whether
each window is a Firefox window or not. For example:

        "Firefox": {
            "wm_class": ".Firefox",
            "command": "firefox"
        },

This window spec will match all windows whose WM_CLASS property contains the
string ".Firefox" (in other words, all Firefox windows).

To have Flitter raise a Firefox window or launch Firefox, run it with the
spec's name as the command-line argument:

    $ flitter firefox

Flitter doesn't have built-in support for keyboard shortcuts.
You just use whatever mechanism your window manager provides to bind keyboard
shortcuts to flitter commands.

To see a list of all your open windows and their properties so you can write
window specs for them, run `wmctrl -lxp` (see `man wmctrl` for more info).

The `"command"` part of the spec is the command that Flitter will run to launch
Firefox, if it finds no Firefox windows.

This way of identifying windows is quite flexible. You can go beyond the simple
one app per keyboard shortcut model, for example:

* A key to switch to the Firefox window showing Google Calender or open Google
  Calender in a new Firefox window
* A key to switch to the Gnome Terminal window running WeeChat or open a new
  Gnome Terminal window with the WeeChat profile

The full set of attributes that you can include in a window spec is:

`window_id`
  The unique ID of an open window, e.g. 0x0180000b

`desktop`
  The desktop that the window is on, e.g. 1

`pid`
  The process ID of the window, e.g. 3384

`wm_class`
  The WM_CLASS of the window, e.g. Navigator.Firefox

`machine`
  The client machine that the window belongs to

`title`
  The window title


Development Install
-------------------

To install Flitter in a virtual environment for development first install
virtualenv, on Debian or Ubuntu do:

    $ sudo apt-get install python-virtualenv

Then create and activate a Python virtual environment and install Flitter into
it:

    $ virtualenv flitter
    $ . flitter/bin/activate
    $ cd flitter
    $ pip install -e 'git+https://github.com/seanh/flitter.git#egg=flitter'

`which flitter` should now report the flitter binary in your virtualenv.

To run the tests do:

    $ cd src/flitter
    $ pip install -r dev-requirements.txt
    $ nosetests

To run the tests and produce a test coverage report, do:

    $ nosetests --with-coverage --cover-inclusive --cover-erase --cover-tests

To upload a new release of Flitter to PyPI ans GitHub:

1. Update the version number in [setup.py](setup.py).
2. `python setup.py sdist`
3. `python setup.py sdist upload`
4. `git commit setup.py -m "Release version X.Y.Z"`
5. `git tag X.Y.Z`
6. `git push`
7. `git push --tags`
