#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import subprocess
import sys
import pkg_resources


def is_installed_from_repo():
    try:
        output = subprocess.check_output([sys.executable, '-m', 'pip', 'show', 'cchloader'])
        for line in output.split('\n'):
            if line.startswith('Location:') and 'gisce' in line:
                return True
        return False
    except subprocess.CalledProcessError:
        return False


def is_version_invalid():
    try:
        version = pkg_resources.get_distribution('cchloader').version
        return pkg_resources.parse_version(version) < pkg_resources.parse_version('4.0')
    except pkg_resources.DistributionNotFound:
        return False


def install_via_pip():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                              '--force-reinstall', 'cchloader'])
        print("Paquet 'cchloader' reinstal·lat des de PyPI correctament.")
    except subprocess.CalledProcessError:
        print("Error: No s'ha pogut instal·lar 'cchloader' des de PyPI.")
        sys.exit(1)


def main():
    if is_installed_from_repo():
        print("El paquet 'cchloader' està instal·lat des de repositori. Reinstal·lant des de PyPI...")  # noqa: E501
        install_via_pip()
        sys.exit(1)
    elif is_version_invalid():
        print("La versió de 'cchloader' és superior a 1.0. Reinstal·lant des de PyPI...")
        install_via_pip()
        sys.exit(1)
    else:
        print("El paquet 'cchloader' està correctament instal·lat. No cal fer res.")
        sys.exit(0)


if __name__ == '__main__':
    main()
