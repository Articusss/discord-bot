# discord-bot

General music bot for small, private use built with `discord.py` and `lavalink`. Features currently:

- Fully featured music player: multiple sources (Youtube/SoundCloud), queues, shuffling


## Requirements

The project requires `python 3.10` or higher. After cloning the repository, run:

```sh
$ pip install -r requirements.txt
```

`discord.py` also requires [additional system dependencies](https://discordpy.readthedocs.io/en/stable/intro.html), make sure to install them too.

## Usage

Create a `.env` file according to [the given example](./env.example) and fill out the sensitive information. Afterwards, start the bot running

```sh
$ python init.py
```