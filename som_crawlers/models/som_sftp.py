import os
from pysftp import Connection, CnOpts
from paramiko import transport

transport.Transport._preferred_kex = (
    "ecdh-sha2-nistp256",
    "ecdh-sha2-nistp384",
    "ecdh-sha2-nistp521",
    # 'diffie-hellman-group16-sha512',  # Needed for Pitarch
    "diffie-hellman-group-exchange-sha256",
    "diffie-hellman-group14-sha256",
    "diffie-hellman-group-exchange-sha1",
    "diffie-hellman-group14-sha1",
    "diffie-hellman-group1-sha1",
)


class SomSftp:
    def __init__(self, server_data):
        cnopts = CnOpts()
        cnopts.hostkeys = None  # disable host key checking.
        params = {
            "host": server_data["url_portal"],
            "port": int(server_data["port"]),
            "username": server_data["usuari"],
            "password": server_data["contrasenya"],
            "cnopts": cnopts,
        }

        self.connection = Connection(**params)

    def list_files(self, path="/", unique_folders=[], recursive=False):
        """return list of files"""
        file_list = []
        dir_list = []

        for current_folder in unique_folders:
            remote_path = os.path.join(path, current_folder)

            def _valid_file(filename):
                file_list.append(filename)

            def _valid_dir(path):
                print("- Found subdir: {}".format(path))
                dir_list.append(path)

            def _valid_unknown(path):
                print("- Found unknown: {}".format(path))

            self.connection.walktree(
                remote_path, _valid_file, _valid_dir, _valid_unknown, recurse=recursive
            )

        return file_list, dir_list

    def download_file(self, remote_path, destination_path):
        return self.connection.get(remote_path, destination_path)

    def close(self):
        self.connection.close()
