#!/usr/bin/env python3

"""An http(s) server for a semantic bucketer.

This server receives:
    /bucket
    POST: data 
    ```json
    {
        "input": "some natural language",
        "classifier": "classifier_name"
    }```
"""

from flask import Flask, request
import json
from base_choice import generate_categorizer
from os import getenv
from os import listdir, getcwd
from os import path
from traceback import print_exc
from dotenv import load_dotenv
from utils import *
from requests import post
from parse_rules import *
import time


load_dotenv()
PORT = int(getenv("PORT", 8080))
HUGGINGFACE_KEY = getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_MODEL = getenv("HUGGINGFACE_MODEL")
HOSTNAME = getenv("HOSTNAME", "0.0.0.0")
MAX_LENGTH = 256
USE_HTTPS = bool(int(getenv("USE_HTTPS", 0)))
bucket_dir = path.join(getcwd(), "buckets")

app = Flask("CleoReasoning")


print(f"Using text generation model: {HUGGINGFACE_MODEL}")
print(f"huggingface_key: {HUGGINGFACE_KEY}")


def queryHfTextGen(text, model=HUGGINGFACE_MODEL, key=HUGGINGFACE_KEY,
                   args={"max_new_tokens": MAX_LENGTH, "wait_for_model": True}):
    response = post(f'https://api-inference.huggingface.co/models/{model}',
                    headers={
                        "Authorization": f"Bearer {key}"
                    }, data=json.dumps({
                        "inputs": text,
                        **args
                    }))
    rdat = json.loads(response.content.decode("utf-8"))
    if isinstance(rdat, list):
        rdat = rdat[0]
    return rdat




classifiers = {
    trim_bucket_fname(b): generate_categorizer(
        path.join(bucket_dir, b), shared_nlp)
    for b in listdir(bucket_dir)
}
print("The following bucketers are available: ")
for b in classifiers.keys():
    print(f"\t{b}")


def log_output(out, summary):
    print(f"\nReturning the following {summary}")
    print(out)
    print("##########################################\n")


@app.route('/', methods=['GET', 'POST'])
def rootReturn():
    return "OK"


@app.route('/analyzeStory')
def get_story_dat():
    intext = json.loads(request.data).get("text")
    if intext is None:
        raise ValueError("No text in request data")
    proc = shared_nlp(intext)



@app.route('/lexicalize', methods=['POST'])
def lexicalize():
    req_dat = json.loads(request.data)
    rawText = req_dat.get("rawText")
    out = get_lexicon_entry(rawText,
                            type_hint=req_dat.get("posHint"))
    log_output(out, f'lexicon entry for {rawText}')
    return json.dumps(out)


@app.route('/bucket', methods=['POST'])
def run_bucketer():
    req_dat = json.loads(request.data)
    bucketer, intext = req_dat["classifier"], req_dat["input"]
    classifier = classifiers.get(bucketer)
    if classifier is None:
        available_keys = '\n\t'.join(classifiers.keys())
        raise ValueError(f"classifier not found: {bucketer}",
                         f"\nAvailable bucketers:\n {available_keys}")
    out = {
        "input": intext,
        "output": classifier(intext),
        "classifier": bucketer,
        **get_lexicon_entry(intext)
    }
    out["entity_type"] = None if not out.get(
        "entity_type") else out.get("entity_type")
    log_output(out, 'bucket analysis')
    return out


@app.route('/textGen', methods=['POST'])
def generate_text():
    req_dat = json.loads(request.data)
    gen_resp = queryHfTextGen(
        req_dat['prompt'])
    if not gen_resp.get("error"):
        cleaned_text = " ".join(list(map(
            lambda t: t.text,
            list(shared_nlp(gen_resp[
                'generated_text']).sents)[:-1])))
        return {'generated_text': cleaned_text}
    else:
        raise Exception(
            f"Text generation failed with {gen_resp['error']}")


if __name__ == "__main__":
    if USE_HTTPS:
        print("Using https...")
        app.run(ssl_context='adhoc', host=HOSTNAME, port=PORT)
    else:
        print("using http..")
        app.run(host=HOSTNAME, port=PORT)
