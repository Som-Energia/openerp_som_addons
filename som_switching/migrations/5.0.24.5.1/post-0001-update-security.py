from oopgrade import oopgrade


def up(cursor, installed_version):
    if not installed_version:
        return

    module = 'som_switching'

    oopgrade.load_data(
        cursor, module, 'security/ir.model.access.csv', idref=None, mode='update'
    )


migrate = up
