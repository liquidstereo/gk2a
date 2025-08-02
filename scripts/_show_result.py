import os
from tabulate import tabulate
import wcwidth
from typing import List, Dict, Any

from configs import Msg

# TODO 📌: AWAITING REFACTORING.

def pad_str_width(s: str, width: int, fillchar: str=' ') -> str:

    ellipsis = '⋯'
    ellipsis_width = wcwidth.wcswidth(ellipsis)

    current_width = wcwidth.wcswidth(s)
    if current_width == -1:  # Handle unprintable characters
        return s.ljust(width, fillchar)

    if current_width > width:
        truncated_s = s
        target_content_width = width - ellipsis_width

        if target_content_width < 0:
            return ellipsis[:width] if width >= ellipsis_width else ellipsis[:width]

        while wcwidth.wcswidth(truncated_s) > target_content_width and len(truncated_s) > 0:
            truncated_s = truncated_s[:-1]
        return truncated_s + ellipsis
    else:
        return s + fillchar * (width - current_width)



def show_result(data: List[Dict[str, Any]],
                success_count: int,
                error_count: int,
                elapsed: str) -> None:

    DEFAULT_WIDTH = 10    # ← DEFAULT CELL WIDTH

    first_row = data[0] if data else {}

    channel = (f'{first_row.get("satellite", "")}_'
               f'{first_row.get("sensor", "")}_'
               f'{first_row.get("channel", "")}_'
               f'{first_row.get("area", "")}_'
               f'{first_row.get("category", "")}_'
               f'{first_row.get("channel", "")}').upper()

    download_dir = first_row.get('download_path', '')
    if download_dir:
        download_dir = os.path.dirname(download_dir)


    col01_offset = 20   # DATA
    col02_offset = -3   # RESULTS
    col03_offset = -3   # FAILURE
    col04_offset = 3    # ELAPSED.TIME

    header_list = [pad_str_width('DATA', DEFAULT_WIDTH+col01_offset),
                   pad_str_width('RESULTS', DEFAULT_WIDTH+col02_offset),
                   pad_str_width('FAILURE', DEFAULT_WIDTH+col03_offset),
                   pad_str_width('ELAPSED.TIME', DEFAULT_WIDTH+col04_offset)]    # ← HEADERs
    table = [[pad_str_width(channel, DEFAULT_WIDTH+col01_offset),
              pad_str_width(f'{success_count}', DEFAULT_WIDTH+col02_offset),
              pad_str_width(f'{error_count}', DEFAULT_WIDTH+col03_offset),
              pad_str_width(elapsed, DEFAULT_WIDTH+col04_offset)]]

    print(tabulate(table,
                   headers=header_list,
                   intfmt=',',
                   tablefmt='outline',
                   stralign='left',
                   numalign='left',
                   disable_numparse=True))

    print(f'-')
    m = (f'DOWNLOAD FILES COMPLETED. '
         f'(RESULT DIR. "./{os.path.relpath(download_dir)}")')
    Msg.Result(m, divide=False)
    Msg.Dim('FOR MORE DETAILS, CHECK THE LOG FILE IN THE RESULT DIR.')
    print(f'-')
    return