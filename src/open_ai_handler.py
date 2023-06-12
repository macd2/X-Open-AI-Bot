import random
import time
import unicodedata
from time import sleep

import openai
from dotenv import dotenv_values

from src.communication_handler import logger
from src.helper import callersname
from src.prompt_engineering import build_chat_log
from src.sql_handler import sql_write_ai_params


# chat = openai.Completion()
# image = openai.Image()


def tweak_gpt_outputs(gpt_response):
    keywords = ["respectfully ", "It is important to ", "Possible response:", "I appreciate your response, but ",
                "@_RussellEdwards"]
    for i in keywords:
        if i.lower() in gpt_response.lower():
            logger.info(f"Replaced {i} in response")
            gpt_response = gpt_response.lower().replace(i.lower(), "")
    return gpt_response


def gpt(model, chat_log, temp, n=1, max_tokens=52, presence_penalty=1):
    env = dotenv_values(".env")
    openai.api_key = env["openai_key"]
    completion = openai.ChatCompletion()

    response = completion.create(model=model,
                                 messages=chat_log,
                                 # max_tokens=max_tokens,
                                 temperature=temp,
                                 # between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic
                                 n=n,  # How many completions to generate for each prompt.
                                 # presence_penalty = presence_penalty, # Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
                                 )
    return response.choices[0]['message']['content']


def get_filter(filters, answer):
    for x in filters:
        if x.lower() in answer.lower():
            logger.info(f"Response did not pass filter: {x}")
            return True
    return False

def ask_gpt(prompt, ai_personality, temperature, model, chat_log=None, ability=""):
    # if a chat log is given we use the conversation mode based on the chat log
    logger.info(f"Asking: {model}")

    if chat_log:
        # if we give a chat log we need to set the text of the prompt to the chat log directly
        # ToDo optimize this procedure
        prompt["prompt"] = unicodedata.normalize("NFKD", chat_log[-1]["content"])
    else:
        chat_log = build_chat_log(prompt=unicodedata.normalize("NFKD", prompt["prompt"]), ai_personality=ai_personality)

    answer = None

    # Make sure the answer is according to these rules
    c = 1
    t = 10
    filters = ["I'm sorry,", "sorry", "humans", "human", "As an AI", "i cannot follow", "sorry, I cannot",
               "let's try to", "I'm an AI", "can't physically", "I'm just a program"]
    while not answer or answer == "None":
        logger.info(f"Try: {c} prompt: {prompt}")
        try:
            answer = gpt(model=model, chat_log=chat_log, temp=temperature, n=1, max_tokens=52, presence_penalty=1)
        except Exception as e:
            logger.info(f"{callersname()} : Got Error {e}")
            if "That model is currently" in e:
                sleep_time = random.randrange(5, t)
                logger.info(f"Sleeping for {sleep_time} Seconds")

                time.sleep(sleep_time)
                t += random.randrange(1, 3)


        logger.info(f"{answer}")
        if get_filter(filters=filters, answer=answer):
            logger.info(f"Filter not passed: {answer}")
            answer = None
            sleep(random.randrange(10, 20))
        c += 1


    ai_params = {
        "ability": ability,
        "prompt": prompt["prompt"],
        "response": answer,
        "personality": ai_personality,
        "nuance": prompt["nuance"],
        "mood": prompt["mood"],
        "model": model,
        "temperature": float(temperature),
    }
    sql_write_ai_params(ai_params=ai_params)

    return answer
