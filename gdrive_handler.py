import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import pickle
from config import GDRIVE_CREDENTIALS, GDRIVE_FOLDER_ID

class GoogleDriveHandler:
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    GDRIVE_CREDENTIALS, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def upload_file(self, file_path, file_name, mime_type, folder_id=None):
        """Upload file to Google Drive"""
        folder_id = folder_id or GDRIVE_FOLDER_ID
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, mimetype=mime_type)
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return file.get('id')
    
    def download_file(self, file_id, destination_path):
        """Download file from Google Drive"""
        request = self.service.files().get_media(fileId=file_id)
        with open(destination_path, 'wb') as f:
            f.write(request.execute())
    
    def list_files(self, folder_id=None):
        """List files in Google Drive folder"""
        folder_id = folder_id or GDRIVE_FOLDER_ID
        
        query = f"'{folder_id}' in parents"
        results = self.service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, createdTime)"
        ).execute()
        
        return results.get('files', [])