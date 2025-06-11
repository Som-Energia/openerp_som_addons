# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
import subprocess
import ast

"""
Aquest script crea scripts de migració per a mòduls d'OpenERP 5.0.
Per a cada mòdul, comprova els fitxers modificats i crea un script de migració
per actualitzar els camps i vistes dels models afectats.

Execució des de l'arrel del repositori:
    python scripts/create_migration_script.py
"""


def get_modified_files():
    """Retorna un diccionari amb els mòduls i els seus fitxers modificats (XML, CSV i Python)."""
    cmd = "git diff --name-only main"
    result = subprocess.check_output(cmd.split()).decode('utf-8')

    modified_files = {}
    for file_path in result.splitlines():
        if 'demo' not in file_path:
            # Processar només XML, CSV de security i Python que no siguin wizards
            is_security_csv = file_path.endswith('.csv') and '/security/' in file_path
            is_xml = file_path.endswith('.xml')
            is_py = (file_path.endswith('.py')
                     and 'wizard' not in file_path.lower()
                     and '/wizard/' not in file_path
                     and 'scripts/' not in file_path)

            if is_security_csv or is_xml or is_py:
                parts = file_path.split('/', 1)
                if len(parts) == 2:
                    module_name, relative_path = parts
                    if module_name not in modified_files:
                        modified_files[module_name] = {'data': [], 'py': [], 'security': []}
                    if is_security_csv:
                        modified_files[module_name]['security'].append(relative_path)
                    elif is_xml:
                        modified_files[module_name]['data'].append(relative_path)
                    elif is_py:
                        modified_files[module_name]['py'].append(relative_path)

    return modified_files


def find_new_fields(file_path):
    """Analitza un fitxer Python per trobar nous camps en _columns."""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())

        models = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                model_name = None
                has_columns = False

                # Buscar _name i _columns
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                if target.id == '_name' and isinstance(item.value, ast.Str):
                                    model_name = item.value.s
                                elif target.id == '_columns':
                                    has_columns = True

                if model_name and has_columns:
                    models.append(model_name)

        return models
    except Exception as e:
        print("Error analitzant {0}: {1}".format(file_path, str(e)))
        return []


def is_manually_modified(file_path):
    """Comprova si un fitxer ha estat modificat manualment."""
    if not os.path.exists(file_path):
        return False

    cmd = "git diff --name-only {0}".format(file_path)
    result = subprocess.check_output(cmd.split()).decode('utf-8')
    return bool(result.strip())


def get_current_branch():
    """Obté el nom de la branca actual de git."""
    cmd = "git rev-parse --abbrev-ref HEAD"
    return subprocess.check_output(cmd.split()).decode('utf-8').strip()


def get_next_script_number(migration_dir):
    """Obté el següent número de seqüència per l'script de migració."""
    if not os.path.exists(migration_dir):
        return '0001'

    # Buscar tots els scripts de migració existents
    existing_scripts = [f for f in os.listdir(migration_dir)
                        if f.startswith('post-') and f.endswith('.py')]

    if not existing_scripts:
        return '0001'

    # Extreure els números de seqüència
    numbers = []
    for script in existing_scripts:
        try:
            num = int(script.split('-')[1].split('_')[0])
            numbers.append(num)
        except (IndexError, ValueError):
            continue

    next_num = max(numbers + [0]) + 1
    return str(next_num).zfill(4)


def create_migration_script(module_name, files):
    """Crea un script de migració pel mòdul especificat."""
    # Primer comprovem si hi ha canvis a fer
    models_to_init = []
    for py_file in files['py']:
        full_path = os.path.join(module_name, py_file)
        models = find_new_fields(full_path)
        models_to_init.extend(models)

    # Si no hi ha ni models per inicialitzar ni fitxers data per actualitzar, sortim
    if not models_to_init and not files['data']:
        return

    manifest_path = os.path.join(module_name, '__terp__.py')
    with open(manifest_path, 'r') as f:
        manifest = eval(f.read())
    version = manifest.get('version', '0.0.0')
    version = "5.0.{0}".format(version)
    migration_dir = os.path.join(module_name, 'migrations', version)

    # Crear directori si no existeix (compatible amb Python 2)
    try:
        os.makedirs(migration_dir)
    except OSError as e:
        if e.errno != os.errno.EEXIST:
            raise

    # Obtenir el següent número de seqüència i el nom de la branca
    next_num = get_next_script_number(migration_dir)
    branch_name = get_current_branch().replace('/', '_')

    # Crear el nom de l'script
    script_name = 'post-{0}_{1}_update_views_and_fields.py'.format(next_num, branch_name)
    script_path = os.path.join(migration_dir, script_name)

    # Comprovar si ja existeix un script per aquesta branca
    existing_branch_script = None
    for f in os.listdir(migration_dir):
        if f.endswith('.py') and branch_name in f:
            existing_branch_script = os.path.join(migration_dir, f)
            break

    if existing_branch_script:
        if is_manually_modified(existing_branch_script):
            print("L'script {0} ha estat modificat manualment. No es sobreescriurà.".format(
                existing_branch_script))
            return
        # Si existeix un script per aquesta branca però no ha estat modificat, l'eliminem
        script_name = existing_branch_script.split('/')[-1]
        script_path = existing_branch_script
        os.remove(existing_branch_script)

    with open(script_path, 'w') as f:
        f.write('''# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
''')
        if models_to_init:
            f.write('''import pooler''')
        f.write('''

def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
''')
        # Afegir _auto_init per models amb nous camps
        if models_to_init:
            f.write('\n    logger.info("Initializing new fields")\n')
            f.write('\n    pool = pooler.get_pool(cursor.dbname)\n')
            for model in models_to_init:
                f.write('''    pool.get("{0}")._auto_init(
        cursor, context={{'module': '{1}'}}
    )\n\n'''.format(model, module_name))

        # Afegir load_data per XMLs modificats
        if files['data']:
            f.write('\n    logger.info("Updating XML files")\n')
            f.write('    data_files = [\n')
            for data_file in files['data']:
                f.write("        '{0}',\n".format(data_file))
            f.write('    ]\n')
            f.write('''    for data_file in data_files:
        load_data(
            cursor, '{0}', data_file,
            idref=None, mode='update'
        )\n\n'''.format(module_name))

        # Afegir load_data per CSVs security modificats
        if files['security']:
            f.write('\n    logger.info("Updating CSV security files")\n')
            f.write('    security_files = [\n')
            for data_file in files['security']:
                f.write("        '{0}',\n".format(data_file))
            f.write('    ]\n')
            f.write('''    for security_file in security_files:
        load_data(
            cursor, '{0}', security_file,
            idref=None, mode='update'
        )\n\n'''.format(module_name))

        f.write('''    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
''')

    print("Creat script de migració: {0}".format(script_path))


def main():
    modified_files = get_modified_files()
    for module_name, files in modified_files.items():
        if files['data'] or files['py']:  # Crear script si hi ha canvis
            create_migration_script(module_name, files)


if __name__ == '__main__':
    main()
    exit(0)
