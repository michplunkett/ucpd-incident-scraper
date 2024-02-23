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

    def __init__(self):
        auth_client = GoogleAuth()
        auth_client.auth_method = "service"
        if ENV_GCP_CREDENTIALS.endswith(FILE_TYPE_JSON):
            auth_client.credentials = (
                ServiceAccountCredentials.from_json_keyfile_name(
                    ENV_GCP_CREDENTIALS
                )
            )
        else:
            auth_client.credentials = ServiceAccountCredentials.from_json(
                json.loads(ENV_GCP_CREDENTIALS)
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
        drive_file = self.__client.CreateFile({"parents": [{"id": ENV_GOOGLE_DRIVE_MAROON_FOLDER_ID, "title": file_name}]})
        drive_file.SetContentFile(file_name)

        drive_file.Upload()
        logging.debug(
            "Finished upload process to the Chicago Maroon's Tech "
            f"Google Drive folder for: {file_name}"
        )
