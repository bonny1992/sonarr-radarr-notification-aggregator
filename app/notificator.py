import time, urllib, yaml, datetime
from urllib.request import urlopen
import schedule
from pytz import timezone
from pathlib import Path
from models import Show, Movie

# time.sleep(500)
# Path("/data").mkdir(parents=True, exist_ok=True)

config_file = Path('/data/config.yml')

while True:
    if not config_file.is_file():
        print('Waiting 5 seconds for config file generation')
        time.sleep(500)
    break

with open('/data/config.yml', 'r') as opened:
    CONFIG = yaml.load(opened, Loader=yaml.SafeLoader)

current_tz = timezone(CONFIG['timezone'])

def create_shows_msg():
    msg = '*Shows*\n\n{SHOWS}\n\n\n'
    episodes = Show.select().order_by(Show.series)
    if len(episodes) > 0:
        eps = []
        for episode in episodes:
            eps.append(
                '{SERIES} - {SEASON}x{EPISODE} - {TITLE} | {QUALITY}'.format(
                    SERIES = episode.series,
                    SEASON = episode.season,
                    EPISODE = episode.episode,
                    TITLE = episode.title,
                    QUALITY = episode.quality
                )
            )
            deletion = Show.delete().where(
                Show.series == episode.series,
                Show.season == episode.season,
                Show.episode == episode.episode
            )
            deletion.execute()
        eps_full_text = '\n'.join(eps)
        print(eps)
        msg = msg.format(
            SHOWS = eps_full_text
        )
        return msg
    return ''

        
def create_movies_msg():
    msg = '*Movies*\n\n{MOVIES}\n\n\n'
    movies = Movie.select().order_by(Movie.title)
    if len(movies) > 0:
        mvs = []
        for movie in movies:
            mvs.append(
                '{TITLE} ({YEAR}) | {QUALITY} | {IMDB_LINK}'.format(
                    TITLE = movie.title,
                    YEAR = movie.year,
                    QUALITY = movie.quality,
                    IMDB_LINK = '[IMDB Link](https://www.imdb.com/title/{}/)'.format(movie.imdb)
                )
            )
            deletion = Movie.delete().where(
                Movie.imdb == movie.imdb,
            )
            deletion.execute()
        mvs_full_text = '\n'.join(mvs)
        print(mvs)
        msg = msg.format(
            MOVIES = mvs_full_text
        )
        return msg
    return ''

def send_tg_message():
    msg = create_shows_msg() + create_movies_msg()
    if msg == '':
        return
    quiet = False
    hour = int(datetime.datetime.now(current_tz).hour)
    if hour >= int(CONFIG['start_quiet']) or hour <= int(CONFIG['end_quiet']):
        quiet = True
        msg = '💤 *Modalità notte* 💤\n\n\n\n' + msg
    TG_URL = 'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&disable_web_page_preview=true&parse_mode=Markdown{QUIET}&text={MSG}'
    TG_URL = TG_URL.format(
        BOT_TOKEN = CONFIG['telegram_bot_token'],
        TG_CHAT_ID = CONFIG['telegram_chat_id'],
        QUIET = '&disable_notification=true' if quiet else '',
        MSG = urllib.parse.quote_plus(msg)
    )
    print(TG_URL)
    urlopen(TG_URL)

schedule.every(int(CONFIG['skip_hours'])).hour.do(send_tg_message)

while True:
    schedule.run_pending()
    time.sleep(1)