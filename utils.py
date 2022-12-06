import json
import re
from pluralizer.pluralizer import *
from dotenv import load_dotenv
from os import getenv
import spacy
import lemminflect


load_dotenv()
LANGUAGE_MODEL = getenv("SPACY_MODEL")

plur = Pluralizer()

vowel_irregular_pat = re.compile(
    r'^((eu|u[ntb]i|use|ewe|unanim|utah).*|one|usage)$', re.IGNORECASE)

hyphen_pat = re.compile(r'\s-\s')


def read_json(p):
    with open(p) as jfile:
        dat = json.loads(jfile.read())
    return dat


def sentOf(doc):
    return list(doc.sents)[0]


def getRelativeClause(doc):
    return " ".join(list(map(lambda t: t.orth_,
                             list(sentOf(doc).root.rights)[0].subtree)))


def textFromDoc(span):
    return " ".join(list(map(lambda t: t.orth_,
                             span.subtree)))


def classifyNpModifiers(doc):
    out = {
        "RC": [],
        "PP": [],
        "ERROR": None
    }
    try:
        rights = list(sentOf(doc).root.rights)
        for i in range(len(rights)):
            span = spanFromSubTree(doc, rights[i])
            ctext = textFromDoc(span)
            c = span[0].left_edge.tag_
            if c.startswith('W'):
                # assume relative clause
                out["RC"].append(ctext)
            elif c == 'IN':
                out["PP"].append(ctext)
            else:
                print(f"Unrecognized complementizer and clause: c: {c}\n\ttext: {ctext}")
    except Exception as e:
        out["ERROR"] = str(e)
    return out


def trim_bucket_fname(name):
    out = name.removesuffix(".json")
    return out.removesuffix(".bucket")


def get_upstairs_poss_marker(npDoc):
    root = rootOf(npDoc)
    maybePosMark = root.left_edge.head.right_edge
    if maybePosMark.dep_ == 'case':
        return maybePosMark
    # there is an edge case here
    # when the possessor NP is something
    # the model reads the possessive
    # case marker "'s" as a contracted
    # form of "is", i.e., VBZ tag
    # In such constructions, the following
    # traversal sequence locates the
    # genitive marker
    maybePosMark = root.left_edge.right_edge
    if maybePosMark.dep_ == 'case':
        return maybePosMark


def detIdx(doc):
    maybe_det = list(doc.sents)[0].root.left_edge
    if maybe_det.pos_ == 'DET':
        return maybe_det.i


def rootIdx(doc):
    return list(doc.sents)[0].root.i


def rootOf(doc):
    return doc[rootIdx(doc)]


def numberOf(test, return_idx=False):
    '''Get any numeric modifiers on a
    noun phrase

    [description]

    Arguments:
        test {[type]} -- [description]

    Keyword Arguments:
        return_idx {bool} -- [description] (default: {False})

    Returns:
        [type] -- [description]
    '''
    out = []
    for dep in rootOf(test).lefts:
        if dep.dep_ == 'nummod':
            out.append(dep)
    if return_idx:
        return list(map(lambda t: t.i, out))
    return " ".join(map(lambda t: t.orth_, out))


def removeDet(np, remove_nummod=True):
    exclude_idx = [detIdx(np)]
    if remove_nummod:
        exclude_idx += numberOf(np, return_idx=True)
    upstairs_pos = get_upstairs_poss_marker(np)
    if upstairs_pos is not None:
        exclude_idx += getNpPossessor(
            np, return_idx=True, include_genitive_marker=True)
        out = " ".join([
            v.orth_ for v in np if v.i not in exclude_idx  # != detIdx(np)
        ])
    else:
        out = remove_possessive_whitespace(
            " ".join([token.orth_ for token in np
                      if token.i not in exclude_idx and token.dep_]))
    return out.strip()


def spanFromSubTree(doc, right):
    return doc[right.i: list(right.subtree)[-1].i + 1]


# like calling token.lefts
    # But it includes all tokens
    # that are right descendants
    # from each of the lefts.
    # If each left dep has
    # no right deps, this is
    # equivalent to calling
    # lefts on the token

def recurseLeftDeps(tok):
    out = []
    for depTok in tok.lefts:
        out.append(depTok)
        rights = right_desc(depTok)
        out += rights
    return out


def right_desc(tok):
    rout = []
    for r in tok.rights:
        # print(f"r = {r}")
        rout.append(r)
        if r.rights:
            #rout += [right_desc(t) for t in r.rights]
            for t in r.rights:
                rout.append(t)
                rec_rights = right_desc(t)
                # print(f"token: {t}\nrecursive rights: {rec_rights}")
                if rec_rights:
                    rout += rec_rights
    return rout


def getNpPossessor(doc, return_idx=False, include_genitive_marker=False):
    root = rootOf(doc)  # doc[rootIdx(doc)]
    tokenList = []
    if root.left_edge.head.dep_ == 'poss':
        # tokenList = recurseLeftDeps(root.left_edge.head) + [root.left_edge.head]
        tokenList += list(doc[root.left_edge.i:root.left_edge.head.right_edge.i + 1])
    # else:
    #     tokenList = list(doc[root.left_edge.i:root.left_edge.head.right_edge.i + 1])
    if include_genitive_marker:
        maybeGenitiveMarkerToken = get_upstairs_poss_marker(doc)
        if maybeGenitiveMarkerToken is not None:
            tokenList.append(maybeGenitiveMarkerToken)
    if return_idx:
        out = list(map(lambda t: t.i, tokenList))
    else:
        out = " ".join(map(
            lambda t: t.orth_,
            tokenList))
    return out

# TODO: add plugin capabilities to this function
# or perhaps a decorator, exclude_determiners is... janky


def transform_root_token(doc, transform,
                         transform_token=True, exclude_determiners=False):
    # transform_token, if true runs transform function on token
    special_det_idx = []
    out = ""
    root_idx = rootIdx(doc)
    if exclude_determiners:
        det_idx = detIdx(doc)
        special_det_idx += getNpPossessor(doc,
                                          return_idx=True,
                                          include_genitive_marker=True)
        special_det_idx.append(det_idx)
    print(special_det_idx)
    for idx, token in enumerate(doc):
        if idx == root_idx:
            to_transform = token if transform_token else token.orth_
            out += f"{transform(to_transform)} "
        elif idx in special_det_idx or token.tag_ == 'POS':
            continue
        else:
            out += f"{token.orth_} "
    
    return remove_possessive_whitespace(out)


def complex_lemmatize(vpDoc):
    return transform_root_token(vpDoc, lambda tok: tok._.lemma())


def remove_possessive_whitespace(ostring):
    return re.sub(r"(\w+) ('s)", r"\1\2", ostring.strip())


def complex_singularize(doc):
    return transform_root_token(doc, plur.singular,
                                transform_token=False, exclude_determiners=True)


def complex_pluralize(doc):
    return transform_root_token(doc, plur.pluralize,
                                transform_token=False, exclude_determiners=True)


def format_text(outStruct):
    for key in [
        "singular", "plural",
        "singular_short", "plural_short",
        "raw_noun", "genitive_definite_determiner",
        "number_mod"
    ]:
        if outStruct.get(key):
            outStruct[key] = hyphen_pat.sub('-',
                                            outStruct[key])
            outStruct[key] = remove_possessive_whitespace(
                outStruct[key])


def lemmatize(doc, root_idx):
    out = ""
    for idx, token in enumerate(doc):
        if idx == root_idx:
            out += f"{token.lemma_} "
        else:
            out += f"{token.orth_} "
    return out.strip(), doc[root_idx]


def check_begins_with_vowel(word):
    print(f"Running check_begins_with_vowel on: '{word}'")
    return (word[0].lower() in "aeiou" and vowel_irregular_pat.match(word) is None)


def handle_genitive_info(npDoc, out):
    populated = False
    dtx = detIdx(npDoc)
    root = npDoc[rootIdx(npDoc)]
    if dtx is not None:
        if npDoc[dtx].dep_ == 'poss':
            out["genitive_definite_determiner"] = npDoc[dtx].orth_
            populated = True
        else:
            out["genitive_definite_determiner"] = None
    # If we have a noun phrase acting as a possessive
    # determiner
    elif get_upstairs_poss_marker(npDoc) is not None:
        populated = True
        out["genitive_definite_determiner"] = getNpPossessor(npDoc)
    if not populated:
        out["genitive_definite_determiner"] = None
    return out


def get_raw_noun(proc):
    return remove_possessive_whitespace(" ".join([
        v.orth_ for v in proc if v.i not in getNpPossessor(
            proc, return_idx=True) and v.dep_ != 'case'
    ]))


def requires_definite_determiner(npDoc):
    spacyRequiresDefDet = (rootOf(npDoc).ent_type_ not in (
        "PERSON", "GPE", "LOC", "ORG"))
    return spacyRequiresDefDet


def load_spacy_model(model=LANGUAGE_MODEL):
    print(f"Loading spaCy model: {LANGUAGE_MODEL}")
    nlp = spacy.load(model)
    print("complete!")
    return nlp
