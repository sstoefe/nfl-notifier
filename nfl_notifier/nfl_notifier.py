import logging
import requests
import toml

from bs4 import BeautifulSoup, Tag
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

from nfl_notifier.google_calendar import create_event


def extract_nfl_broadcast_information():
    """Extract necessary information about ran nfl broadcasts: season, gameday, date and game information.

    Returns:
        Tuple[str, str, str, List[Tuple[str, str, str, str]]]: season, gameday, date, games
    """
    ran_nfl_live_url = "https://www.ran.de/us-sport/nfl/live"
    page = requests.get(ran_nfl_live_url)
    soup = BeautifulSoup(page.content, "html.parser")

    content_area = soup.find("div", class_="content-area left-container")
    formatted_text = content_area.find_next("div", class_="formatted-text")
    elements = formatted_text.findChildren()

    season = None
    gameday = None
    date = None
    games = []

    for element in elements:
        if not season:
            season = find_season(element)

        if not gameday and not date:
            gameday, date = find_gameday_and_date(element)

        game = find_game(element)
        if all(game):
            games.append(game)

    return season, gameday, date, games


def find_season(element: Tag) -> str:
    """Extract season information

    Args:
        element (Tag): element to inspect

    Returns:
        str: season
    """
    if element.name == "h3":
        if element.attrs == {}:
            if "Saison" in element.text:
                return element.text.split("Saison")[1].strip()
    return None


def find_gameday_and_date(element: Tag) -> Tuple[str, str]:
    """Extract gameday and date

    Args:
        element (Tag): element to inspect

    Returns:
        Tuple[str, str]: gameday and date
    """
    if element.name == "p":
        if "Spieltag" in element.text:
            split = element.text.split(":")
            if split[1].strip() != "":
                gameday = split[0].strip()
                date_unformatted = split[1].strip()
                _, date = date_unformatted.split(",")
                return gameday, date.strip()
    return None, None


def find_game(element: Tag) -> Tuple[str, str, str, str]:
    """Extract time, game, broadcast and url

    Args:
        element (Tag): element to inspect

    Returns:
        Tuple[str, str, str, str]: time, game, broadcast, url
    """
    if element.name == "p":
        if "Uhr:" in element.text:
            if "#ranNFLsüchtig" not in element.text:
                child_tag = element.find("a")
                if child_tag:
                    time_split = element.text.replace("\xa0", " ").split(": ")
                    game_split = time_split[1].split("live")
                    time = time_split[0].split(" ")[0].strip()
                    game = game_split[0].strip()
                    broadcast = child_tag.text.strip()
                    url = f"https://www.ran.de{child_tag.attrs['href']}"
                    return time, game, broadcast, url
    return None, None, None, None


def main():
    if Path("config.toml").exists():
        config = toml.load("config.toml")
        logging_path = (
            Path(config["nfl-notifier"]["logging_path"])
            if config["nfl-notifier"]["logging_path"]
            else Path("nfl-notifier.log")
        )
    else:
        logging_path = Path("nfl-notifier")

    logging.basicConfig(
        filename=logging_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    )
    logging.getLogger("googleapiclient").setLevel(logging.ERROR)

    season, gameday, date, games = extract_nfl_broadcast_information()
    for game in games:
        game_time, game_summary, game_broadcast, game_link = game
        game_date = datetime.strptime(f"{date} {season}", "%d. %B %Y")
        hours, minutes = game_time.split(":")
        game_start = datetime(
            year=game_date.year,
            month=game_date.month,
            day=game_date.day,
            hour=int(hours),
            minute=int(minutes),
        )
        game_end = game_start + timedelta(hours=3, minutes=30)

        created_event = create_event(
            summary=f"{gameday}: {game_summary} {game_broadcast}",
            description=f"{game_broadcast}: {game_link}",
            starttime=game_start.isoformat(),
            endtime=game_end.isoformat(),
        )

        logging.info(
            f"event created (summary: '{created_event['summary']}', starts at: {created_event['start']['dateTime']}, ends at: {created_event['end']['dateTime']}"
        )
