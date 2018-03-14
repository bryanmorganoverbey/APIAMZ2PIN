# -*- coding: utf-8 -*-
import urllib


def url_encode(query):
    if isinstance(query, basestring):
        query = urllib.quote_plus(query)
    else:
        query = urllib.urlencode(query)
    query = query.replace('+', '%20')
    return query
