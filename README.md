# IGWOCTISI Server

Game server for [IGWOCTISI](https://github.com/porke/igwoctisi) game. It was developed as a team project on the last term of my Bachelor's Degree studies. It was based on the then-popular web browser [Warlight](http://warlight.net/), and shares most of the rules, with single exception: it takes place in the space.

More information about the game itself is in the main repo.

## A few words about technology used

Server is written using pure Python 2.7, with SQLAlchemy being single external exception. It utilizes builtin `threading` and `socket` modules in order to communicate with game clients and manage multiple game states.

At the time (2013) I wasn't using Python on the daily basis - I chose this language because I wanted to learn something new, and it looked awesome (and it still does). That may make the code slightly... unreadable, not documented and not following lint rules (frankly, the first thing I noticed after two years was lack of `requirements.txt` or any other list of external dependencies).

For example, you can see me reinvent the wheel a few times (`Common.console_message` instead of `logging`, parsing arguments manually in `Server.py` instead of using `argparse` etc.). And I don't want to know what I was thinking with those tabs instead of standard 4-space indentation, really.

Still, it was pretty fun project for me. And for the rest of the team, although they were using some ~~inferior~~ different tools. Again, see main repo for more on this.

## Setup

As it is with Python, you should run everything inside virtualenv. (My current stack is [pyenv](https://github.com/yyuu/pyenv) + [virtualenvwrapper](https://virtualenvwrapper.readthedocs.org/).) Install SQLAlchemy (either 0.7 or 0.8), and then run `Server.py`.

### Arguments

Usage:

```bash
python Server.py [optional-arguments...] host [port]
```

Host defaults to `0.0.0.0`, and port defaults to `23456`.

Arguments:

- `--debug`: more verbosity
- `--database`: connect to external MySQL database
- `--logging`: save logs to external file (useful for debugging purposes)

### Config

Create `Config.py` and fill it with some data. The only thing that is used right now is database configuration (I don't believe that will change in the future).

Example file:

```python
DATABASE = {
    'host': 'localhost',
    'username': 'igwoctisi',
    'password': 'z0mg',
    'database': 'igwoctisi',
}
```

# License

See [LICENSE.md](LICENSE.md).
