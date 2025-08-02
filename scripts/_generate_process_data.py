import os, sys, errno
from pathlib import Path
from datetime import datetime
from io import StringIO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs import Logger
from scripts._common import remove_exist
from scripts._get_time_format import get_time_schedule
from scripts._get_metadata import get_metadata


def generate_datalist(download_dir: Path,
                      area: str, ch: str, ext: str='.srv.png',
                      start: str=None, end: str=None):


    schedule = get_time_schedule(start, end)
    parse_metadata = get_metadata(download_dir,
                                  area, ch, schedule['utc'][0], ext)

    fix = parse_metadata['fix']
    per = 144 if fix else 1

    # *** DATA.HEADER *** #
    header = (f'index,satellite,sensor,'
              f'level,area,category,channel,resolution,proj,'
              f'timecode,localtime,utc,fix,'
              f'data_path,log_path,download_path,img_url,'
              f'url_status,download')


    datalist = [header]

    utc_schedule = schedule['utc']
    local_schedule = schedule['local']



    for i in range(0, len(local_schedule), per):

        metadata_local  = get_metadata(download_dir,
                                       area, ch, local_schedule[i], ext)
        metadata_utc    = get_metadata(download_dir,
                                       area, ch, utc_schedule[i], ext)

        satellite     = metadata_local['satellite']
        sensor        = metadata_local['sensor']
        level         = metadata_local['level']
        area          = metadata_local['area']
        category      = metadata_local['cat']
        channel       = metadata_local['cat_ch']
        resolution    = metadata_local['resolution']
        proj          = metadata_local['proj']
        year          = metadata_local['year']
        month         = metadata_local['month']
        day           = metadata_local['day']
        hour          = metadata_local['hour']
        minute        = metadata_local['minute']
        timecode      = metadata_local['timecode']
        utc           = metadata_local["utc"]
        localtime     = metadata_local['localtime']
        ext           = metadata_local['ext']
        fix           = metadata_local['fix']
        data_path     = metadata_local['data_path']
        log_path      = metadata_local['log_path']
        download_path = metadata_local['download_path']

        url           = metadata_utc['url']
        status        = 0
        download      = False

        row = (f'{i},{satellite},{sensor},{level},{area},'
               f'{category},{channel},{resolution},{proj},'
               f'{timecode},{str(localtime)},{str(utc)},'
               f'{fix},'
               f'{data_path},{log_path},{download_path},{url},'
               f'{status},{download}')

        datalist.append(row)


    return datalist


def generate_datafile(download_dir: Path,
                      area: str, ch: str, ext: str='.srv.png',
                      start: str=None, end: str=None):

    org_area = area
    datalist = generate_datalist(download_dir,
                                 area, ch, ext, start, end)

    data_path = os.path.abspath(datalist[1].split(',')[-6])
    log_path  = os.path.abspath(datalist[1].split(',')[-5])

    for path in (data_path, log_path):
        if os.path.isfile(path):
            remove_exist(path)

    os.makedirs(os.path.dirname(data_path), exist_ok=True)

    logger = Logger(__name__, log_path)

    parse_area  = str(datalist[1].split(',')[4])
    parse_ch = str(datalist[1].split(',')[6])
    parse_fix = str(datalist[1].split(',')[12])

    # *** LOGGER *** #
    if parse_fix == True:
        w = (f'Channel "{parse_ch}" generates '
             f'a single daily data point, '
             f'with the timestamp defaulting to 00:00.')
        logger.warning(w)

    if parse_area != org_area :
        w = (f'Channel "{parse_ch}" does not support "{area.upper()}" area. '
             f'Fallback conversion to "{parse_area.upper()}" area applied.')
        logger.warning(w.upper(), plain=False)
    # *** LOGGER *** #

    with open(data_path, 'w', encoding='utf-8-sig') as f:
        for line in datalist:
            f.write(line + '\n')

    return data_path


def main():
    return None

if __name__ == '__main__':
    main()