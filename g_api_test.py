#coding=utf-8
import httplib2
import pprint

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow


# Copy your credentials from the APIs Console
CLIENT_ID = '581589539477.apps.googleusercontent.com'
CLIENT_SECRET = 'CAFrFxlZ_C22KoyfusIDheYi'

# Check https://developers.google.com/drive/scopes for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

# Redirect URI for installed apps
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

# Path to the file to upload
FILENAME = 'wtf.py'; mt = 'text/plain'
FILENAME = 'index.doc' ; mt = 'application/msword'

# Run through the OAuth flow and retrieve credentials
flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)
authorize_url = flow.step1_get_authorize_url()
print 'Go to the following link in your browser: ' + authorize_url
import webbrowser
webbrowser.open(authorize_url)
code = raw_input('Enter verification code: ').strip()
credentials = flow.step2_exchange(code)

# Create an httplib2.Http object and authorize it with our credentials
http = httplib2.Http()
http = credentials.authorize(http)

drive_service = build('drive', 'v2', http=http)

# Insert a file
media_body = MediaFileUpload(FILENAME, mimetype=mt)
body = {
  'title': FILENAME,
  'description': 'A test document',
  'mimeType': mt
}

file = drive_service.files().insert(body=body, media_body=media_body).execute()
pprint.pprint(file)