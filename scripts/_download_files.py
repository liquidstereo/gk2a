import csv
import os, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from alive_progress import alive_bar
from typing import List, Dict, Any, Tuple
import warnings

from PIL import Image
Image.MAX_IMAGE_PIXELS = None
warnings.filterwarnings("ignore", ".*DecompressionBombWarning.*")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs import Msg, Logger
from scripts._common import remove_exist, trim_last_lines, verify_img_file
from scripts._get_usable_workers import get_usable_workers
from scripts._backoff_download import backoff_download


MAX_WORKER = get_usable_workers()
LARGE_DATA_THRESHOLD = 100000
CHUNK_SIZE = 10000


def _count_csv_rows(data_path: str) -> int:
    with open(data_path, 'r', encoding='utf-8-sig') as f:
        return sum(1 for line in f) - 1


def _process_csv_chunk(chunk_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    processed_data = []
    for row in chunk_data:
        if 'url_status' not in row or not row['url_status']:
            row['url_status'] = 0
        else:
            try:
                row['url_status'] = int(float(row['url_status']))
            except (ValueError, TypeError):
                row['url_status'] = 0

        if 'download' not in row or not row['download']:
            row['download'] = False
        else:
            row['download'] = str(row['download']).lower() in ('true', '1', 'yes')

        processed_data.append(row)

    return processed_data



def _initialize_csv_data(data_path: str) -> List[Dict[str, Any]]:

    row_count = _count_csv_rows(data_path)

    if row_count < LARGE_DATA_THRESHOLD:
        # Msg.Info(f'Small dataset ({row_count:,} rows): using CSV module')
        data = []
        with open(data_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'url_status' not in row or not row['url_status']:
                    row['url_status'] = 0
                else:
                    try:
                        row['url_status'] = int(float(row['url_status']))
                    except (ValueError, TypeError):
                        row['url_status'] = 0

                if 'download' not in row or not row['download']:
                    row['download'] = False
                else:
                    row['download'] = str(row['download']).lower() in ('true', '1', 'yes')
                data.append(row)

        return data

    else:
        if not PANDAS_AVAILABLE:
            # Msg.Error(f'Large dataset ({row_count:,} rows): pandas is required for processing')
            raise ImportError('pandas library is required: pip install pandas')

        # Msg.Info(f'Large dataset ({row_count:,} rows): using pandas chunked processing')
        data = []

        for chunk in pd.read_csv(data_path, chunksize=CHUNK_SIZE, encoding='utf-8-sig'):
            chunk_data = chunk.to_dict('records')
            processed_chunk = _process_csv_chunk(chunk_data)
            data.extend(processed_chunk)

        return data



def verify_download(data: List[Dict[str, Any]],
                    dir_path: str) -> Tuple[List[Dict[str, Any]], int]:

    def _check_existing_file(info: tuple):
        '''Helper function to check a single file in a thread.'''
        index, download_path = info
        full_path = os.path.join(dir_path, download_path)

        if os.path.exists(full_path):
            try:
                if verify_img_file:
                    return (index, True, 200, True)
                else:
                    os.remove(full_path)
                    return (index, False, 0, False)
            except Exception:
                # Error during check, mark for re-download
                return (index, False, 0, False)
        # File doesn't exist
        return (index, False, 0, False)


    rows_to_verify = [(i, row['download_path']) for i, row in enumerate(data)
                      if row.get('download_path')]

    if not rows_to_verify:
        return data, 0

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
        results = list(executor.map(_check_existing_file, rows_to_verify))

    if not results:
        return data, 0


    for index, download_status, url_status, file_exists in results:
        if index < len(data):
            data[index]['download'] = download_status
            data[index]['url_status'] = url_status

    existing_count = sum(1 for res in results if res[3])

    return data, existing_count




def _process_result(future, future_info: tuple,
                    data: List[Dict[str, Any]], logger: Logger) -> Tuple[bool, str]:

    original_index, download_path = future_info
    base_name = os.path.basename(download_path)

    try:
        downloaded_path, status_code = future.result()

        if downloaded_path:
            if original_index < len(data):
                data[original_index]['url_status'] = status_code
                data[original_index]['download'] = True
            return True, f'SUCCESS: "{base_name}"'
        else:
            if original_index < len(data):
                data[original_index]['url_status'] = status_code
                data[original_index]['download'] = False
            return False, f'FAILURE: "{base_name}"'

    except Exception as e:
        if original_index < len(data):
            data[original_index]['url_status'] = -1
            data[original_index]['download'] = False
        return False, f'ERROR: "{base_name}"'



def download_files(data_path: str, dir_path: str = './downloads',
                   save_data: bool=False) -> Tuple[List[Dict[str, Any]], int, int]:

    data = _initialize_csv_data(data_path)
    log_path = data[0]['log_path'] if data else None


    logger = Logger(__name__, log_path)

    data, existing_count = verify_download(data, dir_path)

    if existing_count > 0:
        m = (f'Found {existing_count} existing files.'
             f'Skipping duplicate downloads.')
        logger.info(m)

    to_download = [
        (i, row) for i, row in enumerate(data)
        if row.get('img_url') and not row.get('download', False)
    ]

    total_files = len([row for row in data if row.get('download_path')])
    already_downloaded = len([row for row in data if row.get('download', False)])

    if not to_download:
        if existing_count > 0:
            m = (f'All {total_files} files are already downloaded. '
                 f'({existing_count} verified existing files)')
            Msg.Green(m)
        else:
            Msg.Green('All files are already downloaded.')
        return data, already_downloaded, 0

    urls = [row['img_url'] for _, row in to_download]
    download_paths = [os.path.join(dir_path, row['download_path']) for _, row in to_download]
    original_indices = [i for i, _ in to_download]

    error_count = 0
    logged_urls = set()


    # 🟢 DOWNLOAD.FILE
    with alive_bar(len(urls),spinner=None,title='PLEASE WAIT...',
                   title_length=20,length=22,dual_line=True,stats=True,
                   elapsed=True,manual=False,enrich_print=True) as bar:

        with ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
            future_to_info = {
                executor.submit(backoff_download, url, path, logger, logged_urls): (idx, path)
                for url, path, idx in zip(urls, download_paths, original_indices)
            }

            for future in as_completed(future_to_info):
                bar.title = 'DOWNLOADING...'
                is_success, message = _process_result(future, future_to_info[future], data, logger)
                if not is_success:
                    error_count += 1

                error_text = f' • FAILURE: {error_count}' if error_count > 0 else ''
                bar.text = Msg.Dim(f'{message}{error_text}', verbose=True)
                bar()

        bar.title = 'DOWNLOAD COMPLETED'

    if save_data:
        dropoff = ['timecode', 'data_path', 'log_path', 'img_url', 'fix']    # ← DROP.OFF
        cleaned_data = []
        for i, row in enumerate(data):
            cleaned_row = {k: v for k, v in row.items() if k not in dropoff}
            cleaned_row['index'] = i
            cleaned_data.append(cleaned_row)

        if cleaned_data:
            with open(data_path, 'w', encoding='utf-8-sig', newline='') as f:
                fieldnames = cleaned_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(cleaned_data)

            trim_last_lines(data_path)
    else:
        remove_exist(data_path)


    total_urls_count = len([row for row in data if row.get('download_path')])
    success_count = len([row for row in data if row.get('download', False)])
    new_downloads = success_count - existing_count

    download_dir_abs = os.path.abspath(dir_path).replace(os.sep, '/')
    summary_msg = (
        f'Download process complete. ("{download_dir_abs}") '
        f'Total: {total_urls_count}, Success: {success_count} '
        f'(Existing: {existing_count}, New: {new_downloads}), Failure: {error_count}'
    )
    logger.info(summary_msg)

    return data, success_count, error_count