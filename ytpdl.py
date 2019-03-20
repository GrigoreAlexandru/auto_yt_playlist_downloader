"""
Entry module containing the logic and CLI.
The program currently works by polling the Youtube API at the set rate in a separate thread.
"""
from __future__ import print_function, unicode_literals

import itertools
import pickle
import sys
import threading
import time
import schedule
import argparse

import youtube
import youtube_dl

parser = argparse.ArgumentParser(
        description="Automated youtube playlist downloader")
saved_playlists = []

poll_rate = 0.2 * 60  # In seconds
done = False
ydl_opts = {
    'ignore-errors': True

}


class StoreDictKeyPair(argparse.Action):
    """
    Custom argparse action to store arguments as key-value pair dict.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        my_dict = {}
        for kv in values.split(","):
            k, v = kv.split("=")
            my_dict[k] = v
        setattr(namespace, self.dest, my_dict)


def init(poll_rate):
    """
    Reads or creates the file that contains the saved playlists and scheldules the Youtube API poll.
    """
    global saved_playlists
    try:
        with open('playlists.dat', 'r+b') as playlists:
            saved_playlists = pickle.load(playlists)
    except IOError:
        open('playlists.dat', 'w').close()

    schedule.every(poll_rate).seconds.do(job)
    new_thread(schedule_thread)


def animate():
    """
    Loading animation.
    """
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        print('\rloading ' + c, end='')
        sys.stdout.flush()
        time.sleep(0.1)
    print('\rDone        ')


def stop_anim():
    """
    Loading animation.
    """
    global done
    done = True
    time.sleep(0.3)


def save_playlist(item):
    """
    Saves playlist.
    """
    saved_playlists.append(item)
    print(item['title'], "added to update queue")


def download(item, title):
    """
    Downloads playlist and sets youtubedls download location to 'playlist_title/video_title' .
    """
    ydl_opts['outtmpl'] = '{}\%(title)s.%(ext)s'.format(title)
    youtube_dl.YoutubeDL(ydl_opts).download([item['id']])


def job():
    """
    Job to be executed.
    """
    map(update, saved_playlists)


def update(playlist):
    """
    Update logic. Checks for new items and downloads from the last known item.
    """
    new_playlist = youtube.get_playlist_items(playlist['id'])
    new_vid = new_playlist[0]
    old_vid = playlist.get('latest')

    if old_vid and old_vid['id'] != new_vid['id']:
        old_vid_pos = next((index for (index, item) in enumerate(new_playlist) if item['id'] == old_vid['id']), None)
        map(download, new_playlist[:old_vid_pos], [playlist['title']])

    playlist['latest'] = new_vid


def schedule_thread():
    """
    Schedules the update thead.
    """
    while True:
        schedule.run_pending()
        time.sleep(1)


def new_thread(target):
    """
    Creates a new thread.
    """
    threading.Thread(target=target).start()

def get_args():
    """
    Sets up argparse.
    :return: parsed arguments
    """
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-lk', '--liked', action='store_true', help='Add your liked videos')
    group.add_argument('-mp', '--my-playlists', action='store_true', help='Choose from your playlists')
    group.add_argument('-id', '--id', help='Add playlist by id')
    group.add_argument('-ch', '--channel', help='Add channel uploads, by channel id')
    parser.add_argument('-d', '--download', action='store_true', help='Add and download current playlist retroactively')
    parser.add_argument('-o', '--options', dest='ydl_opts', action=StoreDictKeyPair, metavar='OPT1=VAL1,OPT2=OPT2...',
                        help='youtube-dl options')
    parser.add_argument('-ls', '--list', action='store_true', help='List saved playlists')

    return parser.parse_args()


def main(args):
    """
    Main logic and CLI handler.
    """
    if len(sys.argv) > 1:
        youtube.init()
        init(poll_rate)
        new_thread(animate)

        if args.my_playlists:
            playlists = youtube.get_my_playlists()
            stop_anim()

            for (i, playlist) in enumerate(playlists):
                print(i, ') ', playlist['title'], sep='')

            integer = input("\nEnter playlist number: ")
            playlist = playlists[integer]
            save_playlist(playlist)

            if args.download:
                download(playlist, playlist['title'])
        elif args.id:
            stop_anim()
            playlist = youtube.get_playlist(args.id)
            save_playlist(playlist)
        elif args.channel:
            stop_anim()
            playlist = youtube.get_uploads_playlist(args.channel)
            save_playlist(playlist)
        elif args.list:
            stop_anim()
            print([playlist['title'].encode('utf-8') for playlist in saved_playlists])

        with open('update_list.dat', 'wb') as update_list_dat:
            pickle.dump(saved_playlists, update_list_dat)
    else:
        parser.print_help()


if __name__ == '__main__':
    main(get_args())
