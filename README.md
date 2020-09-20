# MATCOM Assistant Telegram Bot:

This project, a [Telegram](https://telegram.org/) bot, was started to assist Computer Science and Math students of the University of Havana (Cuba) in the organization of Telegram rooms to aid students in the preparation towards the University admissions tests during the covid19 crisis. This initiative has not direct ties with the University of Havana.

## How does it works?

Firstly, the bot needs to be admin in 3 chats:

1. A public group

2. A private group

3. A public channel

When someone sends a message marked with #question (or the QuestionWord in the config 
file) in (1) the bot will send it to (2) and (3) with a few lines showing the ID of the question, who asked it and a section with links to the current answers if any, this section will be edited every time a new answer is provided. 

In 2, replying to the question message sent by the bot using #answer (or the AnswerWord in the 
config file) will send the answer to 1 and 3, showing who answered it and providing a link to the question. 

It supports photos, documents and audios and the questions can be loaded in DM with the bot and answered right there.

## How do I run it?

1. clone this repo

2. add the bot as admin to the Telegram chats

3. modify the config.ini file with your bot token and chat IDs

4. ```
   pip install python-telegram-bot
   ```

5. ```
   python bot.py
   ```


If you can't find your groups' chat IDs, just send the command "/sendMeChatID"
in each chat after step 2. 
