#!/usr/bin/env python3


from base_choice import generate_categorizer
import argparse as ap
import spacy
from os import getenv
from dotenv import load_dotenv


load_dotenv()

# call generate_categorizer to return
# an instance of a categorizer trained on
# the given buckets

LANGUAGE_MODEL = getenv("SPACY_MODEL")


def load_spacy_model(model=LANGUAGE_MODEL):
    print("Loading spaCy model")
    nlp = spacy.load(model)
    print("complete!")
    return nlp

if __name__ == "__main__":
    nlp = load_spacy_model()
    parser = ap.ArgumentParser(prog="Test Semantic Bucketer")
    parser.add_argument("bucket_path", type=str)
    parser.add_argument("--clean", "-c", action="store_true")
    parser.add_argument("--prompt", "-p", type=str, default="input: ")
    parser.add_argument("--remove-stop", "-s", action="store_true")
    parser.add_argument("--debug", "-d", action="store_true")
    args = parser.parse_args()
    cc = generate_categorizer(args.bucket_path, nlp,
                              debug=args.debug,
                              clean_text=args.clean,
                              no_stop=args.remove_stop)
    prompt = args.prompt + \
        " " if not args.prompt.endswith(" ") else args.prompt
    while True:
        uinput = input(prompt)
        guess = cc(uinput)
        print(f"\n\t{guess}\n")
