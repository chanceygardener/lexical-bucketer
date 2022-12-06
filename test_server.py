#!/usr/bin/env python3
#
import requests
import json

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

bucketTests = ["the tiger from Seigfried and Roy", "Anwar Sadat", "The guy who shot Donald Trump", "the bastards that did it",
               "some people in a van"]


# def getNpModifiers(doc):
#     # Yaaay Syntax!
#     rights = list(sentOf(doc).root.rights)

#     return [" ".join(list(map(lambda t: t.orth_,
#                               rights.subtree)))
#             for i in range(len(rights))]


def get_determiner(doc):
    return list(doc.sents)[0].root.left_edge


def detIdx(doc):
    maybe_det = list(doc.sents)[0].root.left_edge
    if maybe_det.pos_ == 'DET':
        return maybe_det.i


def rootIdx(doc):
    return list(doc.sents)[0].root.i


def removeDet(doc):
    return " ".join([token.orth_ for token in doc if token.i != detIdx(doc)])


USE_HTTPS = False
LOCAL = True
if LOCAL:
    host = "0.0.0.0"
    port = "8080"

else:
    host = "poc-servers.soulmachines.cloud"
    port = "46001"

base_url = f"http{'s' if USE_HTTPS else ''}://{host}:{port}"


print("Testing bucketer")

for val in bucketTests:
    testDat = {
        "input": val,
        "classifier": "creature_is_threatening"
    }
    r = requests.post(f"{base_url}/bucket",
                      data=json.dumps(testDat))
    if r.ok:
        print(r.json())
    else:
        print(f"Failed with code {r.status_code}. {r.reason}")

print("Success\n\nNow testing blender")
r = requests.post(f"{base_url}/blender",
                  data=json.dumps({"text": "what grossed you out?"}))
if r.ok:
    print(r.json())
else:
    print(f"Failed with code {r.status_code}. {r.reason}")


print("\nTesting Blender reset")

r = requests.get(f"{base_url}/blenderReset")
if r.ok:
    print(r.json())
else:
    print(f"Failed with code {r.status_code}. {r.reason}")

print("Testing health check")
r = requests.get(base_url)
if r.ok:
    print(r.text)
else:
    print(f"Failed with code {r.status_code}. {r.reason}")

print("testing lexicalization")

tests = bucketTests + [
    "the person who faked the moon landing",
    "Bob Ross",
    "a Catholic priest",
    "a mailman",
    "a doctor",
    "the doctor from the movie ghost",
    "some fisherman on a dock",
    "confused whales",
    "The executioner on the payroll",
    "Charles Manson's grandson",
    "an out-of-work telephone operator"
]

for t in tests:
    r = requests.post(f"{base_url}/lexicalize",
                      data=json.dumps({
                          "rawText": t
                      }))
    if r.ok:
        print(json.dumps(r.json(), indent=4))
    else:
        print(f"failed with code: {r.status_code}, {r.reason}")

