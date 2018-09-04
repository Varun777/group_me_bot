[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

# Interactive GroupMe Chat Bot

This package creates a docker container that runs a GroupMe chat bot to interact with a GroupMe Chat Room.

## Getting Started

These instructions will get you a copy of the project up and running
on your local machine for development and testing purposes.

### Installing
With Docker:
```bash
git clone https://github.com/nickcollins24/group_me_bot

cd group_me_bot

docker build -t ff_bot .
```

Without Docker:

```bash
git clone https://github.com/nickcollins24/group_me_bot

cd group_me_bot

python3 setup.py install
```


## Basic Usage

This gives an overview of all the features of `group_me_bot`

### Environment Variables

- BOT_ID: This is your Bot ID from the GroupMe developers page
- BOT_NAME: This is the name that you gave your GroupMe Bot, or the name that you want your Bot to be referred to as
- USER_ID: This is the ID of the user that you want your Bot to listen for.
- GROUP_ID: This is the ID of the group that you made your Bot a part of.
- ACCESS_TOKEN: This is your personal Access Token from the GroupMe developers page

### Running with Docker
```bash
>>> export BOT_ID=[enter your GroupMe Bot ID]
>>> export BOT_NAME=[enter your GroupMe Bot Name]
>>> export USER_ID=[enter your GroupMe User ID]
>>> export GROUP_ID=[enter your GroupMe Group ID]
>>> export ACCESS_TOKEN=[enter your GroupMe Access Token]
>>> cd group_me_bot
>>> docker run --rm=True \
-e BOT_ID=$BOT_ID \
-e BOT_NAME=$BOT_NAME \
-e USER_ID=$USER_ID \
-e GROUP_ID=$GROUP_ID \
-e ACCESS_TOKEN=$ACCESS_TOKEN
ff_bot
```

### Running without Docker
```bash
>>> export BOT_ID=[enter your GroupMe Bot ID]
>>> export BOT_NAME=[enter your GroupMe Bot Name]
>>> export USER_ID=[enter your GroupMe User ID]
>>> export GROUP_ID=[enter your GroupMe Group ID]
>>> export ACCESS_TOKEN=[enter your GroupMe Access Token]
>>> cd group_me_bot
>>> python3 ff_bot/ff_bot.py
```

## Setting up GroupMe, and deploying app in Heroku

**Do not deploy 2 of the same bot in the same chat.**

Go to www.groupme.com and sign up or login

If you don't have one for your league already, create a new "Group Chat"

![](https://i.imgur.com/32ioDoZ.png)

Next we will setup the bot for GroupMe

Go to https://dev.groupme.com/session/new and login

Click "Create Bot"

![](https://i.imgur.com/TI1bpwE.png)

Create your bot. GroupMe does a good job explaining what each thing is.

![](https://i.imgur.com/DQUcuuI.png)

After you have created your bot you will see something similar to this. Click "Edit"

![](https://i.imgur.com/Z9vwKKt.png)

This page is important as you will need the "Bot ID" on this page.You can also send a test message with the text box to be sure it is connected to your chat room.
Side note: If you use the bot id depicted in the page you will spam an empty chat room so not worth the effort

![](https://i.imgur.com/k65EZFJ.png)

### Heroku setup

Heroku is what we will be using to host the chat bot (for free)

**You should not need to enter credit card information for this hosting service for our needs.**
You **may** run out of free hours without a credit card linked. If you decide to link your credit card you will have enough free hours for the month for a single application since this more than doubles your available hours. We are not responsible for any charges associated with Heroku.

Go to https://id.heroku.com/login and sign up or login


**!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!**

**Click this handy button:**
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

**!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!**

Go to your dashboard (https://dashboard.heroku.com/apps)
Now you will need to setup your environment variables so that it works for your league. Click Settings at your dashboard. Then click "Reveal Config Vars" button and you will see something like this.

![](https://i.imgur.com/7a1V6v8.png)

Now we will need to edit these variables (click the pencil to the right of the variable to modify)
Note: App will restart when you change any variable so your chat room may be semi-spammed with the init message of "Hai" you can change the INIT_MSG variable to be blank to have no init message. It should also be noted that Heroku seems to restart the app about once a day

- BOT_ID: This is your Bot ID from the GroupMe developers page
- BOT_NAME: This is the name that you gave your GroupMe Bot, or the name that you want your Bot to be referred to as
- USER_ID: This is the ID of the user that you want your Bot to listen for.
- GROUP_ID: This is the ID of the group that you made your Bot a part of.
- ACCESS_TOKEN: This is your personal Access Token from the GroupMe developers page

After you have setup your variables you will need to turn it on. Navigate to the "Resources" tab of your Heroku app Dashboard.
You should see something like below. Click the pencil on the right and toggle the buton so it is blue like depicted and click "Confirm."
![](https://i.imgur.com/J6bpV2I.png)

You're done! You now have a fully featured GroupMe chat bot!

Unfortunately to do auto deploys of the latest version you need admin access to the repository on git. You can check for updates on the github page (https://github.com/nickcollins24/group_me_bot/commits/master) and click the deploy button again; however, this will deploy a new instance and the variables will need to be edited again.
