import os
import re
import sys
import time
import json
import socket
import base64
import pygame
import signal
import logging
import threading
import youtube_dl
from subprocess import Popen, DEVNULL
from sonos_tasks import rear_movie

from PIL import Image
from omxplayer.player import OMXPlayer
from omxplayer.keys import *

logger = logging.getLogger("RaspberryCast")
volume = 0
player = None

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
ENV = {**os.environ, 'DISPLAY': ':0'}
# Volume
try:
    with open(os.path.join(DIR_PATH, "volume"), "r") as f:
        volume = int(f.read())
except Exception as e:
    volume = 0

# SIGTERM handler
def terminationhandler(signum, frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, terminationhandler)

# Pygame Initialization
def init_pygame():
    pygame.display.init()
    pygame.font.init()
    pygame.mouse.set_visible(0)
    return pygame.display.set_mode((0,0), pygame.FULLSCREEN)

def aspectscale(img, size):
    ix,iy = img.get_size()
    bx, by = size

    if ix > iy:
        # fit to width
        scale_factor = bx/float(ix)
        sy = scale_factor * iy
        if sy > by:
            scale_factor = by/float(iy)
            sx = scale_factor * ix
            sy = by
        else:
            sx = bx
    else:
        # fit to height
        scale_factor = by/float(iy)
        sx = scale_factor * ix
        if sx > bx:
            scale_factor = bx/float(ix)
            sx = bx
            sy = scale_factor * iy
        else:
            sy = by

    return pygame.transform.scale(img, (int(sx), int(sy)))


def displaysurface(surface, show_ip):
    pygame.quit()
    # x_centered = screen.get_size()[0] / 2 - surface.get_size()[0] / 2
    # y_centered = screen.get_size()[1] / 2 - surface.get_size()[1] / 2
    # 
    # screen.blit(surface, (x_centered, y_centered))
    # 
    # if show_ip:
    #     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     s.connect(("8.8.8.8", 80))
    #     ip_address = s.getsockname()[0]
    #     s.close()
    #     font = pygame.font.SysFont('Arial', screen.get_size()[0] // 24)
    #     text = font.render(ip_address, True, (128, 128, 128))
    #     screen.blit(text, (screen.get_size()[0] // 12, screen.get_size()[1] * 7 // 8))
    # 
    # pygame.display.update()


def displayimage(imagefilename):
    surface = pygame.Surface(screen.get_size()).convert_alpha()
    pil_img = Image.open(imagefilename).convert('RGB')
    mode = pil_img.mode
    size = pil_img.size
    data = pil_img.tobytes()
    img = aspectscale(pygame.image.fromstring(data, size, mode), (screen.get_size()))
    x_centered = screen.get_size()[0] / 2 - img.get_size()[0] / 2
    y_centered = screen.get_size()[1] / 2 - img.get_size()[1] / 2
    surface.blit(img, (x_centered, y_centered))
    displaysurface(surface, False)

ready_surf = None
processing_surf = None
# ready_surf = pygame.Surface(screen.get_size())
# ready_img = aspectscale(pygame.image.load(os.path.join(DIR_PATH, "images", "ready.jpg")), (screen.get_size()))
# ready_img_x_centered = screen.get_size()[0] / 2 - ready_img.get_size()[0] / 2
# ready_img_y_centered = screen.get_size()[1] / 2 - ready_img.get_size()[1] / 2
# ready_surf.blit(ready_img, (ready_img_x_centered, ready_img_y_centered))

# processing_surf = pygame.Surface(screen.get_size())
# processing_img = aspectscale(pygame.image.load(os.path.join(DIR_PATH, "images", "processing.jpg")), (screen.get_size()))
# processing_img_x_centered = screen.get_size()[0] / 2 - processing_img.get_size()[0] / 2
# processing_img_y_centered = screen.get_size()[1] / 2 - processing_img.get_size()[1] / 2
# processing_surf.blit(processing_img, (processing_img_x_centered, processing_img_y_centered))

displaysurface(ready_surf, True)

def playeraction(action):
    global player
    try:
        if action == SEEK_FORWARD_LARGE: # action throws error
            player.seek(60)
        elif action == SEEK_BACK_LARGE: # action throws error
            player.seek(-60)
        else:
            player.action(action)
    except Exception as e:
        print(e)
    except:
        raise
    
def getposition():
    global player
    tot = player.metadata()['mpris:length']/1000/1000
    pos = player.position()
    if pos and tot:
        tot_fmt = time.strftime('%H:%M:%S', time.gmtime(tot))
        pos_fmt = time.strftime('%H:%M:%S', time.gmtime(pos))
        return "{} / {}".format(pos_fmt, tot_fmt)
        
def inspect():
    global player
    import pdb; pdb.set_trace()

def launchhome():
    global player
    try:
        player.quit()  #Kill previous instance of OMX
    except Exception as e:
        print(e)
    except:
        raise

    displaysurface(ready_surf, True)


def launchimage(url):
    global player
    try:
        player.quit()  #Kill previous instance of OMX
    except Exception as e:
        print(e)
    except:
        raise

    try:
        os.system("rm download/image")
        if "data:image/" in url:
            if "base64," in url:
                logger.info("Base64 Image Data Received")
                data = url.split(',')[1].strip()
                pad = len(data) % 4
                data += "=" * pad
                b64img = base64.b64decode(data)
                imgfile = open('download/image', 'wb')
                imgfile.write(b64img)
                imgfile.close()
        else:
            logger.info("Url Image Data Received")
            os.system("wget -O download/image " + url)
    except Exception as e:
        print(e)
    except:
        raise

    displayimage(os.path.join(DIR_PATH, "download", "image"))

def launchvideo(url, config, sub=False):
    setState("2")

    try:
        player.quit()  #Kill previous instance of OMX
    except Exception as e:
        print(e)
    except:
        raise

    if config["new_log"]:
        displaysurface(processing_surf, False)

    logger.info('Extracting source video URL...')
    out = return_full_url(url, sub=sub, slow_mode=config["slow_mode"])

    logger.debug("Full video URL fetched.")

    thread = threading.Thread(target=playWithOMX, args=(out, sub,),
            kwargs=dict(width=config["width"], height=config["height"],
                        new_log=config["new_log"]))
    thread.start()


def queuevideo(url, config, onlyqueue=False):
    logger.info('Extracting source video URL, before adding to queue...')

    out = return_full_url(url, sub=False, slow_mode=config["slow_mode"])

    logger.info("Full video URL fetched.")

    if getState() == "0" and not onlyqueue:
        logger.info('No video currently playing, playing video instead of \
adding to queue.')
        thread = threading.Thread(target=playWithOMX, args=(out, False,),
            kwargs=dict(width=config["width"], height=config["height"],
                        new_log=config["new_log"]))
        thread.start()
    else:
        if out is not None:
            with open('video.queue', 'a') as f:
                f.write(out+'\n')

def openlocal(url, rev_cmd=None, user=None, ip=None):
    logger.info('Received URL local open: ' + url)
    pygame.quit()
    os.system('pkill -f vlc')
    os.system('pkill -f chrom')
    open_cmd = "vlc -f '{}'".format(url) if is_direct(url) else chromium_media_cmd(url)
    nohup(open_cmd)
    if rev_cmd and user and ip:
        run_cmd = "ssh {}@{} '{}'".format(user, ip, rev_cmd)
        nohup(run_cmd)
        
def chromium_media_cmd(url):
    prefix = "Exec=chromium-browser %U"
    fpath = "/usr/share/applications/chromium-media-browser.desktop"
    file = open(fpath, "r")
    for line in file:
        if re.search(prefix, line):
            exec_line = line 
            break
    exp_prefix = "chromium-browser '{}'".format(url)
    return exec_line.replace(prefix, exp_prefix) if exec_line else ""

def nohup(cmd):
    logger.info("Running synchronous shell command: " + cmd)
    nh = "nohup {} &".format(cmd)
    result = Popen([nh], shell=True, stdout=DEVNULL, stderr=DEVNULL, close_fds=True, env=ENV)
    logger.info("Done; PID {}".format(result.pid))
    return result

def is_direct(url):
    yt = "youtu" in url
    vm = "vimeo" in url
    gv = ".googlevideo.com/" in url
    fext = url[-4:] in (".avi", ".mkv", ".mp4", ".mp3")
    return gv or fext # or yt or vm
    
def return_full_url(url, sub=False, slow_mode=False):
    logger.debug("Parsing source url for "+url+" with subs :"+str(sub))

    if (is_direct(url) or sub):
        logger.debug('Direct video URL, no need to use youtube-dl.')
        return url

    ydl = youtube_dl.YoutubeDL(
        {
            'logger': logger,
            'noplaylist': True,
            'ignoreerrors': True,
        })  # Ignore errors in case of error in long playlists
    with ydl:  # Downloading youtub-dl infos. We just want to extract the info
        result = ydl.extract_info(url, download=False)

    if result is None:
        logger.error(
            "Result is none, returning none. Cancelling following function.")
        return None

    if 'entries' in result:  # Can be a playlist or a list of videos
        video = result['entries'][0]
    else:
        video = result  # Just a video

    if "youtu" in url:
        if slow_mode:
            for i in video['formats']:
                if i['format_id'] == "18":
                    logger.debug("Youtube link detected, extracting url in 360p")
                    return i['url']
        else:
            logger.debug('''CASTING: Youtube link detected. Extracting url in maximal quality.''')
            for fid in ('22', '18', '36', '17'):
                for i in video['formats']:
                    if i['format_id'] == fid:
                        logger.debug(
                            'CASTING: Playing highest video quality ' +
                            i['format_note'] + '(' + fid + ').'
                        )
                        return i['url']
    elif "vimeo" in url:
        if slow_mode:
            for i in video['formats']:
                if i['format_id'] == "http-360p":
                    logger.debug("Vimeo link detected, extracting url in 360p")
                    return i['url']
        else:
            logger.debug('Vimeo link detected, extracting url in maximal quality.')
            return video['url']
    else:
        logger.debug('''Video not from Youtube or Vimeo. Extracting url in maximal quality.''')
        return video['url']

def playlist(url, cast_now, config):
    logger.info("Processing playlist.")

    if cast_now:
        logger.info("Playing first video of playlist")
        launchvideo(url, config)  # Launch first video
    else:
        queuevideo(url, config)

    thread = threading.Thread(target=playlistToQueue, args=(url, config))
    thread.start()

def playlistToQueue(url, config):
    logger.info("Adding every videos from playlist to queue.")
    ydl = youtube_dl.YoutubeDL(
        {
            'logger': logger,
            'extract_flat': 'in_playlist',
            'ignoreerrors': True,
        })
    with ydl:  # Downloading youtub-dl infos
        result = ydl.extract_info(url, download=False)
        for i in result['entries']:
            logger.info("queuing video")
            if i != result['entries'][0]:
                queuevideo(i['url'], config)

def playWithOMX(url, sub, width="", height="", new_log=False):
    global player
    logger.info("Starting OMXPlayer now.")
    rear_movie(60)

    logger.info("Attempting to read resolution from configuration file.")

    resolution = ""

    if width or height:
        resolution = " --win '0 0 {0} {1}'".format(width, height)

    setState("1")
    displaysurface(ready_surf, True)
    args = "-b" + resolution + " --vol " + str(volume) + " --orientation 180 " + " -o hdmi"
    if sub:
        player = OMXPlayer(url, args + " --subtitles subtitle.srt")
    elif url is None:
        pass
    else:
        player = OMXPlayer(url, args)

    try:
        os.system("sudo renice -12 -g `pgrep omx`")
        logger.info("renice'd omx to -12")
        
        while not player.playback_status() == "Stopped":  # Wait until video finished or stopped
            time.sleep(0.5)
    except Exception as e:
        print(e)
    except:
        raise

    if getState() != "2":  # In case we are again in the launchvideo function
        setState("0")
        with open('video.queue', 'r') as f:
            # Check if there is videos in queue
            first_line = f.readline().replace('\n', '')
            if first_line != "":
                logger.info("Starting next video in playlist.")
                with open('video.queue', 'r') as fin:
                    data = fin.read().splitlines(True)
                with open('video.queue', 'w') as fout:
                    fout.writelines(data[1:])
                thread = threading.Thread(
                    target=playWithOMX, args=(first_line, False,),
                        kwargs=dict(width=width, height=height,
                                    new_log=new_log),
                )
                thread.start()
            else:
                logger.info("Playlist empty, skipping.")


def setState(state):
    # Write to file so it can be accessed from everywhere
    os.system("echo "+state+" > state.tmp")

def getState():
    with open('state.tmp', 'r') as f:
        return f.read().replace('\n', '')

def setVolume(vol):
    global volume
    if vol == "more":
        volume += 300
    if vol == "less":
        volume -= 300
    with open(os.path.join(DIR_PATH, "volume"), "w") as f:
        f.write(str(volume))
