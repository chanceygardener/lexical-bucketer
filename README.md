# Semantic Bucketer

This Repository includes a framework for creating semantic bucketers from mapping files in JSON

## Requirements
This module requires python version 3.6 or higher. A Pipfile is included if you choose to run this code with pipenv, as is a requirements.txt if you choose to install this to your base python environment or use some other virtualenv framework.

## Installation

Install Mac / Linux

Using pipenv
```bash
pipenv install
```
From requirements.txt
```bash
pip3 install -r requirements.txt
```

You will also need to install the spaCY model en_core_web_lg, which can be done with the following command:
```bash
python3 -m spacy download en_core_web_lg --user
```
Note that, while en_core_web_lg is standard, you can use any model that contains word vectors. Small spaCy models (marked by names ending in "_sm"), do not include word vectors, and while they will return similarity values for processed text, the peformance will be greatly reduced, and has not been tested.

## Usage

```python
from base_choice import generate_categorizer

categorizer = generate_categorizer("path/to/buckets.json")

categorizer.classify("some text input")

```
You can also test a bucket file by running:
```bash
python3 test_classifiers.py
```
Which will launch a test console for a bucketer generated from the bucket file at
the path specified by the variable TEST_PATH

## Creating A Bucket File
Categorizers are generated from bucket files, which are simple JSON maps from defined categories to lists of phrases designed to be similar to or conceptually represent the category. The nature of this similarity is up to the user to experiment with. A few tips for making a good bucket file:

* Try to curate a similar number of training phrases for each bucket.
* Avoid phrases where the meaning is highly dependent on function words, e.g., words that serve mostly a grammatical purpose (e.g., if, not, would, etc.) as syntactic relationships are not reliably detected.
* Try to curate bucket sets with minimal, if any, conceptual overlap, even if the overlap is in another sense, or on another level of abstraction. For example, individual nations generally have a very high similarity to one another as they frequently appear in similar contexts, and would therefore not serve as good buckets or distinguishing training data.

### Bucket File Format

```js
     {
       "bucket1": [
           "similar phrase to bucket 1",
           "something else like bucket 1",
           ...
       ],
       "bucket2": [
            ...  
        ]
     }
```
