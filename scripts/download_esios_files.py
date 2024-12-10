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
from datetime import datetime
from consolemsg import step, error
from subprocess import Popen, PIPE, STDOUT, call
import re
import os
from time import sleep
import paramiko

FTP_FOLDER = 'liquicomun'
REGEX = r'\s+([0-9]+)\s+([^ ]*)\s+[0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{2}:[0-9]{2} - [0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{2}:[0-9]{2} [0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}\s+([^ ]*)\s+([^ ]*)'  # noqa: E501


def get_search_day():
    # Always looking for today because we want all posible files
    today = datetime.today()
    return today.strftime('%d-%m-%Y')


def send_to_server(server, server_port, ftp_server, ftp_username,
                   ftp_password, filename=None, file_path=None, absolute_path=None):
    if absolute_path is not None:
        file_path = absolute_path
        filename = absolute_path.split('/')[-1]
    step("Coping file to the server {}...".format(server))
    call(["scp", "-P", server_port, file_path, server])
    step("File {} copied to {} successfully".format(filename, server))

    step("Unzipping file on remote server {}...".format(server))
    ssh = Popen(
        ["ssh", "-p", server_port, "{}".format(server.split(':')[0]), 'unzip -o',
         "/tmp/{}".format(filename), "-d", "/tmp/"], shell=False, stdout=PIPE, stderr=PIPE)
    step("List of unzipped files {}".format(ssh.stdout.readlines()))
    print ssh.stderr.readlines()
    step("File {} unzip successfully".format(filename))

    step("Coping file to SFTP server {}".format(ftp_server))

    try:
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.load_system_host_keys()
            ssh.connect(hostname=ftp_server, port=server_port,
                        username=ftp_username, password=ftp_password)
            sftp = ssh.open_sftp()
            sftp.chdir('/{}'.format(FTP_FOLDER))
            sftp.put(file_path, filename)
    except Exception:
        error("Error copy SFTP server file {}".format(filename))
        return True

    step("All done")
    step("Removing file from localhost")
    os.remove('{}'.format(file_path))


def download_all_files(server, server_port, ftp_server, ftp_username, ftp_password, kit_path):
    day_of_search = get_search_day()
    step("Listing avaiable files...")
    output = Popen(
        ['./list.sh', '-startTime', day_of_search, '-intervalType', 'Application'],
        cwd=kit_path, stdout=PIPE, stderr=STDOUT)

    # Search for all files
    result = []
    for line in output.stdout:
        result.append(line)

    # Get preferred file
    file_list = []
    preferred_file = None
    for res in result:
        try:
            file_tuple = re.match(REGEX, res).groups()
        except Exception:
            continue
        preferred_file = (file_tuple[0], file_tuple[1])
        file_list.append(file_tuple[1])

        code = preferred_file[0]
        filename = preferred_file[1]

        step("Downloading {}...".format(filename))
        output = Popen(
            ['./get.sh', '-code', code], cwd=kit_path, stdout=PIPE, stderr=STDOUT)

        file_path = '{}/{}'.format(kit_path, filename)
        timeout = 10
        while not os.path.isfile('{}/{}'.format(kit_path, filename)):
            if timeout == 0:
                error("Timeout downloading file {}".format(filename))
                break
            sleep(15)
            timeout -= 1

        if timeout != 0:
            send_to_server(server, server_port, ftp_server, ftp_username,
                           ftp_password, filename, file_path, absolute_path=None)


if __name__ == "__main__":
    file_path = False
    filename = False
    step("Start run: {}".format(datetime.today().strftime('%d-%m-%Y %H:%M:%S')))
    parser = argparse.ArgumentParser(description="Download ESIOS files")
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
    parser.add_argument(
        "--ftp_server",
        dest="ftp_server",
        type=str,
        help="FTP server address",
    )
    parser.add_argument(
        "--ftp_username",
        dest="ftp_username",
        type=str,
        help="FTP user name",
    )
    parser.add_argument(
        "--ftp_password",
        dest="ftp_password",
        type=str,
        help="FTP user password",
    )
    parser.add_argument(
        "--absolute_path",
        dest="absolute_path",
        type=str,
        default='None',
        help="Absolute path of magic folder file downloaded",
    )
    parser.add_argument(
        "--kit_path",
        dest="kit_path",
        type=str,
        default='/home/erp/ConnectionKit/bin',
        help="Absolute path of ConnectionKit bin folder",
    )
    args = parser.parse_args()

    download_all_files(args.server, args.server_port, args.ftp_server,
                       args.ftp_username, args.ftp_password, args.kit_path)

    step("Finsish run: {}".format(datetime.today().strftime('%d-%m-%Y %H:%M:%S')))
    step("=============================================\n")
