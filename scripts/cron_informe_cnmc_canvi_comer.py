# Generate Report CNMC Canvi comercalitzadora
import argparse
from datetime import datetime
import calendar
import dbconfig
from consolemsg import step
import base64
from erppeek import Client


def generate_report(year, month, agent, sequence):
    report_name = "SI_{}_{}_{}{}_{}.xml".format(
        agent,
        "E",
        year,
        month,
        sequence,
    )
    report_name_csv = "SI_{}_{}_{}{}_{}.csv".format(
        agent,
        "E",
        year,
        month,
        sequence,
    )

    date_time_start = datetime.strptime(str(year) + "-" + str(month) + "-01", "%Y-%m-%d")
    last_day_month = str(calendar.monthrange(int(year), int(month))[1])
    date_time_end = datetime.strptime(
        str(year) + "-" + str(month) + "-" + last_day_month, "%Y-%m-%d"
    )
    print {  # noqa: E999
        "file_type": "SI",
        "start_date": date_time_start.strftime("%Y-%m-%d"),
        "end_date": date_time_end.strftime("%Y-%m-%d"),
    }

    c = Client(**dbconfig.erppeek)
    step("Collecting data...")
    wiz = c.WizardCnmcXmlReport.create(
        {
            "file_type": "SI",
            "start_date": date_time_start.strftime("%Y-%m-%d"),
            "end_date": date_time_end.strftime("%Y-%m-%d"),
        }
    )
    wiz.action_generate_file()

    step("Writing {}...".format(report_name))
    with open("/tmp/" + report_name, "w") as f:
        f.write(base64.b64decode(wiz.file))

    step("Writing {}...".format(report_name_csv))
    with open("/tmp/" + report_name_csv, "w") as f:
        f.write(base64.b64decode(wiz.file_csv))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generates switching monthly report")
    parser.add_argument("year", metavar="YEAR")
    parser.add_argument("month", metavar="MONTH")
    parser.add_argument("sequence", metavar="SEQUENCE", nargs="?")
    parser.add_argument("--agent", metavar="AGENT", nargs="?", default="R2-415", help="Agent code ")
    args = parser.parse_args()

    generate_report(args.year, args.month, args.agent, args.sequence)
