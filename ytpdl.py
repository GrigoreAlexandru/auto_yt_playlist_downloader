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

# Lists of Youtube playlist resource
playlists_to_update = []

update_rate = 0.2 * 60
done = False
ydl_opts = {
    'ignore-errors': True

}


class StoreDictKeyPair(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        my_dict = {}
        for kv in values.split(","):
            k, v = kv.split("=")
            my_dict[k] = v
        setattr(namespace, self.dest, my_dict)


def init(update_rate):
    global playlists_to_update
    try:
        with open('playlists.dat', 'r+b') as playlists:
            playlists_to_update = pickle.load(playlists)
    except IOError:
        open('playlists.dat', 'w').close()

    schedule.every(update_rate).seconds.do(job)
    new_thread(schedule_thread)


def animate():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        print('\rloading ' + c, end='')
        sys.stdout.flush()
        time.sleep(0.1)
    print('\rDone        ')


def stop_anim():
    global done
    done = True
    time.sleep(0.3)


def add_to_update_queue(item):
    playlists_to_update.append(item)
    print(item['title'], "added to update queue")


def download(item, title):
    ydl_opts['outtmpl'] = '{}\%(title)s.%(ext)s'.format(title)
    youtube_dl.YoutubeDL(ydl_opts).download([item['id']])


def job():
    map(update, playlists_to_update)


def update(playlist):
    new_playlist = youtube.get_playlist_items(playlist['id'])
    new_vid = new_playlist[0]
    old_vid = playlist.get('latest')

    if old_vid and old_vid['id'] != new_vid['id']:
        old_vid_pos = next((index for (index, item) in enumerate(new_playlist) if item['id'] == old_vid['id']), None)
        map(download, new_playlist[:old_vid_pos], [playlist['title']])

    playlist['latest'] = new_vid


def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)


def new_thread(target):
    threading.Thread(target=target).start()


parser = argparse.ArgumentParser(
    description="Automated youtube playlist downloader")
group = parser.add_mutually_exclusive_group()
group.add_argument('-lk', '--liked', action='store_true', help='Add your liked videos')
group.add_argument('-mp', '--my-playlists', action='store_true', help='Choose from your playlists')
group.add_argument('-id', '--id', help='Add playlist by id')
group.add_argument('-ch', '--channel', help='Add channel uploads, by channel id')
parser.add_argument('-d', '--download', action='store_true', help='Add and download current playlist retroactively')
parser.add_argument('-o', '--options', dest='ydl_opts', action=StoreDictKeyPair, metavar='OPT1=VAL1,OPT2=OPT2...',
                    help='youtube-dl options')
parser.add_argument('-ls', '--list', action='store_true', help='List saved playlists')

args = parser.parse_args()


def main():
    if len(sys.argv) > 1:
        youtube.init()
        init(update_rate)
        new_thread(animate)

        if args.my_playlists:
            playlists = youtube.get_my_playlists()
            stop_anim()

            for (i, playlist) in enumerate(playlists):
                print(i, ') ', playlist['title'], sep='')

            integer = input("\nEnter playlist number: ")
            item = playlists[integer]
            add_to_update_queue(item)

            if args.download:
                download(item, item['title'])
        elif args.id:
            stop_anim()
            playlist = youtube.get_playlist(args.id)
            add_to_update_queue(playlist)
        elif args.channel:
            stop_anim()
            playlist = youtube.get_uploads_playlist(args.channel)
            add_to_update_queue(playlist)
        elif args.list:
            stop_anim()
            print([playlist['title'].encode('utf-8') for playlist in playlists_to_update])

        with open('update_list.dat', 'wb') as update_list_dat:
            pickle.dump(playlists_to_update, update_list_dat)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
