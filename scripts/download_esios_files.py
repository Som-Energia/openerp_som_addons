# Download files of esios webservice using Connection Kit
'''
Script use:
Download files of esios webservice using Connection Kit

Requirements:
- Java 11 or above installed
- eemws-kit-installer-2.0.0.jar (https://bitbucket.org/smree/eemws-core/downloads/)

Friendly tip: Installer create a 'Connection Kit' folder into users home. That space makes me fail all the scripts. I suggest you to remove the space 'ConnectionKit' and change all the apparences of the path in bin/XXX.sh scripts.
`cd ConnectionKit/bin/
sed -i 's/Connection Kit/ConnectionKit/g' *`

'''
import argparse
from datetime import datetime, timedelta
import calendar
import dbconfig
from consolemsg import step
import base64
from erppeek import Client
import subprocess


FILE_TYPE = 'liquicomun'
BIN_PATH = '/home/erp/ConnectionKit/bin'
BIN_PATH = '/home/oriol/ConnectionKit/bin'


def get_search_day():
    # Always looking for the next day to get most updated file unless is the last day of the month
    today = datetime.today()
    tomorrow = datetime.today() + timedelta(days=1)
    if today.month != tomorrow.month:
        return today.strftime('%d-%m-%Y')
    else:
        return tomorrow.strftime('%d-%m-%Y')


def download_files(file_type):
    import pudb
    pu.db
    day_of_search = get_search_day()
    step("Listing avaiable files {}...".format(FILE_TYPE))
    subprocess.call(['ls'], cwd=BIN_PATH)
    result = subprocess.check_call(
        ['./list.sh', '-startTime', day_of_search, '-intervalType', 'Application'], cwd=BIN_PATH)
    step(str(result))

    # step("Writing {}...".format(report_name_csv))
    # with open("/tmp/" + report_name_csv, "w") as f:
    #    f.write(base64.b64decode(wiz.file_csv))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download ESIOS files")
    parser.add_argument(
        "--file_type",
        dest="file_type",
        default=FILE_TYPE,
        type=str,
        help="File type (default 'liquicomun')",
    )
    args = parser.parse_args()

    download_files(args.file_type)
