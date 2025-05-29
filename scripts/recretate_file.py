#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# python recreate_file.py /path/to/file
#

import os
import sys
import time


def recreate_file(filepath):
    if not os.path.isfile(filepath):
        print("El fitxer '%s' no existeix." % filepath)
        return

    # Llegim el contingut
    with open(filepath, 'rb') as f:
        content = f.read()

    # Esborrem el fitxer original
    os.remove(filepath)

    # Esperem un moment perquè canviïn els timestamps
    time.sleep(1)

    # Tornem a crear el fitxer amb el mateix contingut
    with open(filepath, 'wb') as f:
        f.write(content)

    print("Fitxer '%s' recreat amb èxit." % filepath)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Ús: %s /ruta/al/fitxer" % sys.argv[0])
        sys.exit(1)

    filepath = sys.argv[1]
    recreate_file(filepath)
