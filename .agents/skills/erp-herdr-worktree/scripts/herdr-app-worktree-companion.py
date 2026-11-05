#!/usr/bin/env python3
"""Herdr App backend. Terminal addresses are not legacy Herdr pane IDs."""
from __future__ import absolute_import, print_function

import json
import os
import subprocess
import sys


APP = os.environ.get('HERDR_APP_BIN_PATH', 'herdr-app')
CORE = os.environ.get('HC_BIN_PATH', 'hc')


def command(binary, *args):
    output = subprocess.check_output([binary] + list(args), timeout=15)
    result = json.loads(output)
    if not isinstance(result, dict) or result.get('error'):
        raise ValueError('Herdr command failed: {0}'.format(result))
    return result


def app_do(name, **args):
    return command(APP, 'do', name, json.dumps(args))


def caller_context():
    caller = os.environ.get('HC_TERMINAL_ID')
    if not caller:
        raise ValueError('HC_TERMINAL_ID is required; stopping.')
    matches = []
    for space in command(APP, 'ls')['spaces']:
        for tab in space['tabs']:
            for terminal in tab['terminals']:
                if terminal['terminal'] == caller:
                    matches.append((space, tab, terminal))
    if len(matches) != 1:
        raise ValueError('Caller must have exactly one visible Herdr App pane.')
    space, tab, terminal = matches[0]
    if space.get('machine'):
        raise ValueError('A local worktree cannot target a remote app space.')
    if not terminal.get('pane'):
        raise ValueError('Caller pane metadata is unavailable; stopping.')
    info = command(CORE, 'get', caller)
    labels = info.get('labels') or {}
    if (info.get('address') != caller or info.get('state') != 'live'
            or labels.get('herdr.space') != space['id']
            or labels.get('herdr.tab') != tab['id']):
        raise ValueError('App/core caller identity mismatch; stopping.')
    return space, tab, terminal


def foreground_cwd(info):
    # info.cwd is the launch directory, NOT necessarily the current shell cwd.
    foreground = info.get('foreground') or {}
    cwd = foreground.get('cwd')
    if info.get('state') == 'live' and cwd:
        return os.path.realpath(cwd)
    return None


def record_companion(caller, terminal, worktree):
    command(CORE, 'label', terminal, 'erp.role=worktree-companion',
            'erp.owner=' + caller, 'erp.worktree=' + worktree)
    command(CORE, 'label', caller, 'erp.worktree=' + worktree,
            'erp.companion=' + terminal)


def open_companion(worktree):
    unused_space, tab, caller = caller_context()
    caller_id = caller['terminal']
    companions = []
    matching = []
    for terminal in tab['terminals']:
        terminal_id = terminal['terminal']
        if terminal_id == caller_id:
            continue
        info = command(CORE, 'get', terminal_id)
        labels = info.get('labels') or {}
        if labels.get('erp.role') == 'worktree-companion':
            companions.append(terminal_id)
        if foreground_cwd(info) == worktree:
            matching.append(terminal_id)

    if (len(companions) > 1 or len(matching) > 1
            or (companions and matching and companions != matching)):
        raise ValueError('Ambiguous same-tab worktree companions; stopping.')
    if matching:
        companion = matching[0]
        record_companion(caller_id, companion, worktree)
        print('Reusing worktree companion: {0}'.format(companion))
        return
    if companions:
        # hc exposes one foreground process, not the entire foreground group.
        # Unlike legacy process-info, that cannot prove a safe shell retarget.
        raise ValueError('Cannot safely retarget app companion {0}; '
                         'no command was sent and no pane was created.'
                         .format(companions[0]))

    status = command(APP, 'status')
    if status['tab'] != tab['id'] or not status.get('focused_pane'):
        raise ValueError('Show the caller tab before creating its companion.')
    focused_pane = status['focused_pane']
    # pane.split has no folder/no-focus options in Herdr App 0.1.12. Supply
    # the cwd as an argv element (never interpolated shell text), then restore
    # the original focus. All pane commands use explicit IDs.
    argv = ['/bin/sh', '-c', 'cd -- "$1" && exec "$2"',
            'erp-worktree', worktree, os.environ.get('SHELL') or '/bin/sh']
    try:
        created = app_do('pane.split', pane=caller['pane'],
                         direction='right', argv=argv)
        companion = created['terminal']
        # Register before restoring focus or checking startup: either can fail
        # while the new terminal is still missing its foreground cwd.
        record_companion(caller_id, companion, worktree)
    finally:
        app_do('pane.focus', pane=focused_pane)
    if foreground_cwd(command(CORE, 'get', companion)) != worktree:
        raise ValueError('Companion {0} created, but cwd is not confirmed; '
                         'inspect it before retrying.'.format(companion))
    print('Created worktree companion: {0} ({1})'.format(companion, worktree))


def main():
    if sys.argv[1:] == ['--check']:
        caller_context()
    elif len(sys.argv) == 2:
        open_companion(os.path.realpath(sys.argv[1]))
    else:
        raise ValueError('Usage: herdr-app-worktree-companion.py '
                         '<registered-worktree-path> | --check')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError) as error:
        print('Herdr App companion: {0}'.format(error), file=sys.stderr)
        sys.exit(1)
