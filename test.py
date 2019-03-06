from __future__ import print_function

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
download_list = []
update_rate = 0.2 * 60
done = False
ydl_opts = {
    'ignore-errors': True,
    'o': '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'
}


class StoreDictKeyPair(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        my_dict = {}
        for kv in values.split(","):
            k, v = kv.split("=")
            my_dict[k] = v
        setattr(namespace, self.dest, my_dict)


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
    time.sleep(0.1)


def add_to_update_queue(item):
    playlists_to_update.append(item)
    print(item['snippet']['title'], "added to update queue")


def download_playlist(item):
    download_list.append(item)
    print('Downloading', item['snippet']['title'])
    youtube_dl.YoutubeDL(ydl_opts).download([item['id']])

def download_update(item):
    id=item['contentDetails']['videoId']
    print('Downloading', id)
    youtube_dl.YoutubeDL(ydl_opts).download([id])
 
   


def job():
    print("I'm working...")
    map(update, playlists_to_update)



def update(item):
    last_vid = item.get('last_vid')
    id = item['id']
    if last_vid:
        if last_vid != youtube.get_last_vid(id):
            list = youtube.get_playlist_items_list(id)['items']
            i = next((index for (index, d) in enumerate(list) if d['contentDetails']['videoId'] == last_vid), None)
            map(download_update, list[:i])
        else:
            print('no update')
    item['last_vid'] = youtube.get_last_vid(id)


def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)


def init(update_rate):
    global playlists_to_update
    try:
        with open('update_list.dat', 'r+b') as update_list_dat:
            playlists_to_update = pickle.load(update_list_dat)
    except IOError:
        open('update_list.dat', 'w').close()

    schedule.every(update_rate).seconds.do(job)
    new_thread(schedule_thread)


def new_thread(target):
    threading.Thread(target=target).start()


parser = argparse.ArgumentParser(
    description="Automated youtube playlist downloader")
group = parser.add_mutually_exclusive_group()
group.add_argument('-lk', '--liked', action='store_true', help='Add your liked videos')
group.add_argument('-p', '--my-playlists', action='store_true', help='List your playlists')
group.add_argument('-l', '--link', help='Add playlist by link')
group.add_argument('-c', '--channel', help='Add channel uploads')
parser.add_argument('-d', '--download', action='store_true', help='Add and download current playlist retroactively')
parser.add_argument('-o', '--options', dest='ydl_opts', action=StoreDictKeyPair, metavar='OPT1=VAL1,OPT2=OPT2...',
                    help='youtube-dl options')

args = parser.parse_args()

if __name__ == '__main__':

    if len(sys.argv) > 1:
        youtube.init()
        init(update_rate)
        new_thread(animate)

        if args.my_playlists:
            playlists = youtube.get_my_playlists()
            stop_anim()

            for (i, playlist) in enumerate(playlists['items']):
                print(i, ') ', playlist['snippet']['title'], sep='')

            integer = input("\nEnter playlist number: ")
            item = playlists['items'][integer]
            add_to_update_queue(item)

            if args.download:
                download_playlist(item)
        elif args.link:
            stop_anim()
            print(args.custom_link)
        elif args.channel:
            print()

        with open('update_list.dat', 'wb') as update_list_dat:
            pickle.dump(playlists_to_update, update_list_dat)
    else:
        parser.print_help()
