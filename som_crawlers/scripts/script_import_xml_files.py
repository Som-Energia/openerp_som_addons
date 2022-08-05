from massive_importer.lib.erp_utils import ErpManager
from massive_importer.lib.exceptions import InvalidEncodingException

import io
import sys
import click
import os
import base64

@click.command()
@click.option('-o', '--outputfile', help = 'Output file result', required=True)
@click.option('-p', '--pathzip', help = 'Zip path', required=True)


def import_xml(outputfile, pathzip):
    path = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(path,"../outputFiles",outputfile),'w')
    try:
        for fileName in os.listdir(pathzip):
            with open(os.path.join(pathzip,fileName), 'r', encoding="utf8", errors='ignore') as file:
                content  = base64.b64encode(bytes(file.read(), "utf-8"))
        erp =  ErpManager('http://localhost:18069', 'destral_db', 'admin', 'admin')

        erp.import_wizard(fileName, content)
        f.write('Import xml files done')
    except Exception as e:
        f.write(str(e))

if __name__ == '__main__':
    import_xml()
