from __future__ import print_function
import os
import pickle

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

client = None


# Getting credentials and storing them
def init():
    if not os.path.exists('credentials.dat'):
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES)
        credentials = flow.run_local_server(host='localhost',
                                            port=8080,
                                            authorization_prompt_message='Please visit this URL: {url}',
                                            success_message='The auth flow is complete; you may close this window.',
                                            open_browser=True)
        with open('credentials.dat', 'wb') as credentials_dat:
            pickle.dump(credentials, credentials_dat)
    else:
        with open('credentials.dat', 'rb') as credentials_dat:
            credentials = pickle.load(credentials_dat)
    if credentials.expired:
        print("Refreshing youtube API tokens...")
        credentials.refresh(Request())
    global client
    client = build(API_SERVICE_NAME, API_VERSION,
                   credentials=credentials)


# =====================================
#     Custom Youtube api requests
# =====================================

def _playlistitems_list(id, token=None, maxResults=50):
    return client.playlistItems().list(
        part='snippet',
        maxResults=maxResults,
        playlistId=id,
        pageToken=token
    ).execute()


def _channel_related_playlists(id=None, mine=None):
    return client.channels().list(
        part='contentDetails',
        id=id,
        mine=mine
    ).execute()['items'][0]['contentDetails']['relatedPlaylists']


def _playlists_list(token=None, mine=None, id=None):
    return client.playlists().list(
        part='snippet',
        mine=mine,
        maxResults=50,
        pageToken=token,
        id=id
    ).execute()


def get_my_playlists():
    def get_items():
        return [{
            'title': item['snippet']['title'],
            'id': item['id']
        } for item in response['items']]

    response = _playlists_list(mine=True)
    token = response.get('nextPageToken')
    playlists = get_items()
    while token:
        response = _playlists_list(token, True)
        token = response.get('nextPageToken')
        playlists.extend(get_items())
    return playlists


def get_playlist_items(id, all=False, maxResults=50):
    def get_items():
        return [{
            'title': item['snippet']['title'],
            'id': item['snippet']['resourceId']['videoId']
        } for item in response['items']]

    response = _playlistitems_list(id, maxResults=maxResults)
    token = response.get('nextPageToken')
    videos = get_items()
    while token and all:
        response = _playlistitems_list(id, token, maxResults)
        token = response.get('nextPageToken')
        videos.extend(get_items())
    return videos


def get_liked_playlist():
    liked_id = _channel_related_playlists(mine=True)['likes']
    return get_playlist_items(liked_id, True)


def get_uploads_playlist(id):
    upload_id = _channel_related_playlists(id)['uploads']
    return get_playlist(upload_id)


def get_latest_id(id):
    return get_playlist_items(id, maxResults=1)[0]['id']


def get_playlist(id):
    item = _playlists_list(id=id)['items']
    return {
        'title': item[0]['snippet']['title'],
        'id': item[0]['id']
    }
