import os, sys
from pathlib import Path
import requests
import backoff

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs import Logger
from scripts._common import verify_img_file

MIN_FILE_SIZE = 100_000  # 100KB
MAX_RETRIES = 3
MAX_TIMEOUT = 5

def is_valid_image_url(response: requests.Response) -> bool:
    return (
        response.status_code == 200 and
        response.headers.get('Content-Type', '').startswith('image/') and
        len(response.content) >= MIN_FILE_SIZE
    )


@backoff.on_exception(
    backoff.expo,
    (requests.RequestException, ValueError),
    max_tries=MAX_RETRIES,
    jitter=None
)


def try_download(url: str) -> requests.Response:
    response = requests.get(url, timeout=MAX_TIMEOUT)
    if not is_valid_image_url(response):
        e = (f'Not a valid image URL: '
             f'({response.status_code}, {response.headers.get("Content-Type")})')
        raise ValueError(e)
    return response


def backoff_download(url: str, download_path: str,
                     logger: Logger, logged_urls: set) -> tuple[str | None, int]:
    try:
        response = try_download(url)

        os.makedirs(os.path.dirname(download_path), exist_ok=True)

        with open(download_path, 'wb') as f:
            f.write(response.content)
            if verify_img_file(download_path) :
                logger.info(f'SUCCESS: {os.path.basename(download_path)}')
            else :
                logger.error(f'FAILURE: {os.path.basename(download_path)}')
        return download_path, 200

    except Exception as e:
        if url not in logged_urls:
            logger.error(f'FAILURE: {url} - {e}')
            logged_urls.add(url)
        return None, 404