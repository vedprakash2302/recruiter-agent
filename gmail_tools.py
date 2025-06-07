import os
import base64
import json
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
from typing import Dict, List, Optional, Any, Tuple

# If modifying these scopes, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify']

TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'

class GmailService:
    def __init__(self):
        """Initialize the Gmail service with OAuth2 credentials."""
        self.creds = None
        self.service = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from token.pickle if it exists."""
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)
                if self.creds and self.creds.valid:
                    self.service = build('gmail', 'v1', credentials=self.creds)
    
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    self._save_credentials()
                    self.service = build('gmail', 'v1', credentials=self.creds)
                    return True
                except Exception:
                    return False
            return False
        return True
    
    def get_auth_url(self) -> str:
        """Get the authorization URL for OAuth2 flow."""
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(f"{CREDENTIALS_FILE} not found.")
        
        flow = self._get_flow()
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url
    
    def fetch_token(self, code: str) -> None:
        """Fetch token using the authorization code."""
        flow = self._get_flow()
        flow.fetch_token(code=code)
        self.creds = flow.credentials
        self._save_credentials()
        self.service = build('gmail', 'v1', credentials=self.creds)
    
    def _get_flow(self):
        """Create and return a Flow instance."""
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri='http://127.0.0.1:8000/oauth2callback'
        )
        return flow
    
    def _save_credentials(self):
        """Save credentials to token.pickle."""
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(self.creds, token)
    
    def get_gmail_service(self):
        """Get the Gmail service instance."""
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please authenticate first.")
        return self.service

    def create_message(self, sender: str, to: str, subject: str, message_text: str) -> Dict:
        """Create a message for an email.
        
        Args:
            sender: Email address of the sender.
            to: Email address of the receiver.
            subject: The subject of the email message.
            message_text: The text of the email message.

        Returns:
            An object containing a base64url encoded email object.
        """
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        
        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self, user_id: str, message: Dict) -> Dict:
        """Send an email message.

        Args:
            user_id: User's email address. The special value 'me' can be used to indicate the authenticated user.
            message: Message to be sent.

        Returns:
            Sent Message.
        """
        try:
            message = (self.service.users().messages().send(
                userId=user_id, body=message).execute())
            print(f'Message Id: {message["id"]}')
            return message
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise

    def list_messages(self, user_id: str = 'me', query: str = '', max_results: int = 10) -> List[Dict]:
        """List all Messages of the user's mailbox matching the query.

        Args:
            user_id: User's email address. The special value 'me' can be used to indicate the authenticated user.
            query: String used to filter messages returned.
            max_results: Maximum number of messages to return.

        Returns:
            List of messages that match the criteria of the query.
        """
        try:
            results = self.service.users().messages().list(
                userId=user_id, q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            
            if not messages:
                print('No messages found.')
                return []
                
            return messages
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def get_message(self, user_id: str, msg_id: str) -> Optional[Dict]:
        """Get a Message with given ID.

        Args:
            user_id: User's email address. The special value 'me' can be used to indicate the authenticated user.
            msg_id: The ID of the Message required.

        Returns:
            A Message.
        """
        try:
            message = self.service.users().messages().get(
                userId=user_id, id=msg_id, format='full').execute()
            return message
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

# Example usage
if __name__ == "__main__":
    try:
        gmail = GmailService()
        
        # Example: Send an email
        message = gmail.create_message(
            sender='me',
            to='yashrr1998@gmail.com',
            subject='Test Email',
            message_text='This is a test email sent from the Gmail API.'
        )
        gmail.send_message('me', message)
        
        # Example: List recent emails
        messages = gmail.list_messages(query='is:inbox', max_results=5)
        for msg in messages:
            print(f"Message ID: {msg['id']}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
