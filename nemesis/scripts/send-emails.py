#!/usr/bin/env python

import argparse
import os
import sys

nemesis_root = os.path.dirname(os.path.abspath(__file__)) + "/../"
sys.path.insert(0, nemesis_root)

import config
import helpers

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
        Attempt to send pending emails. Each pending email (up to a limit) will
        be considered once per invocation, up to ``--max-retries'' number of
        times. Older emails will be considered before newer emails.
        """,
    )
    parser.add_argument(
        '--limit',
        default=50,
        help="The maximum number of emails to send (default: %(default)s).",
    )
    parser.add_argument(
        '--max-retries',
        default=5,
        help="The maximum number of retries to allow before considering an email"
             " abandoned (default: %(default)s).",
    )
    args = parser.parse_args()

    config.configure_logging()
    helpers.send_emails(limit=args.limit, max_retry=args.max_retries)
