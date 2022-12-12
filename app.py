import falcon
import spacy
import argparse
import pandas as pd
import numpy as np

from spacy.matcher import Matcher
from spaczz.matcher import FuzzyMatcher
from sklearn import metrics

import pickle
import json
import logging


logging_format = "[%(asctime)s] %(process)d-%(levelname)s "
logging_format += "%(module)s::%(funcName)s():l%(lineno)d: "
logging_format += "%(message)s"

logging.basicConfig(
    format=logging_format,
    level=logging.DEBUG
)
log = logging.getLogger()

TERM_FILE = './data/terms.txt'
TYPO_FILE = './data/typos.txt'

nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)
fuzzy = FuzzyMatcher(nlp.vocab)


def convert_to_pattern(term):
    print(term)
    out = list()
    for t in term:
        if t.pos_ == 'PUNCT':
            out.append({"IS_PUNCT": True})
        else:
            out.append({"LOWER": t.text.lower()})
    print(out)
    return out


def process_terms(term_file, typos_file):
    variations = [l.strip() for l in open(term_file, 'r').readlines() if l.strip() != '']
    misspellings = [l.strip() for l in open(typos_file, 'r').readlines() if l.strip() != '']

    # get spacy patterns for all terms in the list of variations
    patterns = [convert_to_pattern(nlp(x)) for x in variations]
    patterns_misspellings = [convert_to_pattern(nlp(y)) for y in misspellings]

    return patterns + patterns_misspellings, variations


def match(text):
    doc = nlp(text)
    matches = matcher(doc)

    log.info('##text-classify## INFO: calling matcher')

    result = 0
    output = None
    if matches:
        result = 1
        t = 'exact'
        for _match_id, start, end in matches:
            span = doc[start:end]
            pattern_id = nlp.vocab.strings[_match_id]
            print("ID", id, "MATCH", pattern_id, start, end, span.text)
            output = span.text
    else:
        matches = fuzzy(doc)
        t = 'fuzzy'
        if len(matches) > 0:
            result = 1
            f = list()
            for _match_id, start, end, ratio, in matches:
                # print("ID", id, "FUZZY", "|"+_match_id+"|", doc[start:end], ratio)
                span = doc[start:end]
                f.append(': '.join([str(_match_id), span.text, str(ratio)]))
            output = '; '.join(f)

    matched = result
    match_type = t

    log.info('##text-classify## INFO: returned match result')

    log.info('##text-classify## INFO: matched span is %s', output)

    return output, matched, match_type


rules, terms = process_terms(TERM_FILE, TYPO_FILE)
matcher.add('ALL', rules, greedy="LONGEST")
for k in terms:
    fuzzy.add(k, [nlp(k)], kwargs=[{"ignore_case": False}])


class Text:
    def __init__(self):
        pass

    @staticmethod
    def on_post(request, response):
        target_key = 'text'
        result = dict()
        result.update({'success': 0})

        log.info('##text-classify## INFO: Received request in %s format with length %s',
                 request.content_type, request.content_length)

        if request.content_length and request.content_type in ['application/json', 'str', 'json']:
            try:
                req_data = json.load(request.stream)
                log.info('##text-classify## INFO: Received request data: %s', req_data)
            except ValueError:
                # falcon is not good at customizing error messages for output so this is a work around
                message = '##text-classify## ERROR RAISED: Malformed JSON'
                log.error(message)
                response.status = falcon.HTTP_400
                response.media = {'success': 0, 'message': message}

                return

            if isinstance(req_data, dict):
                if target_key in req_data:
                    query = req_data[target_key]

                    # log.info('##text-classify## INFO: classifying received query: %s', ';'.join(labels))
                    out, matched, match_type = match(query)
                    log.info('##text-classify## INFO: query classified: %s', out)
                    result = dict()

                    # output = list(zip(out, [str(float("{0:.2f}".format(s))) for s in scores]))
                    # output.sort(key=operator.itemgetter(1))
                    result.update({'match': matched})
                    result.update({'out': out})
                    result.update({'type': match_type})
                    result.update({'success': 1})
                else:
                    out = -1
                    message = '##text-classify## WARNING: The target_key (' + str(
                        target_key) + ') was not found in the JSON string.'
                    result.update({'message': message})
                    log.warning(message)
                    response.status = falcon.HTTP_400
                    result.update({'success': int(out)})
            else:
                message = '##text-classify## WARNING: Cannot read JSON.'
                log.warning(message)
                response.status = falcon.HTTP_400
                response.media = {'success': 0, 'message': message}
        else:
            message = '##text-classify## WARNING: Content length is 0, or format is non-json.'
            log.warning(message)
            response.status = falcon.HTTP_400
            result.update({'message': message})

        log.info('##text-classify## INFO: ' + '; '.join(['%s: %s' % (k, v) for (k, v) in result.items()]))
        response.media = result


class Health:

    def __init__(self):
        pass

    @staticmethod
    def on_get(_, response):
        result = {"hello": "world"}
        response.media = result


api = falcon.API()
api.add_route('/', Text())
api.add_route('/health', Health())
