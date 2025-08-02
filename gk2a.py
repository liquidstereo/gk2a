import argparse

from configs import WorkDirs, Etimer
from scripts import (generate_datafile, download_files,
                     show_result, preview_result)

# TODO 📌: AWAITING REFACTORING.

def exec_gk2a(area: str=None, channel: str=None, ext: str='.srv.png',
              start: str=None, end: str=None, preview: bool=False) :

    timer = Etimer()

    print(f'-')

    download_dir = WorkDirs.init('downloads')
    processfile  = generate_datafile(download_dir,
                                                area, channel, ext,
                                                start, end)

    dataframe, valid, fail = download_files(processfile, download_dir)

    print(f'-')

    show_result(dataframe, valid, fail, timer.elapsed())

    if preview:
        preview_result(dataframe, valid, resize=True)


def parse_arguments():

    parser = argparse.ArgumentParser(description='GK2A Satellite Data Downloader')

    parser.add_argument('-a', '--area', type=str, required=True,
                        default='fd',
                        help='Area of interest (e.g., fd, ea, ko)')
    parser.add_argument('-ch', '--channel', type=str, required=True,
                        default=None,
                        help='Specific channel to download')
    parser.add_argument('-x', '--extension', type=str,
                        default='.srv.png',
                        help='File extension of the images (e.g., srv.png, .png)')
    parser.add_argument('-s', '--start', type=str, required=True,
                        default='2025-07-01 12:00',
                        help='Start datetime for download ("YYYY-MM-DD hh:mm")')
    parser.add_argument('-e', '--end', type=str, required=True,
                        default='2025-07-01 23:50',
                        help='End datetime for download ("YYYY-MM-DD hh:mm")')
    parser.add_argument('-p', '--preview', action='store_true', default=False,
                        help='Enable preview of downloaded images')

    return parser.parse_args()


def main():

    args = parse_arguments()
    exec_gk2a(args.area, args.channel, args.extension,
              args.start, args.end,
              args.preview)

if __name__ == '__main__':
    main()