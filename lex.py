#!/usr/bin/env python3

import requests
import argparse as ap
import json

parser = ap.ArgumentParser()
parser.add_argument('raw', type=str)
parser.add_argument('--remote', '-r', action="store_true")


def query_lex(rawText, endpoint):
    r = requests.post(f"{endpoint}/lexicalize", json={
        "rawText": rawText
    })
    if r.ok:
        out = r.json()
    else:
        out = {
            "status": r.status_code,
            "reason": r.reason
        }
    return out


if __name__ == "__main__":
    args = parser.parse_args()
    if args.remote:
        ENDPOINT = "https://poc-servers.soulmachines.cloud:46001"
    else:
        ENDPOINT = "http://localhost:8080"
    print(json.dumps(query_lex(args.raw, ENDPOINT), indent=4))
