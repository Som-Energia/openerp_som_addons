import sys
from erppeek import Client

dbname, port, user, pwd = sys.argv[1:]

conn = Client("http://localhost:{0}".format(port), dbname, user, pwd)

soci_category = conn.ResPartnerCategory.search([("name", "=", "Soci")])

if not soci_category or len(soci_category) > 1:
    sys.stdout.write("Soci category not found: {0}\n".format(soci_category))
    exit(1)

soci_category = soci_category[0]

socis = [s["partner_id"] and s["partner_id"][0] for s in conn.SomenergiaSoci.read([], ["partner_id"])]  # noqa: E501

search_params = [("category_id", "=", soci_category)]
if socis:
    search_params += [("id", "not in", socis)]

partner2soci_ids = conn.ResPartner.search(search_params, 0, 0, "id", {"active_test": False})

soci_ids = conn.SomenergiaSoci.create_socis(partner2soci_ids)

sys.stdout.write("{0} Socis creats\n".format(len(soci_ids)))
