#!/usr/bin/env python

import wolframalpha
import config

waclient = wolframalpha.Client(config.wa_token)

def wa_query( query ):
    try:
        waresponse = waclient.query(query)
        waresponse = (next(waresponse.results).text)
    except StopIteration:
        waresponse = "No idea, try something else"
    except Exception as e:
        print(f"wa_query error: {e}")
        waresponse = "No idea, try something else"
    return waresponse
