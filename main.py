# Import dependencies.s
from itertools import islice
from twitch import TwitchHelix
import configparser
import logging
import threading
import subprocess
import datetime
import time

# Sentry.io error tracking. Uncomment if you're worried about this.
import sentry_sdk
sentry_sdk.init("https://89abf7559da84797b547a1e73c2619a9@sentry.io/1379532")

try:
    # General variable setup.
    run = True
    sleep_time = 120

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
    print("Exiting!")
    exit()

# Clean up channel names.
def cleanChannelNames(channel_names):
    try:
        channels_to_check = []
        for channel in channel_names:
            channel_name = channel.replace("'", "")
            channels_to_check.append(channel_name)
        return channels_to_check
    except KeyboardInterrupt:
        print("Exiting!")
        exit()

# Use the Twitch API to check if channels are live and if so, record them.
def checkStreams(channel, quality):
    try:
        streams_iterator = client.get_streams(user_logins=channel)
        for stream in islice(streams_iterator, 0, 500):
            if stream != None:
                logging.debug('Found a stream for channel %s.' % (channel))
                url = 'https://twitch.tv/' + channel
                time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")
                file_name = channel + '_' + time + '.mp4'
                in_progress_name = in_progress_directory + file_name
                save_name = save_directory + file_name
                logging.info('Starting recording file %s for channel %s.' % (file_name, channel))
                subprocess.call(['streamlink', url, quality, '-o', in_progress_name])
                subprocess.call(['mv', in_progress_name, save_name])
    except KeyboardInterrupt:
        print("Exiting!")
        exit()

# Run the loop.
while run:
    try:
        channel_names_to_check = cleanChannelNames(channel_names)
        for channel in channel_names_to_check:
            logging.info('Checking channel %s for streams!' % (channel))
            t = threading.Thread(target=checkStreams, args=(channel,quality,))
            logging.debug('Starting thread for channel %s.' % (channel))
            t.start()
        time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("Exiting!")
        exit()
