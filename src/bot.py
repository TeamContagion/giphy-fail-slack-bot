import os
import time
from slackclient import SlackClient
import random

from config import BOT_USER_ID, SLACK_TOKEN, FAIL_MESSAGES, FAIL_IMAGES, FAIL_REGEX, SUCKS_MESSAGES, SUCKS_REGEX
import re


# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_TOKEN)

CHANNEL_USER_HAS_GIPHY = {}


def handle_command(command, channel, user):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = None

    if command.startswith("/giphy"):
        CHANNEL_USER_HAS_GIPHY[(channel, user)] = True
    elif (channel, user) in CHANNEL_USER_HAS_GIPHY and CHANNEL_USER_HAS_GIPHY[(channel, user)]:
        if FAIL_REGEX.search(command):
            response = make_fail(FAIL_MESSAGES, FAIL_IMAGES)
        CHANNEL_USER_HAS_GIPHY[(channel, user)] = False
    elif "giphy" in command and SUCKS_REGEX.search(command):
        response = make_fail(SUCKS_MESSAGES, FAIL_IMAGES)
    else:
        CHANNEL_USER_HAS_GIPHY[(channel, user)] = False

    if response:
        slack_client.api_call("chat.postMessage", channel=channel,
                              text=response, as_user=True)


def make_fail(messages, images):
    response = random.choice(messages)
    if "%s" in response:
        response = response % random.choice(images)
    return response


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and output['user'] != BOT_USER_ID:
                # return text after the @ mention, whitespace removed
                return output['text'].lower(), \
                       output['channel'], \
                       output['user']
    return None, None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
        exit(1)