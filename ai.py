#!/usr/bin/env python

import openai
import config

openai.api_key = config.openai_token

def ai_query( query ):
    try:
        promptstring = 'Shoes is a chatbot that reluctantly answers questions with sarcastic responses:\n You: ' + query
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=promptstring,
            temperature=0.5,
            max_tokens=60,
            top_p=0.3,
            frequency_penalty=0.5,
            presence_penalty=0
        )
        airesponse = (response.choices[0].text[9:])
    except:
        airesponse = "Wuh?"
    return airesponse