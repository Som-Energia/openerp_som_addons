from ftplib import FTP, FTP_TLS, FTP_PORT
import os


class SomFtp:
    def __init__(self, server_data):
        self.ftpcon = FTP()
        self.ftpcon.set_pasv(True)
        self.ftpcon.connect(server_data["url_portal"], int(server_data["port"]))
        self.ftpcon.login(server_data["usuari"], server_data["contrasenya"])

    def list_files(self, path="/", unique_folders=[]):
        """return list of files"""
        file_list = []
        dir_list = []

        for current_folder in unique_folders:
            remote_path = os.path.join(path, current_folder)
            file_list += self.ftpcon.nlst(remote_path)

        return file_list, dir_list

    def download_file(self, remote_path, destination_path):
        self.ftpcon.retrbinary(
            "RETR " + remote_path, open(destination_path, "wb").write
        )

    def close(self):
        return self.ftpcon.quit()
