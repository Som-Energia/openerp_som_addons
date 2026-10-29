#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import argparse
import importlib
import os
import subprocess
import sys


TOOL_MODULES = ('pre_commit.main', 'flake8.main.cli')
RUNTIME_MODULES = ('destral.cli', 'generationkwh.investmentmodel')


def check_modules(module_names, importer=importlib.import_module):
    errors = []
    for name in module_names:
        try:
            module = importer(name)
            print('OK: {} ({})'.format(name, getattr(module, '__file__', 'built-in')))
        except Exception as error:
            errors.append('{}: {}'.format(name, error))
    return errors


def check_requirements(requirements, require=None):
    if require is None:
        from pkg_resources import require
    errors = []
    for line in requirements:
        requirement = line.strip()
        if not requirement or requirement.startswith('#'):
            continue
        try:
            require(requirement)
        except Exception as error:
            errors.append('{}: {}'.format(requirement, error))
    return errors


def detect_workspace(script_dir):
    if os.environ.get('WORKSPACE'):
        return os.path.abspath(os.environ['WORKSPACE'])
    common_dir = subprocess.check_output([
        'git', '-C', script_dir, 'rev-parse', '--path-format=absolute', '--git-common-dir',
    ]).decode('utf-8').strip()
    return os.path.dirname(os.path.dirname(common_dir))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Check local tools and ERP imports before Destral.')
    parser.add_argument('--tools-only', action='store_true', help='Do not import ERP dependencies')
    parser.add_argument('--workspace', help='Directory containing erp, destral and generationkwh')
    args = parser.parse_args(argv)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print('Python: {} ({})'.format(sys.executable, sys.version.split()[0]))
    errors = check_modules(TOOL_MODULES)
    # The pinned setup targets the legacy Python 2 toolchain. Python 3 users
    # can provide their own compatible tools without being forced to downgrade.
    if sys.version_info[:2] == (2, 7):
        with open(os.path.join(script_dir, '..', 'requirements-local-validation.txt')) as source:
            errors.extend(check_requirements(source))
    if not args.tools_only:
        workspace = args.workspace or detect_workspace(script_dir)
        paths = [os.path.join(workspace, path) for path in (
            'destral', 'erp/server/bin', 'erp/server/bin/addons', 'erp/server/sitecustomize',
        )]
        sys.path[0:0] = paths
        errors.extend(check_modules(RUNTIME_MODULES))
    if errors:
        for error in errors:
            print('ERROR: {}'.format(error), file=sys.stderr)
        print('Run PYENV_VERSION=erp scripts/setup-local-validation.sh; '
              'see docs/guides/local-validation.md.', file=sys.stderr)
        return 1
    print('Local validation environment is ready.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
