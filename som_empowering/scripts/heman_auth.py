import sys

from amoniak.utils import setup_peek, setup_mongodb


def sync_perms():
    c = setup_peek()
    m = setup_mongodb()
    partners = c.ResPartner.search([
        ('empowering_token', '!=', False)
    ])
    print "{} partners found".format(len(partners))
    for idx, partner in enumerate(c.ResPartner.read(partners,
                                                    ['empowering_token'])):
        idx += 1
        allowed = c.GiscedataPolissa.search_reader([
            '|',
            ('titular.id', '=', partner['id']),
            ('pagador.id', '=', partner['id'])
        ], ['name'])
        if allowed:
            allowed = [x['name'] for x in allowed]
            m.tokens.insert({
                'token': partner['empowering_token'],
                'allowed_contracts': allowed
            })
        sys.stderr.write('{}/{}\r'.format(idx, len(partners)))
        sys.stderr.flush()


if __name__ == '__main__':
    sync_perms()
