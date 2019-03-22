# Import dependencies.s
from itertools import islice
from twitch import TwitchHelix
import configparser
import logging
import threading
import subprocess
import datetime
import time
from os import path

# Sentry.io error tracking. Uncomment if you're worried about this.
import sentry_sdk
sentry_sdk.init("https://00404187dc264687a17c8311c3c2f58c@sentry.io/1420494")

try:
    # General variable setup.
    run = True
    sleep_time = 10

    # Setup configparser and get variables from config file.
    parser = configparser.ConfigParser()
    parser.read('config.ini')
    quality = parser.get('config', 'quality')
    client_id_auth = parser.get('auth', 'user_id')
    channel_names = parser.get('config', 'channels').split(', ')
    save_directory = parser.get('config', 'save_directory')
    if not save_directory.endswith('/'):
        save_directory = save_directory + "/"
    in_progress_directory = parser.get('config', 'in_progress_directory')
    if not in_progress_directory.endswith('/'):
        in_progress_directory = in_progress_directory + "/"

    # Setup Twitch API client.
    client = TwitchHelix(client_id=client_id_auth)

    # Setup logging.
    logging.basicConfig(filename='lars.log', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
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

# Use the Twitch API to check if channels are live and if so, record them.
def checkStreams(channel, quality):
    try:
        streams_iterator = client.get_streams(user_logins=channel)
        for stream in islice(streams_iterator, 0, 500):
            if stream != None:
                if path.isfile(channel):
                    current_processes = subprocess.check_output(['ps', '-aux'])
                    if 'streamlink' in current_processes:
                        print('Channel %s is already recording.' % (channel))
                        logging.info('Channel %s is already recording.' % (channel))
                        pass
                    else:
                        subprocess.call(['rm', channel])
                        print('Channel %s is not recording but lock file exists; cleaning up.' % (channel))
                else:
                    subprocess.call(['touch', channel])
                    print('Found a stream for channel %s.' % (channel))
                    logging.debug('Found a stream for channel %s.' % (channel))
                    url = 'https://twitch.tv/' + channel
                    time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")
                    file_name = channel + '_' + time + '.mp4'
                    in_progress_name = in_progress_directory + file_name
                    save_name = save_directory + file_name
                    print('Starting recording file %s for channel %s.' % (file_name, channel))
                    logging.info('Starting recording file %s for channel %s.' % (file_name, channel))
                    subprocess.call(['streamlink',
                                     url,
                                     quality,
                                    '-o',
                                    in_progress_name,
                                    '--default-stream',
                                    '720p,480p',
                                    '--retry-streams',
                                    '10',
                                    '--retry-max',
                                    '10',
                                    '--hls-live-restart'])
                    subprocess.call(['mv', in_progress_name, save_name])
                    subprocess.call(['rm',channel])
            elif stream == None:
                print('Stream %s not online.' % (channel))
                logging.info('Channel %s is not online.' % (channel))
                pass
            else:
                print('Stream %s is encountering errors.' % (channel)) 
                logging.info('Channel %s is encountering errors.' % (channel))
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
            print('Checking channel %s for streams!' % (channel))
            logging.info('Checking channel %s for streams!' % (channel))
            t = threading.Thread(target=checkStreams, args=(channel,quality,))
            print('Starting thread for channel %s.' % (channel))
            logging.debug('Starting thread for channel %s.' % (channel))
            t.start()
        time.sleep(sleep_time)
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        sentry_sdk.capture_exception(e)
