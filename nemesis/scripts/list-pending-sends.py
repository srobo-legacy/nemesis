#!/usr/bin/env python

import argparse
import os
import sys

nemesis_root = os.path.dirname(os.path.abspath(__file__)) + "/../"
sys.path.insert(0, nemesis_root)

import config
from sqlitewrapper import PendingSend

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="List pending email sends.",
    )
    parser.add_argument(
        '--limit',
        default=1000,
        type=int,
        help="The maximum number of emails to list (default: %(default)s).",
    )
    parser.add_argument(
        '--max-retries',
        default=5,
        type=int,
        help="Restrict to emails with up to this many retry attempts (default: "
             "%(default)s).",
    )
    args = parser.parse_args()

    for ps in PendingSend.Unsent(
        max_results=args.limit,
        max_retry=args.max_retries + 1,
    ):
        print(ps)
