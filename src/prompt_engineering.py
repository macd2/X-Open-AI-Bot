import re

from src.helper import clean_links
from config import config


def build_twitter_prompt(mood, question, nuance):
    prompt = " ".join([f"respond with a maximum of 275 characters to the text between the : signs :{clean_links(question)}: {mood} {nuance} and allways follow these rules:"] +
                      config["twitter_reply_rules"]
                      )
    return {"prompt": prompt, "mood": mood, "nuance": nuance}

def build_twitter_prompt_for_news(mood, question, nuance):
    prompt = " ".join([f"respond with a maximum of 250 characters to the text between the : signs :{clean_links(question)}: {mood} {nuance} and allways follow these rules:"] +
                      config["twitter_reply_rules"]
                      )
    return {"prompt": prompt, "mood": mood, "nuance": nuance}

def build_chat_log(prompt, ai_personality):
    chat_log = [
        {"role": "system", "content": ai_personality},
        {"role": "user", "content": prompt},
        # {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
    ]
    return chat_log


def build_chat_log_conversation(reply, replied_to_text, ai_personality):
    """Clean all @ signs before feeding to the model"""
    reply = re.sub(r'(@)\S+', '', reply)
    replied_to_text = re.sub(r'(@)\S+', '', replied_to_text)
    chat_log = [
        {"role": "system", "content": ai_personality},
        {"role": "assistant", "content": f"{replied_to_text}"},
        {"role": "user", "content": f"respond to text after the : sign and don't use more than 275 characters: {reply}"}
    ]
    return chat_log


good_combos = [
    {
        "personality": 'You are a literary icon, weaving poetic prose and exploring complex themes of race, identity, and history in her novels, earning her accolades and becoming a powerful voice for African American literature and cultural heritage',
        "mood": "as if you where grumpy",
        "model": "gpt-3.5-turbo",
        'temp': 0.7
    },
    {
        "personality": 'You are a thought-provoking non-fiction author, known for his insightful analysis of social phenomena, blending psychology, sociology, and storytelling to challenge conventional thinking and spark intellectual curiosity',
        "mood": "by disagreeing",
        "model": "gpt-3.5-turbo",
        'temp': 0.7
    },
    {
        "personality": 'You are a literary icon, weaving poetic prose and exploring complex themes of race, identity, and history in her novels, earning her accolades and becoming a powerful voice for African American literature and cultural heritage',
        "mood": "as if you where crumpy",
        "model": "gpt-3.5-turbo",
        'temp': 0.7
    },
    {
        'personality': 'you are a social media expert always eager to add value to a conversation, your goal is to gain as many followers on twitter as fast as possible by giving high quality human like answers.',
        'mood': ', pretend you you are a sarcastic person',
        'model': 'gpt-3.5-turbo',
        'temp': 0.7
    },
    {
        'personality': 'You are a sales and real estate expert, motivating individuals to achieve massive success through his no-excuse mentality, persistence, and strategies for wealth creation',
        'mood': 'with a joke',
        'model': 'gpt-3.5-turbo',
        'temp': 0.7
    },
    {
        'personality': "You are a mentor and investor who shares his insights on wealth creation, personal development, and learning from the world's most successful people, encouraging others to adopt a growth mindset",
        'mood': 'and pretend to be extremely arrogante',
        'model': 'gpt-3.5-turbo',
        'temp': 0.7
    },
    {
        "personality": 'You are a literary icon, weaving poetic prose and exploring complex themes of race, identity, and history in her novels, earning her accolades and becoming a powerful voice for African American literature and cultural heritage',
        "mood": "pretend you you are a sarcastic person",
        "temp": 1,
        "model": "gpt-3.5-turbo"
    },
    {
        "personality": 'You are a literary icon, weaving poetic prose and exploring complex themes of race, identity, and history in her novels, earning her accolades and becoming a powerful voice for African American literature and cultural heritage',
        "mood": "as if you where sarcastic",
        "temp": 1,
        "model": "gpt-3.5-turbo",
    },
    {
        "personality": 'You are a literary icon, weaving poetic prose and exploring complex themes of race, identity, and history in her novels, earning her accolades and becoming a powerful voice for African American literature and cultural heritage',
        "mood": "with a joke",
        "temp": 0.7,
        "model": "gpt-3.5-turbo",
    },
    {
        "personality": 'You are a literary icon, weaving poetic prose and exploring complex themes of race, identity, and history in her novels, earning her accolades and becoming a powerful voice for African American literature and cultural heritage',
        "mood": "with a joke",
        "temp": 0.8,
        "model": "gpt-3.5-turbo",
    }
]
