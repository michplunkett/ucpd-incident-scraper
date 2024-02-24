import json
import logging

from oauth2client.service_account import ServiceAccountCredentials
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from incident_scraper.utils.constants import (
    ENV_GCP_CREDENTIALS,
    ENV_GOOGLE_DRIVE_MAROON_FOLDER_ID,
    FILE_TYPE_JSON,
)


class MaroonGoogleDrive:
    """
    Class that manages interactions with Google Drive.
    """

    SCOPES = ["https://www.googleapis.com/auth/drive"]

    def __init__(self):
        auth_client = GoogleAuth()
        auth_client.auth_method = "service"
        if ENV_GCP_CREDENTIALS.endswith(FILE_TYPE_JSON):
            auth_client.credentials = (
                ServiceAccountCredentials.from_json_keyfile_name(
                    ENV_GCP_CREDENTIALS,
                    scopes=self.SCOPES,
                )
            )
        else:
            auth_client.credentials = (
                ServiceAccountCredentials.from_json_keyfile_dict(
                    json.loads(ENV_GCP_CREDENTIALS), scopes=self.SCOPES
                )
            )

        self.__client = GoogleDrive(auth_client)
        logging.debug("Connected to the Chicago Maroon Google Drive.")

    def upload_file_to_maroon_tech_folder(self, file_name: str) -> None:
        """
        Upload the parametrized file to the Chicago Maroon's Tech folder.
        """
        print(file_name)
        logging.debug(
            "Starting upload process to the Chicago Maroon's Tech "
            f"Google Drive folder for: {file_name}"
        )

        file_id = ""
        file_list = self.__client.ListFile(
            {
                "q": f"'{ENV_GOOGLE_DRIVE_MAROON_FOLDER_ID}' in parents "
                "and trashed=False"
            }
        ).GetList()
        for f in file_list:
            if f["title"] == file_name:
                file_id = f["id"]

        if file_id:
            file = self.__client.CreateFile({"id": file_id})
            logging.debug(f"Updating file: {file_name}.")
        else:
            file = self.__client.CreateFile(
                {
                    "parents": [
                        {
                            "id": ENV_GOOGLE_DRIVE_MAROON_FOLDER_ID,
                            "title": "Tech",
                        }
                    ],
                    "title": file_name,
                    "mimeType": "text/csv",
                }
            )
            logging.debug(f"Creating file: {file_name}.")

        file.SetContentFile(file_name)
        file.Upload()

        logging.debug(
            "Finished upload process to the Chicago Maroon's Tech "
            f"Google Drive folder for: {file_name}"
        )
