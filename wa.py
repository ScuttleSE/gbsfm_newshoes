#!/usr/bin/env python

import wolframalpha
import config

waclient = wolframalpha.Client(config.wa_token)

def wa_query( query ):
    try:
        waresponse = waclient.query(query)
        waresponse = (next(waresponse.results).text)
    except:
        waresponse = "No idea, try something else"
    return waresponse
