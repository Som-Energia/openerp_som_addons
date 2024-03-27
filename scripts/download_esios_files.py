# Download files of esios webservice using Connection Kit
'''
Script use:
Download files of esios webservice using Connection Kit

Requirements:
- Java 11 or above installed
- eemws-kit-installer-2.0.0.jar (https://bitbucket.org/smree/eemws-core/downloads/)

# How to install eemws
- Download from bitbucket:
wget https://bitbucket.org/smree/eemws-core/downloads/eemws-kit-installer-2.0.0.jar
- Run the installer
java -jar eemws-kit-installer-2.0.0.jar
Friendly tip: During the installation, the install will ask you for the Target Path.
I suggest you to remove the space and put /home/erp/ConnectionKit
- Copy certificate .p12 file
- Modify file /home/erp/ConnectionKit/config/config.properties following values:
```
WEBSERVICES.URL=https://participa.esios.ree.es/ServicioLQ/ServiceEME
javax.net.ssl.keyStore=PATH_TO_CERTIFICATE
javax.net.ssl.keyStorePassword=PASSWORD_OF_CERTIFICATE
```
'''

import argparse
from datetime import datetime, timedelta
from consolemsg import step, error
from subprocess import Popen, PIPE, STDOUT, call
import re
import os
from time import sleep

FILE_TYPE = 'liquicomun'
FILE_PREFERENCE = ['A2_liquicomun', 'A1_liquicomun']
BIN_PATH = '/home/erp/ConnectionKit/bin'  # /bin folder of the ConnectionKit path
REGEX = r'\s+([0-9]+)\s+([^ ]*)\s+[0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{2}:[0-9]{2} - [0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{2}:[0-9]{2} [0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}\s+([^ ]*)\s+([^ ]*)'  # noqa: E501


def get_search_day():
    # Always looking for the next day to get most updated file unless is the last day of the month
    today = datetime.today()
    tomorrow = datetime.today() + timedelta(days=1)
    if today.month != tomorrow.month:
        return today.strftime('%d-%m-%Y')
    else:
        return tomorrow.strftime('%d-%m-%Y')


def download_files(file_type, server, server_port):
    day_of_search = get_search_day()
    step("Listing avaiable files {}...".format(FILE_TYPE))
    output = Popen(
        ['./list.sh', '-startTime', day_of_search, '-intervalType', 'Application'],
        cwd=BIN_PATH, stdout=PIPE, stderr=STDOUT)

    # Search for liquicomuns
    result = []
    errors = []
    for line in output.stdout:
        if file_type in line:
            result.append(line)
        else:
            errors.append(line)

    # Get preferred file
    file_list = []
    preferred_file = None
    for res in result:
        file_tuple = re.match(REGEX, res).groups()
        if (file_tuple[2] == FILE_PREFERENCE[0] or (file_tuple[2] == FILE_PREFERENCE[1]
                                                    and preferred_file is None)):
            preferred_file = (file_tuple[0], file_tuple[1])
            file_list.append(file_tuple[1])

    if len(result) == 0:
        error("No files avaiables")
        print errors
        return 0
    elif len(file_list) == 0 or preferred_file is None:
        error("No A2_liquicomun or A1_liquicomun files avaiables")
        print result
        return 0
    elif preferred_file:
        step("Found file...")
        code = preferred_file[0]
        filename = preferred_file[1]

    step("Downloading {}...".format(filename))
    output = Popen(
        ['./get.sh', '-code', code], cwd=BIN_PATH, stdout=PIPE, stderr=STDOUT)

    file_path = '{}/{}'.format(BIN_PATH, filename)
    timeout = 10
    while not os.path.isfile('{}/{}'.format(BIN_PATH, filename)):
        if not timeout:
            error("Timeout downloading file {}".format(filename))
            return 0
        sleep(15)
        timeout -= 1

    step("Coping file to the server {}...".format(server))
    call(["scp", "-P", server_port, file_path, server])
    os.remove('{}/{}'.format(BIN_PATH, filename))
    step("File {} copied to {} successfully".format(filename, server))

    step("Unzipping file on remote server {}...".format(server))
    ssh = Popen(
        ["ssh", "-p", server_port, "{}".format(server.split(':')[0]), 'unzip -o',
         "/tmp/{}".format(filename), "-d", "/tmp/"], shell=False, stdout=PIPE, stderr=PIPE)
    step("List of unzipped files {}".format(ssh.stdout.readlines()))
    print ssh.stderr.readlines()
    step("File {} unzip successfully".format(filename))


if __name__ == "__main__":
    step("Start run: {}".format(datetime.today().strftime('%d-%m-%Y %H:%M:%S')))
    parser = argparse.ArgumentParser(description="Download ESIOS files")
    parser.add_argument(
        "--file_type",
        dest="file_type",
        default=FILE_TYPE,
        type=str,
        help="File type (default 'liquicomun')",
    )
    parser.add_argument(
        "--destination_server",
        dest="server",
        type=str,
        help="user@server:path destionation",
    )
    parser.add_argument(
        "--server_port",
        dest="server_port",
        type=str,
        help="SSH server port",
    )
    args = parser.parse_args()

    download_files(args.file_type, args.server, args.server_port)
    step("Finsish run: {}".format(datetime.today().strftime('%d-%m-%Y %H:%M:%S')))
    step("=============================================\n")
