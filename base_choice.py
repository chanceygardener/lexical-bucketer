#!/usr/bin/env python3

import json
from statistics import mean
from spacy.tokenizer import Tokenizer


def read_json(fname):
    with open(fname) as dfile:
        rawdat = dfile.read()
    try:
        dat = json.loads(rawdat)
    except json.decoder.JSONDecodeError as e:
        print(rawdat, "\n")
        raise ValueError(
            f"Invalid JSON at {fname}\nerror message: {e}")
    return dat


def process(nlp, text, remove_stop=False,
            clean=False):
    if remove_stop:
        tokenizer = Tokenizer(nlp.vocab)
        to_proc = " ".join(filter(
            lambda tok: tok not in nlp.Defaults.stop_words,
            tokenizer(text)))
    else:
        to_proc = text
    proc = nlp(to_proc)
    if clean:
        proc = nlp(
            " ".join(map(
                lambda tok: tok.lemma_,
                filter(lambda t: bool(t.ent_type),
                       proc))))
    return proc


class BucketSet:

    def __init__(self, filepath):
        dat = read_json(filepath)
        for bucket, training_dat in dat.items():
            setattr(self, f"class_{bucket}",
                    training_dat)

    def classes(self, spacy_model, remove_stop=False, clean=False):
        return {c: list(map(lambda k: process(spacy_model, k),
                            self.__dict__[c]))
                for c in self.__dict__
                if c.startswith(
            "class_")}


class BaseCategorizer:

    schema = None
    dbg = False
    remove_stop = False
    clean = False

    def __init__(self, nlp):
        assert self.schema is not None, "Base class cannot initialize directly"
        self.nlp = nlp
        self.buckets = BucketSet(
            self.schema).classes(
            self.nlp,
            remove_stop=self.remove_stop, clean=self.clean)

    def _bucket_compare(self, bucket, text):
        '''return the mean of the cosine similarities
        between the text and each training phrase in
        the bucket

        [description]

        Arguments:
            bucket {str} -- the name of the bucket
            text {spacy.tokens.doc.Doc} -- spacy processed text
        '''
        assert bucket in self.buckets, f"Unrecognized Bucket: {bucket}"
        return mean(map(lambda ph: ph.similarity(text),
                        self.buckets[bucket]))
        

    def __call__(self, text, confidence_threshold=0):
        scores = list(map(lambda k: (k, self._bucket_compare(
            k, self.nlp(text))), self.buckets))
        scores = sorted(scores, key=lambda s: s[1])
        if self.dbg:
            for bucket, score in scores:
                print(f"{bucket}: {score}")
        return scores[-1][0]


def generate_categorizer(fpath, nlp, debug=False,
                         no_stop=False, clean_text=False,
                         confidence_threshold=0):
    class Categorizer(BaseCategorizer):
        schema = fpath
        dbg = debug
        remove_stop = no_stop
        clean = clean_text
        min_confidence = confidence_threshold

    return Categorizer(nlp)
