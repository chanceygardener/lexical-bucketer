from utils import *
import sys

shared_nlp = load_spacy_model()


def update_with_np_vowel_det_info(lexEntry, doc, root):
    lexEntry.update({"requires_definite_determiner": requires_definite_determiner(doc),
                     "begins_with_vowel_sound_short": check_begins_with_vowel(root.orth_),
                     "begins_with_vowel_sound_long": check_begins_with_vowel(
        removeDet(doc))})


def handle_recognized_noun(npDoc, out):
    root = rootOf(npDoc)
    out["np_modifiers"] = classifyNpModifiers(npDoc)
    out["raw_noun"] = get_raw_noun(npDoc)
    update_with_np_vowel_det_info(out, npDoc, root)
    try:
        out = handle_genitive_info(npDoc, out)
    except Exception as e:
        out["genitive_definite_determiner"] = None
        print(f"GENITIVE INFO FAILED WITH : {e}")
    morph_tags = root.morph.to_json()
    et = root.ent_type_
    number_mod = numberOf(npDoc)
    out["number_mod"] = number_mod
    out["has_number_mod"] = bool(number_mod)
    if "Number=Sing" in morph_tags and et != "PERSON":
        out["singular"] = removeDet(npDoc)
        out["singular_short"] = root.orth_
        out["plural"] = complex_pluralize(npDoc)
        out["plural_short"] = plur.pluralize(root.orth_)
    elif "Number=Plur" in morph_tags and et != "PERSON":
        out["singular"] = complex_singularize(npDoc)
        out["plural"] = removeDet(npDoc)
        out["singular_short"] = plur.singular(root.orth_)
        out["plural_short"] = root.orth_
    else:
        out["singular"] = npDoc.text
        out["plural"] = npDoc.text


def handle_noun_typehint(npDoc, out):
    isPlural = plur.isPlural(npDoc.text)
    root = rootOf(npDoc)
    out["has_number_mod"] = False
    out["number_mod"] = ""
    if isPlural:
        updates = {
            "singular": complex_pluralize(npDoc),
            "plural": removeDet(npDoc),
            "singular_short": plur.singular(root.orth_),
            "plural_short": root.orth_,
            "requires_definite_determiner": requires_definite_determiner(npDoc),
            "begins_with_vowel_sound_short": check_begins_with_vowel(root.orth_),
            "begins_with_vowel_sound_long": check_begins_with_vowel(
                removeDet(npDoc))
        }

    else:
        updates = {
            "singular": removeDet(npDoc),
            "plural": complex_pluralize(npDoc),
            "singular_short": root.orth_,
            "plural_short": plur.pluralize(root.orth_),
            "requires_definite_determiner": requires_definite_determiner(npDoc),
            "begins_with_vowel_sound_short": check_begins_with_vowel(root.orth_),
            "begins_with_vowel_sound_long": check_begins_with_vowel(
                removeDet(npDoc))
        }
    out.update(updates)


def handle_recognized_verb(vpDoc, out):
    lexTagToPennTag = {
        "past_participle": "VBN",
        "past_tense": "VBD",
        "progressive": "VBG",
        "present_third_sing": "VBZ",
        "present": "VBP"
    }
    out["inf"] = complex_lemmatize(vpDoc)
    for lex_tag, penn_tag in lexTagToPennTag.items():
        out[lex_tag] = transform_root_token(
            vpDoc, lambda token: token._.inflect(penn_tag),
            transform_token=True,
            exclude_determiners=False)


def get_lexicon_entry(text, type_hint=None):
    try:
        proc = shared_nlp(text)
        root = list(proc.sents)[0].root
        et = root.ent_type_
        out = {
            "text": text,
            "entity_type": et if et else None,
            "pos": root.pos_ if type_hint is None else type_hint,
            "root_word": root._.lemma(),
            "lex_status": "SUCCESS"
        }
        print(f"Root of raw text parsed as: '{root.orth_}' POS tag: '{root.pos_}'")
        if root.pos_ in ("NOUN", "PROPN"):
            handle_recognized_noun(proc, out)
        elif type_hint == "NOUN":
            handle_noun_typehint(proc, out)
        elif root.pos_ in ("VERB", "AUX"):
            handle_recognized_verb(proc, out)
        format_text(out)
        return out
    except Exception as e:
        print(f"Lexicalization for '{text}' failed with {e}")
        return {
            "text": text,
            "lex_status": "FAILED",
            "traceback": sys.exc_info()
        }


