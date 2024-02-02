# Download files of esios webservice using Connection Kit
'''
Script use:
Download files of esios webservice using Connection Kit

Requirements:
- Java 11 or above installed
- eemws-kit-installer-2.0.0.jar (https://bitbucket.org/smree/eemws-core/downloads/)

Friendly tip: Installer create a 'Connection Kit' folder into users home. That space makes me fail
all the scripts. I suggest you to remove the space 'ConnectionKit' and change all the apparences of
the path in bin/XXX.sh scripts.

`cd ConnectionKit/bin/
sed -i 's/Connection Kit/ConnectionKit/g' *`

'''
import argparse
from datetime import datetime, timedelta
from consolemsg import step, error
from subprocess import Popen, PIPE, STDOUT
import re
import shutil
import os
import time

FILE_TYPE = 'liquicomun'
BIN_PATH = '/home/erp/ConnectionKit/bin'  # /bin folder of the ConnectionKit path
DESTINATION_PATH = '/tmp'  # Place where to save downloade file


def get_search_day():
    # Always looking for the next day to get most updated file unless is the last day of the month
    today = datetime.today()
    tomorrow = datetime.today() + timedelta(days=1)
    if today.month != tomorrow.month:
        return today.strftime('%d-%m-%Y')
    else:
        return tomorrow.strftime('%d-%m-%Y')


def download_files(file_type):
    day_of_search = get_search_day()
    step("Listing avaiable files {}...".format(FILE_TYPE))
    output = Popen(
        ['./list.sh', '-startTime', day_of_search, '-intervalType', 'Application'],
        cwd=BIN_PATH, stdout=PIPE, stderr=STDOUT)
    result = []
    for line in output.stdout:
        if FILE_TYPE in line:
            result.append(line)
    if len(result) == 1:
        code, filename = re.match(r'\s+([0-9]+)\s+([^ ]*)', result[0]).groups()
    elif len(result) == 0:
        error("No files avaiables")
    elif len(result) == 0:
        error("To many files to download")

    step("Downloading {}...".format(filename))
    output = Popen(
        ['./get.sh', '-code', code], cwd=BIN_PATH, stdout=PIPE, stderr=STDOUT)
    time.sleep(3)
    shutil.copy('{}/{}'.format(BIN_PATH, filename), '{}/{}'.format(DESTINATION_PATH, filename))
    if os.path.isfile('{}/{}'.format(BIN_PATH, filename)):
        os.remove('{}/{}'.format(BIN_PATH, filename))
    step("File {} copied to {} successfully".format(filename, DESTINATION_PATH))


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
