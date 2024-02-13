# -*- coding: utf-8 -*-
from osv import osv
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/drive"]
APPLICATION_NAME = "Drive API Python Quickstart"


class GoogleDriveManager(osv.osv_memory):
    _name = "google.drive.manager"

    def getCredentials(self, cursor, uid, context={}):
        config = self.pool.get("res.config")
        token_file = config.get(cursor, uid, "google_drive_token_file", "token.pickle")
        client_secret_file = config.get(
            cursor, uid, "google_drive_client_secret_file", "client_secrets.json"
        )
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(token_file):
            with open(token_file, "rb") as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)
        return creds

    def uploadMediaToDrive(
        self, cursor, uid, document_name, document_path, folder_hash=None, context=None
    ):
        cred = self.getCredentials(cursor, uid)
        file_metadata = {
            "name": document_name,
            "mimeType": "application/vnd.google-apps.document",
            "parents": [folder_hash],
        }

        service = build("drive", "v3", credentials=cred)
        media = MediaFileUpload(document_path, mimetype="text/html", resumable=True)
        return service.files().create(body=file_metadata, media_body=media).execute()


GoogleDriveManager()
