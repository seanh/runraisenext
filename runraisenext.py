#!/usr/bin/env python2.7
"""A script for launching apps and switching windows."""
import sys
import argparse
import subprocess
import json
import os
import pickle

import wmctrl


def run(command):
    """Run the given shell command as a subprocess."""
    subprocess.call(command, shell=True)


def run_window_spec_command(window_spec, run_function):
    """Run the command from the given window spec, if it has one.

    :param window_spec: the window spec whose command to run
    :type window_spec: dict

    :param run_function: the function to call to run the command
    :type run_function: callable

    """
    command = window_spec.get('command')
    if command:
        run_function(command)


def focus_window(window):
    """Focus the given window.

    :param window: the window to focus
    :type window: wmctrl.Window

    """
    window.focus()


def get_window_spec_from_file(alias, file_):
    """Get the requested window spec from the config file.

    :rtype: dictionary

    """
    specs = json.loads(
        open(os.path.abspath(os.path.expanduser(file_)), 'r').read())
    lowercased_specs = {}
    for key in specs:
        assert key.lower() not in lowercased_specs
        lowercased_specs[key.lower()] = specs[key]
    spec = lowercased_specs[alias.lower()]
    return spec


def pickle_file():
    """Return the path to the file we use to track windows in mru order."""
    return os.path.abspath(os.path.expanduser("~/.runraisenext.pickle"))


def windows():
    """Return the list of open windows in most-recently-used order."""
    with open(pickle_file(), "r") as file_:
        try:
            pickled_window_list = pickle.load(file_)
        except IOError:
            # This happens when the picke file doesn't exist yet, for example.
            pickled_window_list = []
    current_window_list = wmctrl.windows()

    # Remove windows that have been closed since the last time we ran.
    pickled_window_list = [
        w for w in pickled_window_list if w in current_window_list]

    # Add windows that have been opened since the last time we ran to the front
    # of the list.
    for window in current_window_list:
        if window not in pickled_window_list:
            pickled_window_list.insert(0, window)

    return pickled_window_list


def update_pickled_window_list(open_windows, newly_focused_window):
    """Move the newly focused window to the top of the cached list of windows.

    We keep a cached list of windows in most-recently-used order so that
    when switching to a new app we can switch to the app's most recently used
    windows first.

    Each time after focusing a window we call this function to update the
    cached list on disk for the next time we run.

    """
    assert newly_focused_window in open_windows
    open_windows.remove(newly_focused_window)
    assert newly_focused_window not in open_windows, (
        "There shouldn't be more than one instance of the same window in "
        "the list of open windows")
    open_windows.insert(0, newly_focused_window)
    with open(pickle_file(), "w") as file_:
        pickle.dump(open_windows, file_)


def matches(window, window_spec):
    """Return True if the given window matches the given window spec.

    False otherwise.

    A window spec is a dict containing items that will be matched against
    the window object's attributes, for example:

        {'window_id': '0x02a00001',
         'desktop': '0',
         'pid': '4346',
         'wm_class': '.Firefox',
         'machine': 'mistakenot',
         'title': 'The Mock Class - Mock 1.0.1 documentation - Firefox'}

    A window object matches a spec if it has an attribute matching each of
    the items in the spec.

    A spec doesn't have to contain all of the attributes. For example
    {'wm_class': '.Firefox'} will match all windows with a wm_class
    attribute matching ".Firefox".

    Attribute matching is done by looking for substrings. For example a
    wm_class of ".Firefox" will match a window with a wm_class of
    "Navigator.Firefox".

    Window specs can also contain a "command" key (the command to be run to
    launch the app if it doesn't have any open windows) - this key will be
    ignored and the window will match the spec as long as all the other keys
    match.

    """
    for key in window_spec.keys():
        if key == 'command':
            continue
        if window_spec[key].lower() not in getattr(window, key, '').lower():
            return False
    return True


def _unvisited_windows(matching_windows, open_windows):
    """Return the list of matching windows that we haven't looped through yet.

    When we're looping through the windows of an app there's a continuous
    sequence of the app's windows at the top of the list of all open windows
    (which is sorted in most-recently-focused order). These are the windows
    from the app that we've already looped through.

    This function returns the app's windows that aren't part of this list:
    the ones we haven't looped through yet.

    May return an empty list.

    """
    visited_windows = []
    for window in open_windows:
        if window in matching_windows:
            visited_windows.append(window)
        else:
            break
    return [w for w in matching_windows if w not in visited_windows]


def runraisenext(window_spec, run_function, open_windows, focused_window,
                 focus_window_function):
    """Either run the app, raise the app, or go to the app's next window.

    Depending on whether the app has any windows open and whether the app is
    currently focused.

    :param window_spec: the window spec to match against open windows
    :type window_spec: dict

    :param run_function: the function to use to run window spec commands
    :type run_function: callable taking one argument: the window spec

    :param open_windows: the list of open windows
    :type open_windows: list of Window objects

    :param focused_window: the currently focused window, should be one of the
        Window objects from open_windows
    :type focused_window: Window

    :param focus_window_function: the function to call to focus a window
    :type focus_window_function: callable taking one argument: a Window object
        representing the window to be focused

    """
    # If no window spec options were given, just run the command
    # (if there is one).
    if ('id' not in window_spec and
            'desktop' not in window_spec and
            'pid' not in window_spec and
            'wm_class' not in window_spec and
            'machine' not in window_spec and
            'title' not in window_spec):
        run_window_spec_command(window_spec, run_function)
        return

    # If there are no open windows, just run the command (if there is one).
    if not open_windows:
        run_window_spec_command(window_spec, run_function)
        return

    matching_windows = [window for window in open_windows
                        if matches(window, window_spec)]

    if not matching_windows:
        # The requested app is not open, launch it.
        run_window_spec_command(window_spec, run_function)
    elif focused_window not in matching_windows:
        # The requested app isn't focused. Focus its most recently used window.
        focus_window_function(matching_windows[0])
        update_pickled_window_list(open_windows, matching_windows[0])
    elif len(matching_windows) == 1 and focused_window in matching_windows:
        # The app has one window open and it's already focused, do nothing.
        pass
    else:
        # The app has more than one window open, and one of the app's windows
        # is focused. Loop to the app's next window.
        assert focused_window in matching_windows and len(matching_windows) > 1
        unvisited = _unvisited_windows(matching_windows, open_windows)
        if unvisited:
            focus_window_function(unvisited[0])
            update_pickled_window_list(open_windows, unvisited[0])
        else:
            focus_window_function(matching_windows[-1])
            update_pickled_window_list(open_windows, matching_windows[-1])


def parse_command_line_arguments(args):
    """Parse the command-line arguments and return the requested window spec."""

    parser = argparse.ArgumentParser(
        description="a script for launching apps and switching windows",
        add_help=True)

    window_spec_args = parser.add_argument_group("window spec")
    window_spec_args.add_argument(
        '-i', '--id', dest="window_id",
        help="the window ID to look for, e.g. 0x0180000b")
    window_spec_args.add_argument(
        '-d', '--desktop', help="the desktop to look for windows on, e.g. 1")
    window_spec_args.add_argument(
        '-p', '--pid', help="the pid to look for, e.g. 3384")
    window_spec_args.add_argument(
        '-w', '--wm_class',
        help="the WM_CLASS to look for, e.g. Navigator.Firefox")
    window_spec_args.add_argument(
        '-m', '--machine', help="the client machine name to look for")
    window_spec_args.add_argument(
        '-t', '--title',
        help='the window title to look for, e.g. "wmctrl - A command line '
        'tool to interact with an EWMH/NetWM compatible X Window Manager. - '
        'Mozilla Firefox"')

    parser.add_argument(
        '-c', '--command',
        help="the command to run to launch the app, if no matching windows "
        "are found, e.g. firefox")

    parser.add_argument(
        'alias', nargs='?',
        help="the alias of a window spec from the config file to use for "
        "matching windows")

    parser.add_argument(
        "-f", "--file", help="Use a custom config file path",
        default="~/.runraisenext.json")

    args = parser.parse_args(args)

    if args.window_id is not None:
        if (args.desktop or args.pid or args.wm_class or args.machine
                or args.title):
            parser.exit(status=1,
                        message="A window ID uniquely identifies a window, "
                        "it doesn't make sense to give the -i, --id argument "
                        "at the same time as any other window spec arguments")

    # Form the window spec dict.
    if args.alias:
        window_spec = get_window_spec_from_file(args.alias, args.file)
    else:
        window_spec = {}
    if args.window_id is not None:
        window_spec['id'] = args.window_id
    if args.desktop is not None:
        window_spec['desktop'] = args.desktop
    if args.pid is not None:
        window_spec['pid'] = args.pid
    if args.wm_class is not None:
        window_spec['wm_class'] = args.wm_class
    if args.machine is not None:
        window_spec['machine'] = args.machine
    if args.title is not None:
        window_spec['title'] = args.title
    if args.command is not None:
        window_spec['command'] = args.command

    return window_spec


def main(args):
    window_spec = parse_command_line_arguments(args)
    return runraisenext(window_spec, run, windows(),
                        wmctrl.focused_window(), focus_window)


if __name__ == "__main__":
    main(sys.argv[1:])
