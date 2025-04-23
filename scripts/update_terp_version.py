#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Script to update __terp__.py versions of the module

This is a script copied from GISCE due execution path limitatons
Original path script: erp/scripts/update_terp_version.py

Som Energia example execution:
    python scripts/update_terp_version.py . 24.5.0

"""

EXTRA_DIRECTORIES = [
    'server/bin/addons/base',
    'addons/gisce/',
    'addons/extra/account_invoice_pending',
    'addons/spain/l10n_es_extras/l10n_ES_aeat_sii',
    'addons/spain/l10n_es_extras/l10n_ES_face',
    'addons/official/account',
    'addons/official/crm',
    'addons/spain/l10n_es/l10n_chart_ES',
]


def confirm(ask_query="OK to push to continue [Y/N]?"):
    """
    Ask user to enter Y or N (case-insensitive).
    :return: True if the answer is Y.
    :rtype: bool
    """
    answer = ""
    while answer not in ["y", "n"]:
        answer = raw_input(ask_query + ' ').lower()
    return answer == "y"


if __name__ == "__main__":
    import os
    import sys
    import re

    directory = sys.argv[1]
    version = sys.argv[2]

    pattern = "2\.[0-9]+\.[0-9]+"  # noqa: W605
    # Versions should be a 2, followed by a . and a number and another . and
    # another number. A possible example is: "2.79.2"
    if not re.match(pattern, version):
        confirm_message = "Provided version does not match usual pattern, " \
                          "do you wish to continue?"
        if not confirm(confirm_message):
            sys.exit(0)

    print ("Updating to version {version}".format(**locals()))
    version_regex = r'["\']version*["\'](.*)["\'],'
    replace_str = r'"version": "{}",'.format(version)

    modules = 0
    updated = 0

    directories_to_update = []
    if directory != 'all':
        directories_to_update.append(directory)
    else:
        directories_to_update.extend(EXTRA_DIRECTORIES)

    for directory in directories_to_update:
        for root, dirs, files in os.walk(directory):
            if '.svn' in dirs:
                dirs.remove('.svn')
            if '.git' in dirs:
                dirs.remove('.git')
            if '__terp__.py' in files:
                modules += 1
                module = root.split(os.path.sep)[-1]
                terp_file_path = os.path.join(root, '__terp__.py')
                with open(terp_file_path, 'r') as f:
                    terp = f.read()
                    parsed_version_terp = re.sub(version_regex, replace_str,
                                                 terp)
                with open(terp_file_path, 'w') as f:
                    f.write(parsed_version_terp)
                if parsed_version_terp != terp:
                    updated += 1
                    print (
                        "** MODULE: {module} **  => Upgraded to {version}".format(
                            **locals()
                        ))

    print("Updated {updated}/{modules}".format(**locals()))
