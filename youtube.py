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

def get_playlist_items_list(id, token='', maxResults=50):
    return client.playlistItems().list(
        part='contentDetails',
        maxResults=maxResults,
        playlistId=id,
        pageToken=token
    ).execute()


def get_my_channel_playlists():
    return client.channels().list(
        part='contentDetails',
        mine=True
    ).execute()['items'][0]['contentDetails']['relatedPlaylists']


def get_liked_videos():
    videos = []
    liked_id = get_my_channel_playlists()['likes']
    response = get_playlist_items_list(liked_id)
    token = response.get('nextPageToken')
    while token:
        for item in response['items']:
            videos.append(item['contentDetails']['videoId'])
        response = get_playlist_items_list(liked_id, token)
        token = response.get('nextPageToken')
    return videos


def get_my_playlists(token=''):
    return client.playlists().list(
        part='snippet',
        mine=True,
        maxResults=50,
        pageToken=token
    ).execute()


def get_all_my_playlists():
    playlists = []
    response = get_my_playlists()
    token = response.get('nextPageToken')
    while token:
        playlists.append(response['items'])
        response = get_my_playlists(token)
        token = response.get('nextPageToken')
    return playlists


def get_last_vid(id):
    return get_playlist_items_list(id, maxResults=1)['items'][0]['contentDetails']['videoId']
