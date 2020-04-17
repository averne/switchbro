# switchbro

Discord webhook bot for switchbrew rss:
+ Parses rss feed from switchbrew wiki and post updates.
+ Renders diff as png.

<p align="center"><img src="https://i.imgur.com/EXSL1i6.png" height=500></p>

# Setup
```sh
$ git clone https://github.com/averne/switchbro.git
$ cd switchbro
```
Create a `webhook.url` file containing the url of your Discord webhook, or edit [main.py](https://github.com/averne/switchbro/blob/master/src/main.py).
```sh
$ python3 -m venv env
$ source env/bin/activate
$ python3 -m pip install -U -r requirements.txt
$ python3 src/main.py
```
Alternatively, a systemd unit file template is [provided](https://github.com/averne/switchbro/blob/master/res/switchbro.service) (fill in user and directory).
