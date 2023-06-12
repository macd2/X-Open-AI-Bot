import random
import time
import unicodedata
from time import sleep

import openai
from dotenv import dotenv_values

from src.communication_handler import logger
from src.helper import callersname, get_content_between_markers
from src.prompt_engineering import build_chat_log
from src.sql_handler import sql_write_ai_params


# chat = openai.Completion()
# image = openai.Image()


def clean_model_output(gpt_response):
    keywords = ["respectfully ", "It is important to ", "Possible response:", "I appreciate your response, but ",
                "@_RussellEdwards", "I have to respectfully disagree with the text between the * signs."]
    for i in keywords:
        if i.lower() in gpt_response.lower():
            logger.info(f"Replaced: {i}")
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

#ToDo filtere seperate the hastgas and the text if the filtered word is only in the hastags than replace the hashtag for example #Humanintereaction
def model_not_comply_filter(answer):
    if "I'm sorry" in answer and "AI" in answer and "I cannot".lower() in answer.lower():
        logger.info("Model don't want to comply filter activated: I'm sorry, AI and I cannot in response")
        return True
    else:
        return False


def general_response_filter(filters, answer):
    for x in filters:
        if x.lower() in answer.lower():
            logger.info(f"General Repose filter activate on: {x}")
            return True
    return False

def ask_gpt(prompt="", ai_personality="", temperature=0.8, model="gpt-3.5-turbo", chat_log=None, params=None, ability=""):
    # if a chat log is given we use the conversation mode based on the chat log
    logger.info(f"Asking: {model}")
    build_chat_log_ = False

    if not chat_log:
        build_chat_log_ = True
        chat_log = build_chat_log(prompt=prompt["prompt"], ai_personality=ai_personality)

    answer = None

    # Make sure the answer is according to these rules
    c = 1
    t = 10
    f_count = 1

    filters = ["humans", "human", "As an AI", "i cannot follow", "sorry, I cannot",
               "let's try to", "I'm an AI", "can't physically", "I'm just a program","with the text between",
               "my programming","comply with those rules","as an AI language model", "inclusivity", "harmful language"]

    logger.info(f"Prompt: {prompt if prompt else chat_log}")
    filter_ = "passed"
    while not answer or answer == "None":
        logger.info(f"GPT TRY: {c}")
        try:
            answer = gpt(model=model, chat_log=chat_log, temp=temperature, n=1, max_tokens=52, presence_penalty=1)
        except openai.error.RateLimitError as e:
            logger.info(f"{callersname()} : Got Error {e}")
            sleep_time = random.randrange(5, t)
            logger.info(f"Sleeping for {sleep_time} Seconds")

            time.sleep(sleep_time)
            t += random.randrange(1, 3)
            c += 1
            continue
        except Exception as e:
            logger.error(f"{callersname()} : Got Error: {e}")
            time.sleep(5)
            continue

        logger.info(f"Model Response: {answer}")
        if general_response_filter(filters=filters, answer=answer) or model_not_comply_filter(answer=answer):
            f_count += 1
            c += 1
            if f_count == 4:
                logger.info(f"Did Not pass filter for {f_count} times skipp answer")
                filter_ = "not_passed"
                break
            answer = None
            sleep(random.randrange(3, 10))

    if build_chat_log_:
        ai_params = {
            "ability": ability,
            "question":get_content_between_markers(text=prompt["prompt"], start_marker="*", end_marker="*") if prompt["prompt"] else None,
            "prompt": prompt["prompt"],
            "response": answer,
            "personality": ai_personality,
            "nuance": prompt["nuance"],
            "mood": prompt["mood"],
            "model": model,
            "temperature": float(temperature),
            "filter": filter_
        }
    else:
        ai_params = {
            "ability": ability,
            "question": chat_log[-1]["content"],
            "response": answer,
            "personality": ai_personality,
            "nuance": params["nuance"],
            "mood": params["mood"],
            "rules": params["rules"],
            "model": model,
            "temperature": float(temperature),
            "filter": filter_
        }
    sql_write_ai_params(ai_params=ai_params)
    if filter_ == "not_passed":
        answer = "NOT PASSED"

    return answer
