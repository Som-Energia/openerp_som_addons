import csv
import sys
from erppeek import Client
import dbconfig

erp = Client(**dbconfig.erppeek_terp)

# CSV columns
# ajuntament,iban,remesa,saras,pagament,idioma


def netejar_nom_ajuntament(nom):
    versions = ['ajuntament', 'Ajuntament', 'AJUNTAMENT', 'Ayuntamiento', 'AYUNTAMIENTO']
    articles = ["DE L'", "ELS", "els", "LES", "les", "D'", "d'", "EL", "el", "DE", "de", "L'", "l'"]
    for versio in versions:
        result = nom.split(versio)
        if len(result) > 1:
            for article in articles:
                result2 = result[1].split(article)
                if(len(result2)) > 1:
                    return result2[1].strip()
            return result[1].strip()


def crear_partner(fila):
    ajuntament_category = erp.IrModelData.get_object_reference(
        'som_municipal_taxes', 'res_partner_category_ajuntament',
    )[1]
    vals_partner = {
        'name': fila['ajuntament'],
        'category_id': [(4, ajuntament_category)],
        'customer': False,
        'include_in_mod347': False,
    }
    partner_id = erp.ResPartner.create(vals_partner)

    vals_bank = {
        'iban': fila['iban'],
        'partner_id': partner_id.id,
        'state': 'iban',
        'default_bank': True,
    }

    erp.ResPartnerBank.create(vals_bank)

    return partner_id


def crear_ajuntament_config(fila):
    nom = netejar_nom_ajuntament(fila['ajuntament'])

    municipi_id = erp.ResMunicipi.search([('name', 'ilike', nom)])
    if not municipi_id:
        print "No s'ha pogut crear: {}".format(fila['ajuntament'])
        return False

    vals = {
        'name': fila['ajuntament'],
        'municipi_id': municipi_id[0],
        'active': True,
        'payment_order': True if fila['remesa'] else False,
        'red_sara': True if fila['saras'] else False,
    }
    if fila['remesa']:
        vals['partner_id'] = crear_partner(fila)

    if fila['idioma']:
        vals['lang'] = "ca_ES"
    else:
        vals['lang'] = "es_ES"

    if fila['pagament'] == 'trimestral':
        vals['payment'] = 'quarter'
    elif fila['pagament'] == 'anual':
        vals['payment'] = 'year'
    else:
        raise Exception("Camp pagament no ben informat")

    erp.SomMunicipalTaxesConfig.create(vals)

    return True


def carrega_ajuntaments(filename):
    creats = []
    no_creats = []
    with open(filename, 'rb') as fitxer:
        lector = csv.DictReader(fitxer)

        # Iterem per les files del fitxer
        for fila in lector:
            try:
                result = crear_ajuntament_config(fila)
            except Exception as e:
                result = False
                print "No s'ha pogut crear: {}. Error: {}".format(fila['ajuntament'], str(e))

            if result:
                creats.append(fila['ajuntament'])
            else:
                no_creats.append(fila['ajuntament'])

    print "Creats {}".format(len(creats))
    print "No Creats {}".format(len(no_creats))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print u"Usage: {} <fitxer.csv>".format(sys.argv[0])
        sys.exit()
    carrega_ajuntaments(sys.argv[1])
