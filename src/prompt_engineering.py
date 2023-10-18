import unicodedata

import config
from src.helper import clean_links


def mood_generator(question, mood, filter_words=None):
    if not filter_words:
        filter_words = config.config["mood_filter_words"]

    filter_words = [x.lower() for x in filter_words]
    if not set(question.replace("#", "").lower().split()).isdisjoint(filter_words):
        return config.config["response_mood_if_filter"]
    else:
        return mood

def gpt_build_chat_log_conversation(newprompt: str, ai_personality: str, max_output_len: int, rules, mood: str,                                    nuances: str):
    mood = mood_generator(newprompt, mood)

    history = [
        {"role": "user",
         "content": f"i will give you a text and i want you to respond {mood} and {nuances} and with not more than {max_output_len} characters respond with OK when you are ready!"},
        {"role": "assistant", "content": "OK"},
        {"role": "user",
         "content": f'following this rules for your response: {rules} respond with OK when you are ready!'},
        {"role": "assistant", "content": "OK"},
    ]

    chat_log = [{"role": "system", "content": ai_personality}]
    chat_log += history
    chat_log.append({"role": "user", "content": clean_links(unicodedata.normalize("NFKD", newprompt))})

    params = {"mood": mood, "nuance": nuances, "max_output_len": max_output_len, "rules": rules}

    return chat_log, params


def gpt_build_chat_log_continue_conversation(chatlog_history: list, new_responses: list):
    # input example
    # new_responses = [{"role": "assistant", "content": "this is the model response"},
    #                  {"role": "user", "content": "this is the user response on the model response"}]

    for i in new_responses:
        chatlog_history.append(
            {"role": f'{i["role"]}', "content": clean_links(unicodedata.normalize("NFKD", i["content"]))})

    return chatlog_history


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
