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
import sys
from pythonNotify import main as pythonNotify
from os import path

# Sentry.io error tracking. Uncomment if you're worried about this.
import sentry_sdk
sentry_sdk.init("https://00404187dc264687a17c8311c3c2f58c@sentry.io/1420494",
                max_breadcrumbs=50,
                environment='dev',
)

try:
    # Setup logging.
    logging.basicConfig(filename='lars.log', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)

    # General variable setup.
    run = True
    sleep_time = 30
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
    send_pushover_notifications = parser.get('config', 'send_pushover_notifications')
    if send_pushover_notifications == "True":
        send_pushover_notifications = True
        pushover_user_key = parser.get('config', 'pushover_user_key')
        pushover_app_key = parser.get('config', 'pushover_app_key')
    
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
    return False;

# Move in-progress files to saved if streamlink isn't recording anything.
def moveFiles(stream, channel):
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")
    stream_title = stream['title'].strip()
    file_name = '[' + channel + '](' + time + ')<' + stream_title + '>.mp4'
    in_progress_name = in_progress_directory + file_name
    save_name = save_directory + file_name
    subprocess.call(['mv', in_progress_name, save_name])
    if debug:
        print('Moving in progress files to saved directory.')
    logging.info('Moving in progress files to saved directory.')

# Use the Twitch API to check if channels are live and if so, record them.
def checkStreams(channel, quality):
    try:
        if path.isfile(channel):
            if checkIfProcessRunning('streamlink'):
                if debug:
                    print('Channel %s is already recording.' % (channel))
                logging.info('Channel %s is already recording.' % (channel))
                sys.exit()
            else:
                moveFiles(stream, channel)
                subprocess.call(['rm', channel])
                if debug:
                    print('Channel %s is not recording but lock file exists; cleaning up.' % (channel))
                logging.info('Channel %s is not recording but lock file exists; cleaning up.' % (channel))
        else:
            if checkIfProcessRunning('streamlink'):
                subprocess.call(['touch', channel])
                if debug:
                    print('Channel %s is already recording but no lock file exists, creating now!' % (channel))
                logging.info('Channel %s is already recording but no lock file exists, creating now!' % (channel))
                sys.exit()
            else:
                streams_iterator = client.get_streams(user_logins=channel)
                for stream in islice(streams_iterator, 0, 500):
                    if debug:
                        print(str(stream))
                    logging.debug(str(stream))
                    if stream != None:
                        subprocess.call(['touch', channel])
                        if debug:
                            print('Found a stream for channel %s.' % (channel))
                        logging.debug('Found a stream for channel %s.' % (channel))
                        if send_pushover_notifications:
                            pythonNotify.sendPushoverNotification(pushover_app_key, pushover_user_key, 'There is a new stream recording now for the channel: %s!' % (channel), channel + ' is now recording!', 0)
                        url = 'https://twitch.tv/' + channel
                        time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")
                        stream_title = stream['title'].strip()
                        file_name = '[' + channel + '](' + time + ')<' + stream_title + '>.mp4'
                        in_progress_name = in_progress_directory + file_name
                        save_name = save_directory + file_name
                        if debug:
                            print('Starting recording file %s for channel %s.' % (file_name, channel))
                        logging.info('Starting recording file %s for channel %s.' % (file_name, channel))
                        subprocess.call(['streamlink',
                                        url,
                                        quality,
                                        '-o',
                                        in_progress_name,
                                        '--hls-live-restart'])
                        if path.isfile(channel):
                            subprocess.call(['rm',channel])
                    elif stream == None:
                        if debug:
                            print('Stream %s not online.' % (channel))
                        logging.info('Channel %s is not online.' % (channel))
                        pass
                    else:
                        if debug:
                            print('Stream %s is having an error.' % (channel))
                        logging.info('Stream %s is having an error.' % (channel))
                        pass
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
            t.start()
        time.sleep(sleep_time)
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        sentry_sdk.capture_exception(e)
