#!/usr/bin/python3
#
# Documentation
# =============================
#
# This little script to easily send slack notifications.
# Tiger's team webhooks are configured here: https://XXX.slack.com/apps/YYY-incoming-webhooks
#
# Examples:
#   slack_send.py --help
#   slack_send.py -w "test" -m ":tiger: This is my test message" -a "Formated value"
#   slack_send.py -w "alert" -m ":alert: Foreman duplicate hosts found! :alert:" "Second message"  -a "CMD OUT1" "CMD OUT2"
#
# Infos:
#   Author: MrJK
#   Date: 05/2021
#   Status: Stable
#   Version: 1.0
#
# EOFDOC


# Python imports
# =============================

import sys
import os
import requests
import json
import re
import logging
from argparse import ArgumentParser
from pprint import pprint


# Default functions
# =============================

DEFAULT_PROXY_CONFIG = "/etc/profile.d/proxy_env.sh"
DEFAULT_CHANNEL = ""
DEFAULT_USERNAME = "Slack Notifier Webhook"
DEFAULT_EMOJI = ":tiger:"

# Slack WebHooks:
DEFAULT_HOOKS = {
    "info":  "https://hooks.slack.com/services/...",  # #my-slack-chan-info
    "alert": "https://hooks.slack.com/services/...",  # #my-slack-chan-alerts
    "test":  "https://hooks.slack.com/services/...",  # #my-slack-chan-tests
}


# Utils functions
# =============================

def set_logger():
    """Return the default logger"""
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)

    # Create a formatter that creates a single line of json with a comma at the end
    formatter_json = logging.Formatter(( 
        '{"unix_time":%(created)s, "time":"%(asctime)s", "module":"%(name)s", '
        '"line_no":%(lineno)s, "level":"%(levelname)s", "msg":"%(message)s"}'))
    formatter = logging.Formatter(("%(asctime)s - %(levelname)s - %(message)s"))

    # Create a channel for handling the logger and set its format
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # Connect the logger to the channel
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    return logger


def parse():
    """Return command line arguments in a dict"""
    parser = ArgumentParser(description="Post to Slack Team")

    parser.add_argument(
        "--webhook",
        "-w",
        type=str,
        default="test",
        choices=DEFAULT_HOOKS.keys(),
        help="Slack WebHook",
    )
    parser.add_argument(
        "--user", "-u", type=str, default=DEFAULT_USERNAME, help="Slack username"
    )
    parser.add_argument(
        "--icon_emoji", "-e", type=str, default=DEFAULT_EMOJI, help="Slack User emoji"
    )

    parser.add_argument(
        "--message",
        "-m",
        nargs="+",
        default=[],
        help="Messages to send (3000 char max)",
    )
    parser.add_argument(
        "--attachement",
        "-a",
        nargs="+",
        default=[],
        help="Output to send (3000 char max)",
    )

    return parser.parse_args()


def get_proxy(conf):
    """Retrieve Bell proxy settings"""

    if not os.path.isfile(conf):
        logger.warning(f"Missing proxy configuration file: {conf}")
        return None

    # Read shell environment config
    proxy = None
    with open(conf, "rt") as config:
        for line in config:
            match = re.search('BELL_PROXY=(("(?P<p1>.*)")|(?P<p2>.*))', line)
            if match:
                r = match.groupdict()
                proxy = r.get("p1", None) or r.get("p2", None)

    # Return request proxy config
    if not proxy:
        logger.warning(f"Cound not apply proxy configuration: {proxy}")
        return None
    logger.debug(f"Found proxy configuration: {proxy}")
    return {
        "http": proxy,
        "https": proxy,
    }


# Slack functions
# =============================

def build_blocks(messages, attachements):
    """Assemble messages and attachements"""

    blocks = []

    # Build messages
    for message in messages:
        if not message:
            logger.info("Ignoring empty message")
            continue
        message = message[0:2990]
        data = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": str(message),
            },
        }
        blocks.append(data)

    # Build attachments
    for attachement in attachements:
        if not attachement:
            logger.info("Ignoring empty attachement")
            continue
        attachement = "```\n" + attachement[0:2990] + "\n```"
        data = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": str(attachement),
            },
        }
        blocks.append(data)

    return blocks


def slack_payload(channel=None, user=None, icon=None, blocks=None):
    """Build slack payload"""
    # TOFIX: Ultimately, this function should be merged in build_blocks

    payload = {}
    if channel:
        payload["channel"] = channel
    if user:
        payload["username"] = user
    if icon:
        payload["icon_emoji"] = icon
    if blocks:
        payload["blocks"] = blocks
    return payload


def slack_send(webhook, payload, proxies=None):
    """Send payload to slack channel"""

    response = requests.post(
        webhook,
        data=json.dumps(payload),
        proxies=proxies,
        headers={"Content-Type": "application/json"},
    )
    if response.status_code != 200:
        raise ValueError(
            "Request to slack returned an error %s, the response is:\n%s"
            % (response.status_code, response.text)
        )
    else:
        logger.info("Message sent to Slack")
    return response


# Main functions
# =============================

def main():
    """Main command line"""

    # Command  Lines Arguments
    args = parse()

    # Parse proxy data
    proxies = get_proxy(DEFAULT_PROXY_CONFIG)

    # Build blocks
    blocks = build_blocks(args.message, args.attachement)

    # Build slack payload
    payload = slack_payload(user=args.user, icon=args.icon_emoji, blocks=blocks)

    # Send Slack webhook
    slack_send(DEFAULT_HOOKS[args.webhook], payload, proxies=proxies)


if __name__ == "__main__":
    logger = set_logger()
    main()

