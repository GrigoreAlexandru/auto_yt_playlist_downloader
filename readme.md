## ytpdl
CLI tool that automates the downloading of youtube playlists. The tool polls the Youtube API at a set rate and downloads any new update.
Uses [youtube-dl](https://github.com/ytdl-org/youtube-dl) to download videos. Also supports passing options to youtube-dl.

## Install

``` 
git clone https://github.com/GrigoreAlexandru/auto_yt_playlist_downloader.git
```

```
pip install -r auto_yt_playlist_downloader/requirements.txt
```

## Usage
Docs [here](https://grigorealexandru.github.io/auto_yt_playlist_downloader/docs/).
```
ytpdl.py [-h] [-lk | -mp | -id ID | -ch CHANNEL] [-d]
                [-o OPT1=VAL1,OPT2=OPT2...] [-ls]

Automated youtube playlist downloader

optional arguments:
  -h, --help            show this help message and exit
  -lk, --liked          Add your liked videos
  -mp, --my-playlists   Choose from your playlists
  -id ID, --id ID       Add playlist by id
  -ch CHANNEL, --channel CHANNEL
                        Add channel uploads, by channel id
  -d, --download        Add and download current playlist retroactively
  -o OPT1=VAL1,OPT2=OPT2..., --options OPT1=VAL1,OPT2=OPT2...
                        youtube-dl options
  -ls, --list           List saved playlists```
