import logging
import requests
import os
from rich import progress
from fcloud.api import search


def save_urls_in(results: list, path: str = "urls.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for song in results:
            f.write(song.url + "\n")
    logging.info(path + " saved")


def rich_progress():
    """Returns a custom `rich` progress bar instance"""
    # https://github.com/pypa/pip/blob/3820b0e52c7fed2b2c43ba731b718f316e6816d1/src/pip/_internal/cli/progress_bars.py#L41
    columns = (
        progress.TextColumn("[progress.description]{task.description}"),
        progress.BarColumn(),
        progress.DownloadColumn(),
        progress.TransferSpeedColumn(),
        progress.TextColumn("eta"),
        progress.TimeRemainingColumn(),
    )
    _progress = progress.Progress(*columns)
    return _progress


def download_url(url: str, name: str):
    r = requests.head(url, allow_redirects=True)
    file_size = int(r.headers.get("content-length", 0))
    _progress = rich_progress()
    task_id = _progress.add_task(name, total=file_size)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(name, "wb") as f:
            with _progress:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
                    _progress.update(task_id, total=file_size, advance=len(chunk))


def download_song(song, path: str = None):
    file_name = song.artist + " - " + song.name
    if path:
        file_name = os.path.join(path, file_name)
    file_name += ".mp3"
    download_url(song.url, file_name)


def parse_args(args):
    results = []
    i = 0
    # Sometimes there's no any song fetched.
    while not results and i < 4:
        if i > 1:
            logging.info("No result found. Retrying...")
        results = search(args.query)
        i += 1
    if not results:
        raise SystemExit(
            f"Unfortunately no result found for '{args.query}'. Try again please, it happens sometimes!"
        )
    if args.save_urls:
        save_urls_in(results)
    if args.download:
        download_song(results[0])
