import random
from datetime import datetime, timedelta
from time import sleep
from typing import Tuple

from dotenv import dotenv_values
from duckduckgo_search import DDGS
from newsapi import NewsApiClient
from serpapi import GoogleSearch, serp_api_client_exception

from config import config
from src.communication_handler import logger
from src.helper import get_hash, callersname
from src.pickle_handler import load_pickle, write_pickle

# source https://github.com/deedy5/duckduckgo_search
# Load environment variables from .env file
env = dotenv_values(".env")


# News no API Key
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


# Get News SerpAPI
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


def get_news_api(search_term):
    # params = {
    #     "api_key": env["serpapi"],
    #     "engine": "duckduckgo",
    #     "q": f"{search_term}",
    #     "tbm": "nws",
    #     # "kl": "us-en",
    #     "tbs": "qdr:d",
    #     "num": 100
    # }
    params = {
        "q": f"{search_term}",
        "google_domain": "google.com",
        "api_key": f'{env["serpapi"]}',
        "tbm": "nws",
        "tbs": "qdr:d",
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        if results["error"] == 'Your searches for the month are exhausted. You can upgrade plans on SerpApi.com website.':
            logger.info(results["error"])
            return "API limit reached"
    except serp_api_client_exception as e:
        logger.error(f"Fetching news not successful got: {e}")
        return None
    if results.get('search_metadata').get('status') == 'Success':
        for i in results['news_results']:
            i["body"] = i["snippet"]
            i["url"] = i["link"]
            i["body_hash"] = get_hash(i["body"])
            i["search_term"] = search_term
        return results["news_results"]
    else:
        logger.info(f"Search was not successful status is: {results.get('search_metadata').get('status')}")
        return None


# Get News via News API (https://newsapi.org/)
def write_description_hash(response_):
    if response_["status"] == 'ok':
        if int(response_["totalResults"]) == 0:
            return None
        for i in response_["articles"]:
            i["description_hash"] = get_hash(i["description"])
    return response_


def write_search_term(response_, search_term):
    if response_["status"] == 'ok':
        if int(response_["totalResults"]) == 0:
            return None
        for i in response_["articles"]:
            i["search_term"] = search_term
    return response_


def write_body_text(response_):
    if response_["status"] == 'ok':
        if int(response_["totalResults"]) == 0:
            return None
        for i in response_["articles"]:
            i["body"] = i["title"].split(" -")[0] + ". " + i["description"]
    return response_

def filter_news(response_, filter_words:list):
    if response_["status"] == 'ok':
        if int(response_["totalResults"]) == 0:
            return None

        response_["articles"] = [i for i in response_["articles"] if all(keyword not in i["body"] for keyword in filter_words)]
        return response_


newsapi = NewsApiClient(api_key=env['news_api_key'])
def get_news_news_api(search_term, type_: str):
    if type_ == "top_headlines":
        # /v2/top-headlines
        # To Do refactor so it will always match the search term list
        if search_term in ['Investing', 'management', 'Finance', 'Risk', 'Economy']:
            category = 'business'
        elif search_term in ['Discoveries']:
            category = random.choice([
                                  'science',
                                  'technology'])
        else:
            category = 'business',   # ['business',
                                      #'entertainment',
                                      # 'general',
                                      # 'health',
                                      # 'science',
                                      # 'sports',
                                      # 'technology']
        logger.info(f"Using search term: {search_term} and category: {category}")
        top_headlines = newsapi.get_top_headlines(q=search_term,  # 'bitcoin',
                                                  category=category,
                                                  language='en',
                                                  country='us')
        if top_headlines['totalResults'] == 0:
            return None, None
        try:
            top_headlines = write_description_hash(top_headlines)
            top_headlines = write_search_term(top_headlines, search_term)
            top_headlines = write_body_text(top_headlines)
            top_headlines = filter_news(top_headlines, filter_words=["gay", "woman rights", "LGBT", "Woman rights"])
        except Exception as e:
            logger.error(f"{callersname()} : Got error in getting news: {e}")
            return None, None

        if not top_headlines:
            # In case the filter takes out all news results
            return None, None
        return top_headlines, category

    if type_ == "all_articles":
        # /v2/everything

        last_hour_date_time = datetime.now() - timedelta(days=1)
        yesterday = last_hour_date_time.strftime('%Y-%m-%d')

        all_articles = newsapi.get_everything(q=search_term,  # 'bitcoin',
                                              # sources='bbc-news,the-verge',
                                              # domains='bbc.co.uk,techcrunch.com',
                                              from_param=yesterday,  # '2017-12-01',
                                              # to='2017-12-12',
                                              language='en',
                                              sort_by='relevancy',
                                              page=1)
        if all_articles['totalResults'] == 0:
            return None, None
        try:
            all_articles = write_description_hash(all_articles)
            all_articles = write_search_term(all_articles, search_term)
            all_articles = write_body_text(all_articles)
            all_articles = filter_news(all_articles, filter_words=["gay", "woman rights", "LGBT", "Woman rights"])
        except Exception as e:
            logger.error(f"{callersname()} : Got error in getting news: {e}")
            return None

        return all_articles

    if type_ == "source":
        # /v2/top-headlines/sources
        return newsapi.get_sources()


def returns_news_list_news_api(search_term: str, use_cache: bool, use_api=True, hrs_since_news=8):
    search_result_file_name = "search_results"
    # Try to load the cached version
    if use_cache:
        try:
            search_results = load_pickle(filename=search_result_file_name, max_file_age_hrs=10)
            search_term = search_results[0]["search_term"]
            return search_results, search_term
        except Exception as e:
            logger.info(f"News pickle couldn't be loaded: {e}")

    while True:
        sleep(random.randrange(10, 20))
        if not env["news_api_key"]:
            logger.info("No API key set for Newsapi in the .env file skipping search")
            return None, search_term

        top_headlines, category = get_news_news_api(search_term=search_term, type_="top_headlines")
        all_articles = get_news_news_api(search_term=search_term, type_="all_articles")

        if not top_headlines and not all_articles:
            logger.info(f"Found no news for Search Term: {search_term}")
            search_term = random.choice(config["search_terms"])
            logger.info(f"Try new Search Term: {search_term}")
            continue

        r1 = []
        r2 = []
        if top_headlines:
            r1 = top_headlines["articles"]
        if all_articles:
            r2 = all_articles["articles"]

        search_results = r1 + r2
        search_results = [x for x in search_results if "LGBT" not in x["body"]]
        write_pickle(obj=search_results, filename=search_result_file_name)
        return search_results, search_term


def return_news_list(search_term: str, use_cache: bool, use_api=True, hrs_since_news=8) -> Tuple:
    search_result_file_name = "search_results"

    # Try to load the cached version
    if use_cache:
        try:
            search_results = load_pickle(filename=search_result_file_name, max_file_age_hrs=10)
            search_term = search_results[0]["search_term"]
            return search_results, search_term
        except Exception as e:
            logger.info(f"News pickle couldn't be loaded: {e}")

    while True:
        sleep(random.randrange(10, 20))
        if use_api and env["serpapi"]:
            search_results = get_news_api(search_term=search_term)
            if search_results == "API limit reached":
                return None, search_term
            if search_results:
                search_results = filter_out_old_news_api(news=search_results, hours_since=hrs_since_news)
            if not search_results:
                logger.info(f"Found no news for Search Term: {search_term}")
                search_term = random.choice(config["search_terms"])
                logger.info(f"Try new Search Term: {search_term}")
        else:
            search_results = get_news(search_term=search_term)

        if search_results:
            write_pickle(obj=search_results, filename=search_result_file_name)
            return search_results, search_term
