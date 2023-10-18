

# 🤖 TwitMind - ChatGPT-Powered Twitter Bot 🐦

Welcome to the world of intelligent Twitter bots powered by ChatGPT! As a developer, you have the opportunity to harness advanced technology and powerful features to create your very own Twitter bot that stands out in the digital crowd.

## Features:

- **🎭 Bot Personality Control:** Tailor the personality of your bot with precision. You have the creative freedom to define its character, tone, and style. Whether you want your bot to be witty, informative, friendly, or even a little mysterious, it's entirely up to you!

- **📊 Local Database:** Keep your bot organized and track its actions effortlessly. TwitMind seamlessly integrates with a local database, allowing you to log interactions, tweets, and vital data, ensuring efficient management.

- **📱 Telegram Support:** Take your bot on the go! With Telegram support, you can see your bots actions in real time.

- **💬 ChatGPT Integration:** TwitMind seamlessly integrates with ChatGPT, providing you with the ability to generate human-like responses, answer questions, and engage in dynamic conversations with your Twitter audience.
-  **Respond to Tweets Based on Keywords:** TwitMind  can identify and respond to tweets containing specific keywords, enabling targeted engagement.

- **📰 News Search Integration:** TwitMind can search the web for news on topics of your choice, allowing you to share fresh and relevant content with your followers, keeping them engaged and informed.

- **📣 Replying to Mentions:** Engage with your audience! Your bot can monitor and respond to mentions, ensuring that you never miss an opportunity to connect with your followers.

- **📝 Post New Tweets:** Keep your Twitter feed active and exciting! Schedule and post new tweets on your terms, whether you're sharing thoughts, updates, or even promoting your content.

Get ready to experience a new level of Twitter interaction with TwitMind a ChatGPT-powered bot. It's more than just a bot; it's your digital sidekick, designed to enhance your social media presence and engage with your audience in meaningful ways. 🚀

You can see a live version of the bot by following @_RussellEdwards on Twitter  

## Running the Twitter Bot - Quick Start Guide

### Dependencies
To run the Twitter bot, it is recommended to use Python 3.10 or higher. **First**, you need to install the required dependencies. To do this, open the project's root folder and execute the following command:

    pip install -r requierements.txt 

You will also need to create an **twitter app account** on https://dev.twitter.com/apps

1. Sign in with your Twitter account
2. Create a new app account
3. Modify the settings for that app account to allow read & write
4. Generate a new OAuth token with those permissions

Following these steps will create 4 tokens that you will need to place in the configuration file discussed below.

**ChatGPT**
To run the bot you also need an OpenAi API Key for ChatGPT



## Bot Customization

**Open `config.py` File:** Customize your bot's behavior by editing the `config.py` file. Here's what you can configure:
- **Keywords:**
		* This defines which topics the the bot should search and reply to.
- **Search_terms**
		* Search terms used for new search for new tweets
### Personality - The personality consist of 3 Layers (L1, L2 and L3)
- **ai_personalities**
		* L1 The bot can change its personality based on this list. By default a random personality out of this list is chosen on each new tweet. You can experiment with list to get the desired bot personality. 
	- **moods**
		* this is L2 of personality and adds finer control on how the bot should respond. You could define a personality but than make the bot always sarcastic with the mood controller. By default a random personality is combined with a random mood if you want a more consistent bot personality you can change that by only have one personality and one mood defined.
	- **moods_reply_mentions**
		* this defines with which mood the bot should respond to mentions
	- **moods_news_post**
		* the mood for tweets based on news
	- **strong text**nuances
		* the nuance is the L3 of the personality and adds fine tuning to the personality of the bot. 
	- **mood_filter_words**
		* this defines the keywords once detected change the mood of the bot. For example: If the keyword "Asexual" was detected in the tweet than the bot change change its attitude / mood.
	- **response_mood_if_filter**
		* here you define the personality to bot should switch to if one of the mood_filter_words was detected.
- **twitter_reply_rules_V2**
		* this is the prompt engineering of the bot and the base for the actual prompt that is send to ChatGPT. Here you can define all the rules you want ChatGPT to follow for the response. High-quality rules lead to better ChatGPT outputs.
- **temps**
		* Control ChatGPT's temperature for responses. Learn more [here](https://community.openai.com/t/cheat-sheet-mastering-temperature-and-top-p-in-chatgpt-api-a-few-tips-and-tricks-on-controlling-the-creativity-deterministic-output-of-prompt-responses/172683) 
- **models**
		* Choose the model you want to use. Check [here](https://platform.openai.com/docs/models/overview) for model availability.
- **likes**
		*Decide whether the bot should like tweets it replies to.

## Bot Actions

4. **Open `main.py` File:** In this file, you can comment out actions under `if __name__ == "__main__":` your bot should not perform by adding `#` before `p.start` command of the respective function.

## Running the Bot

5. **Run the Bot:** To start your bot, open your terminal and execute:

   `python main.py`
  

### Contribution Guidelines ###

Thank you for considering contributing to TwitMind! Contributions from the community are highly appreciated. Here are some guidelines to help you get started:

1. **Reporting Issues**
   - If you encounter any issues or bugs, please check the existing issues to see if it has already been reported.
   - If not, feel free to create a new issue, including detailed information about the problem you encountered, steps to reproduce it, and your environment (Python version, OS, etc.).

2. **Feature Requests**
   - If you have ideas for new features or improvements, you can open a feature request issue. Clearly describe the feature you have in mind and why you think it would be valuable.

3. **Pull Requests**
   - We welcome contributions in the form of pull requests.
   - Please make sure your code follows the project's coding style and conventions.
   - Document any new features, functions, or changes you make.
   - Be prepared to discuss and address feedback on your pull request.

4. **Testing**
   - Ensure that your code is thoroughly tested before submitting a pull request.
   - If you are adding new functionality, include relevant tests.
   - Run the existing tests to make sure your changes don't break anything.

5. **Documentation**
   - Improve or extend the project's documentation when necessary.
   - Document any new configuration options, environment variables, or installation instructions.

## Disclaimer

We hold no liability for what you do with this bot or what happens to you by using this bot. Abusing this bot *can* get you banned from Twitter, so make sure to read up on [proper usage](https://support.twitter.com/articles/76915-automation-rules-and-best-practices) of the Twitter API.