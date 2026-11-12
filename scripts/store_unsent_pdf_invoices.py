import configdb
from erppeek import Client as Client


def main():
    c = Client(**configdb.erppeek)
    fact_obj = c.model("giscedata.facturacio.factura")

    total_successful, failed_ids = fact_obj.store_unsent_pdf_invoices()

    print("Successfuly stored {} invoices".format(total_successful))
    if failed_ids:
        print("Some errors ocurred:")
        print(failed_ids)
        exit(1)


if __name__ == "__main__":
    main()
