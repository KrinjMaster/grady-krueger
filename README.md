# Grady Krueger
You teachers assistant with paper test checking.
## How to run locally
To run locally first install Docker and Docker CLI. Then in terminal run 
```
docker pull krinjmax/grady-krueger:latest
```
Then for project to startup correctly create a directory and file within it called something like ``.env``, there you will write your telegram bot token and option to use webhooks (not configured yet).
After you created ``.env`` file you should write 2 variables there:
```env
BOT_TOKEN=Your_telegram_bot_token
BOT_USE_WEBHOOK=False (does not really matter, but better set to False)
```
After that, goto directory where ``.env`` file is located and execute this command in terminal:
```
docker run --rm --env-file=.env krinjmax/grady-krueger:latest
```
Insted of ``.env`` insert your env file name with ``.`` in front. ``--rm`` flag just removes container after you closed it.

## Run and modify
For that just install Python3, pip and clone this git repo. After you've done it run this command:
```
pip install -r requirements.txt
```
