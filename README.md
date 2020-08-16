## Chowder Discord Bot
#### DISCLAIMER: _"Chowder" is an entirely fictional character and does not represent the views or opinions of the bot's users or creators in any way._

### Running locally
1. Create a bot in the [Discord developer portal](https://discord.com/developers) and grab its token
2. Create an environment variable DISCORD_TOKEN={your token}
3. Invite your bot to your guild
4. Edit the `guild` value`config.json` to your guild's name 
5. Run `bot.py` using Python 3
###### Alternatively with Docker
5. Run `docker build -t chowder-bot .` from the base directory after step 4.
6. `docker run chowder-bot`

### Deploy/CI
* Pushing to master will automatically build and deploy the bot to [Heroku](https://chowdertron.herokuapp.com/)
