#!/usr/bin/env python

import openai
import config

openai.api_key = config.openai_token

chatgpt_behaviour = "You are a Discord chatbot named Shoes that reluctantly answers questions with sarcastic and witty responses."

def ai_query( query, prompthistory ):
    try:
        jsonstring = [{"role": "system", "content": chatgpt_behaviour}]
        for prompt in range(0,len(prompthistory)):
            if len(prompthistory[prompt]) == 2:
                jsonstring.append({'role': 'user', 'content': prompthistory[prompt][1]})
            if len(prompthistory[prompt]) > 4:
                jsonstring.append({'role': 'assistant', 'content': prompthistory[prompt][6:]})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=jsonstring
        )
        airesponse = (response.choices[0].message.content)
    except:
        airesponse = "Wuh?"
    return airesponse
