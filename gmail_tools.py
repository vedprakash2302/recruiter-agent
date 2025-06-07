import os
import base64
import json
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import googleapiclient.discovery_cache.base
import pickle
from typing import Dict, List, Optional, Any, Tuple

# Disable discovery cache warnings
import logging
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

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
                    self.service = build('gmail', 'v1', credentials=self.creds, cache_discovery=False)
    
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    self._save_credentials()
                    self.service = build('gmail', 'v1', credentials=self.creds, cache_discovery=False)
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
        self.service = build('gmail', 'v1', credentials=self.creds, cache_discovery=False)
    
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
            A Message with full details.
        """
        try:
            message = self.service.users().messages().get(
                userId=user_id, 
                id=msg_id, 
                format='full',
                metadataHeaders=['From', 'To', 'Subject', 'Date', 'Message-ID', 'References', 'In-Reply-To']
            ).execute()
            return self._format_message(message)
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
            
    def get_thread_messages(self, user_id: str, thread_id: str) -> List[Dict]:
        """Get all messages in a thread.
        
        Args:
            user_id: User's email address or 'me'.
            thread_id: The ID of the thread to fetch.
            
        Returns:
            List of messages in the thread, sorted by date (oldest first).
        """
        try:
            thread = self.service.users().threads().get(
                userId=user_id,
                id=thread_id,
                format='full'
            ).execute()
            
            messages = []
            if 'messages' in thread:
                for msg in thread['messages']:
                    full_message = self.service.users().messages().get(
                        userId=user_id,
                        id=msg['id'],
                        format='full',
                        metadataHeaders=['From', 'To', 'Subject', 'Date', 'Message-ID', 'References', 'In-Reply-To']
                    ).execute()
                    messages.append(self._format_message(full_message))
            
            # Sort messages by internalDate (oldest first)
            messages.sort(key=lambda x: int(x.get('internalDate', 0)))
            return messages
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def _clean_email_body(self, body: str) -> str:
        """Clean up email body by removing quoted/replied text."""
        if not body:
            return ''
            
        # Common patterns for quoted text in email replies
        quote_patterns = [
            r'On\s.+\sat\s.+,\s.+\s<.+@.+>\s+wrote:',  # Gmail style
            r'On\s.+\s+<.+@.+>\s+wrote:',  # Another Gmail style
            r'On\s.+\s+<.+@.+>\son\s.+\swrote:',  # Outlook style
            r'From:\s+.+\s+Sent:\s+.+\s+To:',  # Outlook desktop style
            r'----\s*Original Message\s*----',  # Common separator
            r'From:\s*\S+@\S+',  # Simple From: email pattern
            r'To:\s*\S+@\S+',    # Simple To: email pattern
            r'On\s+\w+,\s+\w+\s+\d+,\s+\d+\s+at\s+\d+:\d+\s+[AP]M\s+\w+\s+<',  # Another common pattern
            r'On\s+\w+\s+\d{1,2},\s+\d{4},\s+at\s+\d+:\d+\s+[AP]M\s+\w+\s+<',  # Another variation
            r'On\s+\w+\s+\d{1,2}\s+\w+\s+\d{4},\s+at\s+\d+:\d+\s+[AP]M\s+\w+\s+<',  # Another variation
            r'On\s+\w+\s+\d{1,2}\s+\w+\s+\d{4}\s+at\s+\d+:\d+\s+[AP]M\s+\w+\s+<',  # Another variation
            r'On\s+\w+\s+\d{1,2}\s+\w+\s+\d{4}\s+at\s+\d+:\d+\s+[AP]M\s+\w+\s+\([^)]+\)\s+<',  # With timezone
            r'On\s+\w+\s+\d{1,2}\s+\w+\s+\d{4}\s+at\s+\d+:\d+\s+[AP]M\s+[^<]+\s+<',  # With name and email
            r'On\s+\w+\s+\d{1,2}\s+\w+\s+\d{4}\s+at\s+\d+:\d+\s+[AP]M\s+[^<]+\s+<[^>]+>\s+wrote:',  # With name, email and wrote
            r'On\s+\w+\s+\d{1,2}\s+\w+\s+\d{4}\s+at\s+\d+:\d+\s+[AP]M\s+[^<]+\s+<[^>]+>\s+said:',  # With name, email and said
        ]
        
        # Split the body into lines
        lines = body.split('\n')
        clean_lines = []
        
        for line in lines:
            # Check if this line matches any of the quote patterns
            is_quote = False
            for pattern in quote_patterns:
                import re
                if re.search(pattern, line, re.IGNORECASE):
                    is_quote = True
                    break
            
            # If we hit a quote line, stop adding lines
            if is_quote:
                break
                
            clean_lines.append(line)
        
        # Join the lines back together and clean up
        clean_body = '\n'.join(clean_lines).strip()
        
        # Remove any trailing dashes or underscores that might be left
        clean_body = re.sub(r'[_-]+\s*$', '', clean_body).strip()
        
        return clean_body

    def _format_message(self, message: Dict) -> Dict:
        """Format message data into a simplified structure."""
        if not message:
            return {}
            
        # Extract headers
        headers = {}
        for header in message.get('payload', {}).get('headers', []):
            name = header.get('name', '').lower()
            if name in ['from', 'to', 'subject', 'date']:
                headers[name] = header.get('value', '')
        
        # Get body content
        body = ''
        if 'parts' in message.get('payload', {}):
            for part in message['payload']['parts']:
                if part.get('mimeType') == 'text/plain' and 'body' in part and 'data' in part['body']:
                    try:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                    except:
                        continue
        elif 'body' in message.get('payload', {}) and 'data' in message['payload']['body']:
            try:
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
            except:
                pass
                
        # Clean up the body to remove quoted/replied text
        import re  # Ensure re is imported at the top of the file
        body = self._clean_email_body(body)
        
        return {
            'id': message.get('id'),
            'thread_id': message.get('threadId'),
            'from': headers.get('from', ''),
            'to': headers.get('to', ''),
            'subject': headers.get('subject', '(No subject)'),
            'date': headers.get('date', ''),
            'body': body.strip()
        }
        
    def get_messages_by_email(self, email: str, max_results: int = 10) -> List[Dict]:
        """
        Get messages by email address (from or to).
        
        Args:
            email: Email address to search for (e.g., 'user@example.com')
            max_results: Maximum number of messages to return (max 50)
            
        Returns:
            List of message objects with basic email information
        """
        try:
            # First try with exact email match
            queries = [
                f'from:{email} OR to:{email}',  # Exact match
                f'"{email}"',                    # Quoted exact match
                email.split('@')[0],              # Just the username part
                email.replace('@', ' ')           # Without @ symbol
            ]
            
            messages = []
            seen_message_ids = set()
            
            for query in queries:
                if len(messages) >= max_results:
                    break
                    
                try:
                    # Get list of message IDs
                    results = self.service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=max_results
                    ).execute()
                    
                    # Process each message
                    for msg in results.get('messages', []):
                        if msg['id'] in seen_message_ids:
                            continue
                            
                        try:
                            # Get full message details
                            full_msg = self.service.users().messages().get(
                                userId='me',
                                id=msg['id'],
                                format='full'
                            ).execute()
                            
                            # Format the message
                            formatted = self._format_message(full_msg)
                            if formatted:
                                # Verify the email is actually in from/to
                                if (email in formatted.get('from', '') or 
                                    email in formatted.get('to', '')):
                                    messages.append(formatted)
                                    seen_message_ids.add(msg['id'])
                                    
                                    if len(messages) >= max_results:
                                        break
                                        
                        except Exception as e:
                            print(f"Error processing message {msg.get('id')}: {str(e)}")
                            continue
                            
                except Exception as e:
                    print(f"Query '{query}' failed: {str(e)}")
                    continue
            
            # Sort by date (newest first)
            messages.sort(key=lambda x: x.get('date', ''), reverse=True)
            return messages[:max_results]
            
        except Exception as e:
            print(f"Error in get_messages_by_email: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

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
