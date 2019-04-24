# Import dependencies.s
from itertools import islice
from twitch import TwitchHelix
import configparser
import logging
import threading
import subprocess
import datetime
import time
import psutil
import os
import sys
import pickledb

# Sentry.io error tracking. Uncomment if you're worried about this.
import sentry_sdk
sentry_sdk.init("https://3d82a59570f8433a9d53017e0e84efd5@sentry.io/1441155",
                max_breadcrumbs=50,
                environment='master',
)

try:
    # Setup logging.
    logging.basicConfig(filename='lars.log', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)

    # General variable setup.
    run = True
    debug = False
    fallback_quality = '480p'

    # Setup configparser and get variables from config file.
    parser = configparser.ConfigParser()
    parser.read('config.ini')
    quality = parser.get('config', 'quality')
    if quality == '':
        quality = fallback_quality
    if debug:
        print('Using quality: %s' % (quality))
    logging.info('Using quality: %s' % (quality))
    client_id_auth = parser.get('auth', 'user_id')
    if debug:
        print('Using Client-ID: %s' % (client_id_auth))
    logging.info('Using Client-ID: %s' % (client_id_auth))
    channel_names = parser.get('config', 'channels').split(', ')
    save_directory = parser.get('config', 'save_directory')
    if not save_directory.endswith('/'):
        save_directory = save_directory + "/"
    in_progress_directory = parser.get('config', 'in_progress_directory')
    if not in_progress_directory.endswith('/'):
        in_progress_directory = in_progress_directory + "/"
    sleep_time = int(parser.get('config', 'sleep_time'))
    
    # Setup Twitch API client.
    client = TwitchHelix(client_id=client_id_auth)
except KeyboardInterrupt:
    exit()
except Exception as e:
    sentry_sdk.capture_exception(e)

# Clean up channel names.
def cleanChannelNames(channel_names):
    try:
        channels_to_check = []
        for channel in channel_names:
            channel_name = channel.replace("'", "")
            channels_to_check.append(channel_name)
        return channels_to_check
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        sentry_sdk.capture_exception(e)

# Check for process.
def checkIfProcessRunning(processName):
    for proc in psutil.process_iter():
        try:
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

# Move in-progress files to saved if streamlink isn't recording anything.
def moveFiles(channel):
    files = []
    files_search = os.listdir(in_progress_directory)
    for file in files_search:
        if os.path.isfile(in_progress_directory + str(file)):
            files.append(file)
    for file in files:
        if channel in str(file):
            in_progress_path = in_progress_directory + file
            save_path = save_directory + file
            subprocess.call(['mv', in_progress_path, save_path])
            if debug:
                print('Moving file %s to saved directory.' % (file))
            logging.info('Moving file %s to saved directory.' % (file))

# Record stream using streamlink.
def recordStream(stream, quality, channel):
    if debug:
        print('Found a stream for channel %s with quality %s.' % (channel, quality))
    logging.debug('Found a stream for channel %s with quality %s.' % (channel, quality))
    url = 'https://twitch.tv/' + channel
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")
    file_name = '[' + channel + '](' + time + ').mp4'
    in_progress_name = in_progress_directory + file_name
    save_name = save_directory + file_name
    subprocess.call(['streamlink',
                    url,
                    quality,
                    '-o',
                    in_progress_name,
                    '--hls-live-restart',
                    '--twitch-disable-ads',
                    '--twitch-disable-hosting'])

# Use the Twitch API to check if channels are live and if so, record them.
def checkStreams(channel, quality):
    try:
        db = pickledb.load('db.json', False)
        streams_iterator = client.get_streams(user_logins=channel)
        for stream in islice(streams_iterator, 0, 500):
            if debug:
                print(str(stream))
            logging.debug(str(stream))
            if stream != None:
                if db.get(channel) == 'true': # If channel is live and the lockfile exists.
                    if debug:
                        print('Channel %s is already recording; skipping channel.' % (channel))
                    logging.info('Channel %s is already recording; skipping channel.' % (channel))
                    sys.exit(0)
                else: # If channel is live and the lockfile does NOT exist.
                    db.set(channel, 'true')
                    if debug:
                        print('Channel %s is live but no lockfile exists; creating lockfile and starting recording.' % (channel))
                    logging.info('Channel %s is live but no lockfile exists; creating lockfile and starting recording.' % (channel))
                    recordStream(stream, quality, channel)
                    moveFiles(channel)
                    sys.exit(0)
            else:
                if os.path.isfile(channel): # If the stream is NOT live and the lockfile exists.
                    db.set(channel, 'false')
                    if debug:
                        print('Lock file for channel %s exists but no stream is recording; removing lock file.' % (channel))
                    logging.info('Lock file for channel %s exists but no stream is recording; removing lock file.' % (channel))
                    moveFiles(channel)
                    sys.exit(0)
                else: #If the stream is NOT live and the lockfile does NOT exist.
                    if debug:
                        print('Channel %s is not live; skipping channel.' % (channel))
                    logging.info('Channel %s is not live; skipping channel.' % (channel))
                    moveFiles(channel)
                    sys.exit(0)
        db.dump()
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        sentry_sdk.capture_exception(e)

# Run the loop.
while run:
    try:
        channel_names_to_check = cleanChannelNames(channel_names)
        for channel in channel_names_to_check:
            if debug:
                print('Checking channel %s for streams!' % (channel))
            logging.info('Checking channel %s for streams!' % (channel))
            t = threading.Thread(target=checkStreams, args=(channel,quality,))
            if debug:
                print('Starting thread for channel %s.' % (channel))
            logging.debug('Starting thread for channel %s.' % (channel))
            t.run()
        time.sleep(sleep_time)
    except KeyboardInterrupt:
        exit()
    #except Exception as e:
    #    sentry_sdk.capture_exception(e)
