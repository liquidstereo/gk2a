import os, sys, errno
from pathlib import Path
import time
import re
import requests
from typing import List, Literal, Union

sys.path.insert(0, str(Path(__file__).resolve().parents[1])) # 현재 파일의 ".parent[1]" 경로를 root로 잡고 추가한다. 뒤의 숫자가 parent단계

from configs import Msg, timer
# from scripts._common import is_valid_image
from scripts._data_map import LEVEL1B_MAP, LEVEL2_MAP
from scripts._fetch_data_info import (fetch_data_info)
from scripts._get_time_format import (dt_to_str, str_to_timecode, shift_timezone, local_to_utc, utc_to_local)


def get_time_info(time_str, fix: bool = False):


    year, month, day = time_str[:4], time_str[4:6], time_str[6:8]
    hour, minute = ('00', '00') if fix else (time_str[8:10], time_str[10:12])
    timecode = f'{year}{month}{day}{hour}{minute}'

    return {
        'year': year,
        'month': month,
        'day': day,
        'hour': hour,
        'minute': minute,
        'timecode': timecode.lower(),
        'fix': fix
    }



def generate_url(satellite: str, sensor: str,
                 level: str, cat: str, ch: str, area: str, resolution: str, proj: str,
                 year: int, month: int, day: int, hour: int,
                 timecode: str, ext: str):

    LEVEL_MAPPING = {'LE2': 'L2', 'LE3': 'L3', 'LE4': 'L4', 'LE1B': 'L1B'}
    url_level = LEVEL_MAPPING.get(level, level)
    is_le = level in LEVEL_MAPPING


    filename = (f'{satellite}_{sensor}_'
                f'{level}_{ch}_{area}{resolution}{proj}_'
                f'{timecode}').lower()

    if not is_le:
        filename += ext

    if level == 'LE1B':
        url_fmt = (f'https://nmsc.kma.go.kr/IMG/'
                   f'{satellite}/{sensor}/PRIMARY/{url_level}'
                   f'/COMPLETE/{area.upper()}/{year}{month}/{day}/{hour}')
    else:
        url_fmt = (f'https://nmsc.kma.go.kr/IMG/'
                   f'{satellite}/{sensor}/{url_level}'
                   f'/{cat}/{area.upper()}/{year}{month}/{day}/{hour}')

    return f'{url_fmt}/{filename}{ext if is_le else ""}'




# =========================================================================== #

def get_metadata(download_dir: Path, area: str, ch: str,
                 input_time_str: str, ext: str):

    timecode = dt_to_str(input_time_str)

    data_info = fetch_data_info(ch, area, ext)
    fix = data_info['fix']  # UTC 00:00 고정이 필요한 일일 데이터 여부

    utc_shorten = shift_timezone(timecode, 'utc', fmt=False)
    local_shorten = shift_timezone(utc_shorten, 'local', fmt=False)

    utc_time = str_to_timecode(utc_shorten, as_str=True)
    local_time = str_to_timecode(local_shorten, as_str=True)

    time_info = get_time_info(timecode, fix)

    data_url = generate_url(
        data_info['satellite'], data_info['sensor'], data_info['level'],
        data_info['cat'], data_info['ch'], area,
        data_info['resolution'], data_info['proj'],
        time_info['year'], time_info['month'], time_info['day'], time_info['hour'],
        time_info['timecode'], ext
    )

    result_format = (f'{data_info["satellite"]}'
                     f'_{data_info["sensor"]}'
                     f'_{data_info["level"]}'
                     f'_{area}'
                     f'_{data_info["cat"]}'
                     f'_{data_info["ch"]}')

    download_filename = f'{data_info["ch"]}_{utc_to_local(utc_shorten)}'.upper()

    subdir_path = os.path.join(download_dir, result_format.upper())
    data_path = os.path.join(subdir_path, f'{result_format.lower()}.csv')
    download_path = os.path.join(subdir_path, f'{download_filename}{ext}')
    log_path = os.path.join(subdir_path, f'{result_format.lower()}.log')


    return {
        'satellite': data_info['satellite'],
        'sensor': data_info['sensor'],
        'level': data_info['level'],
        'cat': data_info['cat'],
        'cat_ch': data_info['ch'],
        'resolution': data_info['resolution'],
        'area': area,
        'proj': data_info['proj'],
        'year': time_info['year'],
        'month': time_info['month'],
        'day': time_info['day'],
        'hour': time_info['hour'],
        'minute': time_info['minute'],
        'timecode': time_info['timecode'],
        'utc': utc_time,
        'localtime': local_time,
        'ext': ext,
        'fix': fix,
        'result_format': result_format,
        'data_path': data_path,
        'log_path': log_path,
        'download_path': download_path,
        'url': data_url
    }


@timer
def main():

    # None
    return None


if __name__ == '__main__':
    main()