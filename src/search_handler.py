from src.logger_handler import setup_logger
import random
from time import sleep

from dotenv import dotenv_values
from duckduckgo_search import DDGS
from serpapi import GoogleSearch

from config import config
from src.helper import get_hash
from src.pickle_handler import load_pickle, write_pickle

logger = setup_logger()

# source https://github.com/deedy5/duckduckgo_search

def get_news(search_term="finance"):
    _ = []
    with DDGS() as ddgs:
        ddgs_news_gen = ddgs.news(
            search_term,
            region="wt-wt",
            safesearch="Off",
            timelimit="d",
        )
        for v in ddgs_news_gen:
            v["search_term"] = search_term
            v["body_hash"] = get_hash(v["body"])
            _.append(v)
    return _


def get_news_api(search_term):
    env = dotenv_values(".env")
    params = {
        "api_key": env["serpapi"],
        "engine": "duckduckgo",
        "q": f"{search_term}",
        "tbm": "nws",
        # "kl": "us-en",
        "tbs": "qdr:d",
        "num": 100
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        for i in results['news_results']:
            i["body"] = i["snippet"]
            i["url"] = i["link"]
            i["body_hash"] = get_hash(i["body"])
            i["search_term"] = search_term
    except Exception as e:
        logger.info(f"Fetching news not successful got: {e}")
        return None
    return results["news_results"]


def filter_out_old_news_api(news: list, hours_since: int):
    temp_list = []
    for x in news:
        num = x["date"].split(" ")
        if num[1] == "minutes":
            temp_list.append(x)
            continue
        if int(num[0]) <= hours_since and num[1] != "hours":
            temp_list.append(x)
    return temp_list


def return_news_list(search_term, use_cache, use_api=True, hrs_since_news=8):
    env = dotenv_values(".env")
    # ToDo Automate the use_api by checking of a value for the api_ was provided in the .env file
    search_result_file_name = "search_results"

    search_results = None
    if use_cache:
        try:
            search_results = load_pickle(filename=search_result_file_name, max_file_age_hrs=10)
            search_term = search_results[0]["search_term"]
            if search_results:
                return search_results, search_term
        except Exception as e:
            logger.info(f"News Not fetched got: {e}")

    # if no news found, or they are older than specified than get new set of news
    while not search_results:
        sleep(random.randrange(10, 20))
        if use_api and env["serpapi"]:
            search_results = get_news_api(search_term=search_term)
            if search_results:
                search_results = filter_out_old_news_api(news=search_results, hours_since=hrs_since_news)
            if not search_results:
                logger.info(f"Found no news for Search Term: {search_term}")
                search_term = random.choice(config["search_terms"])
                logger.info(f"Try new Search Term: {search_term}")
        else:
            search_results = get_news(search_term=search_term)

    # Cache the results to a file
    write_pickle(obj=search_results, filename=search_result_file_name)

    return search_results, search_term
