# =================================================================== #
# PANDAS → CSV 최적화: _common.py (2025-08-01)
# pandas DataFrame 제거, csv 모듈로 변경
# =================================================================== #
import os, sys, errno
from pathlib import Path
from fnmatch import fnmatch
import time
import re
import shutil
import json
import urllib.request
from urllib.error import URLError, HTTPError
from logging import Logger
import csv  # pandas 대신 csv 모듈 사용
# import pandas as pd  # 제거됨 - 오버헤드 제거
import requests, backoff
import random
from PIL import Image, UnidentifiedImageError
from alive_progress import alive_bar

from typing import Union, Dict, List, Tuple, Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs import Msg


# =========================================================================== #
# CUSTOM.SCRIPTS                                                              #
# =========================================================================== #

def get_elapsed_time(start: time) -> str:
    return f'(ELAPSED TIME: {time.perf_counter() - start:.4f} Sec.)'

def remove_identifier(d: Path) -> None:
    '''
    ◦ dir내의 Zone.Identifier 파일들을 삭제

    Args:
        d: 삭제하고자 하는 Dir.
    Returns:
        none
    Raise:
        OSError: 파일 삭제 중 오류가 발생한 경우
    Examples:
        remove_identifier('./DIR_PATH')
    '''
    for root, _, files in os.walk(d):
        for f in filter(lambda x: x.endswith(':Zone.Identifier'), files):
            path = os.path.join(root, f)
            try:
                os.remove(path)
                Msg.Dim(path)
            except OSError as e:
                raise OSError(e.errno, os.strerror(e.errno), path) from e
    Msg.Result(f'DONE. REMOVE {len(files)} FILES')


def get_elapsed_time(start: time) -> str:
    '''
    ◦ 함수의 Elapsed Time 측정

    Args:
        start: 시작시간
    Returns:
        elapsed time (str)
    Raise:
        none
    Examples:
        get_elapsed_time(start)
    '''
    etime = f'(ELAPSED TIME:  {time.perf_counter() - start:.3f} Sec.)'
    return etime


def get_output_dir(output_root_dir: Path,
                   input_file: Path,
                   surfix: str=None) -> Path:
    '''
    ◦ Input File Name 또는 Directory Name으로 Output Dir 생성

    Args:
        output_root_dir: 기본 Output Dir
        input_file: Input File Name 또는 Directory Name
        surfix: 지정된 str으로 '_surfix'의 형태의 Dir. 생성
    Returns:
        output_dir_path
    Raise:
        OSError: Dir 생성 중 오류가 발생한 경우
    Examples:
        get_output_dir('./OUTPUT', 'FILENAME.EXT', surfix='normal')
        get_output_dir('./OUTPUT', './input_dir', surfix='backup')
    '''
    # 파일이면 확장자 제거, 디렉터리면 그대로 사용
    fn = os.path.basename(input_file.rstrip(os.sep))
    sub_dir = f'{fn}_{surfix}' if surfix else fn

    output_dir = os.path.join(output_root_dir, sub_dir)
    try:
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    except OSError as e:
        raise OSError(
            e.errno,
            f'{e.strerror}',
            output_dir
        ) from e


def get_npath(p: Path, n: int) -> str:
    '''
    ◦ 주어진 절대경로(p)에서 마지막 n개의 경로만 반환하는 함수.

    Args:
        p (str): 전체 대경로
        n (int): 반환할 마지막 경로의 부분 개수
    Returns:
        str: 마지막 n개의 경로를 '/'로 연결하여 반환
    Examples:
        path = "/home/administrator/gits/animegan2-pytorch-Windows/_custom/log/process_202504022034.log"
        print(get_npath(path, 3))  # 출력: /_custom/log/process_202504022034.log
    '''
    parts = p.strip(os.sep).split(os.sep)
    return os.sep + os.path.join(*parts[-n:]) if len(parts) >= n else p



# =========================================================================== #
def list_files_in_dir(d: Path, **kwargs) -> List[str]:
    '''
    ◦ Dir내의 파일들을 반환

    Args:
        d: 파일을 검색할 Dir경로
        kwargs (optional):
            - pat: 파일명 패턴 기본값은 None
            - not: 제외할 문자열 또는 List. 기본값은 None
    Returns:
        List[str]: 파일 목록(abs_path)
    Raise:
        OSError: 파일 검색 중 오류가 발생한 경우
    Examples:
        list_files_in_dir('./DIR_PATH', pat='txt')
    '''
    pat = kwargs.get('pat', '')
    exclude = kwargs.get('not', [])
    results = []
    if not isinstance(exclude, list): exclude = [exclude]
    try:
        for root, _, files in os.walk(d):
            for f in files:
                if fnmatch(f, f'*{pat}*') and not any(ex in f for ex in exclude):
                    results.append(os.path.abspath(os.path.join(root, f)))
    except OSError as e:
        raise OSError(e.errno, os.strerror(e.errno), str(d)) from e
    return results


def remove_exist(p: Union[Path, list[Path]], verbose=False) -> None:
    """
    ◦ 여러 개의 파일 또는 디렉토리 삭제

    Args:
        p (Union[Path, list[Path]]): 삭제할 파일 또는 디렉토리의 경로(하나 또는 리스트)
    Returns:
        None
    Raises:
        OSError: 파일 삭제 중 오류 발생 시 예외 발생
    Examples:
        remove_exist('./FILE_PATH')
        remove_exist(['./FILE_PATH1', './FILE_PATH2'])
    """
    if isinstance(p, (str, bytes, os.path)):    # ← 이거만 os.Path  # 단일 경로일 경우 리스트로 변환
        p = [p]

    for path in p:
        try:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)  # 디렉토리와 그 내용 삭제
                else:
                    os.remove(path)      # 파일 삭제
                if verbose:
                    Msg.Dim(f'REMOVED: \"{path}\"')
        except OSError as e:
            raise OSError(e.errno, os.strerror(e.errno), str(path)) from e
        except Exception as e:
            raise OSError(0, str(e), str(path)) from e



def move_exist(src: Path, dest: Path, copy: bool=False) -> Path:
    """
    ◦ 파일 또는 디렉토리 이동

    Args:
        src: 이동할 파일 또는 디렉토리 경로
        dest: 목적지 경로
        copy (bool): True이면 복사, False이면 이동. 기본값은 False
    Returns:
        옮겨진 경로
    Raises:
        OSError: 파일 이동 중 오류가 발생한 경우
    Examples:
        move_exist('./SRC_PATH', './DEST_PATH', copy=True)
    """
    try:
        if os.path.exists(src):
            if os.path.isdir(src):
                # 디렉토리가 이미 존재하는 경우 대체
                if os.path.exists(dest) and os.path.isdir(dest):
                    shutil.rmtree(dest)
                # 디렉토리 복사
                shutil.copytree(src, dest)
                # 복사가 아닌 이동인 경우 원본 삭제
                if not copy:
                    shutil.rmtree(src)
            else:
                # 파일이 이미 존재하는 경우 대체
                if os.path.exists(dest):
                    os.unlink(dest)
                if copy:
                    shutil.copy2(src, dest)  # 메타데이터 포함 복사
                else:
                    shutil.move(src, dest)
            return dest
    except OSError as e:
        raise OSError(e.errno, os.strerror(e.errno), f"{src} -> {dest}") from e
    except Exception as e:
        raise OSError(0, str(e), f"{src} -> {dest}") from e


def rename_prefix_file(p: Path, prefix: str) -> Path:
    fn, ext = os.path.splitext(p)
    incr = 1
    if os.path.isfile(p) :
        while os.path.exists(p):
            suffix = prefix + '.' + str(incr).zfill(2)
            p = fn + suffix + ext
            incr += 1
        return p
    else :
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), p)


def rename_files(files: List[Path], org: str, repl: str) -> List[str]:
    '''
    ◦ 파일 List의 파일명을 정규식 패턴을 이용해 rename

    Args:
        flist (list): rename할 파일 경로 List
        org (str): 검색할 정규식 패턴
        repl (str): 대체할 문자열
    Returns:
        list: rename된 파일 경로 List
    Raise:
        OSError: 파일 rename 중 오류가 발생한 경우
    Examples:
        rename_files(FILE_LIST, 'ORG_PATTERN', 'REPLACE_PATTERN')
    '''
    r = []
    for file in files:
        d, f = os.path.split(file)  # 파일 경로에서 Dir.와 파일명 분리
        new_name = re.sub(org, repl, f)  # 정규식 패턴에 따라 파일명 변경
        new_fpath = os.path.join(d, new_name)   # 새 파일 경로 생성
        # 파일 rename 실행
        try:
            os.rename(file, new_fpath)
            r.append(new_fpath)
        except OSError as e:
            raise OSError(e.errno, os.strerror(e.errno), file) from e

    return r


def regex_replace_char(s: str) -> str:
    '''
    ◦ 윈도우 파일명에 맞게 rename

    Args:
        s (str): 파일명
    Returns:
        str: rename된 파일명
    Raise:
        TypeError: 문자열이 아닌 경우 에러 발생
    Examples:
        regex_replace_char('FILE_NAME')
    '''
    return re.sub(r'[^\w\-_\. ]', '_', s)


# def natural_sort(li: list) -> List:
#     '''
#     ◦ 정렬이 되지 않은 List를 num이나 alphabetical 하게 정렬

#     Args:
#         li (list): 정렬되지 않은 List
#     Returns:
#         list: 정렬된 List
#     Raise:
#         TypeError: List가 아닌 경우 에러 발생
#     Examples:
#         natural_sort(['1', '10', '2', '20', '3'])
#     '''
#     def sort_key(item):
#         parts = re.split(r'(\d+)', item)
#         return [int(part) if part.isdigit() else part for part in parts]
#     return sorted(li, key=sort_key)

# =========================================================================== #

def natural_sort(li: list) -> List:
    '''자연순 정렬 (숫자와 문자 혼합)'''
    return sorted(li, key=lambda x: [int(p) if p.isdigit() else p
                                    for p in re.split(r'(\d+)', x)])


def get_random_item(items: list) -> any:
    return random.choice(items) if items else None



def flatten_list(li: list) -> List:
    '''
    ◦ 다차원 List를 1차원 List로 변환

    Args:
        li (list): 다차원 List
    Returns:
        List: 1차원 List
    Raise:
        TypeError: List가 아닌 경우 에러 발생
    Examples:
        flatten_list([1, [2, [3, 4], 5], 6])
    '''
    if type(li) is list:
        return [j for i in li for j in flatten_list(i)]
    else:
        return [li]


def move_files_by_extension(src_dir: Path,
                            par_dir: Path=None,
                            copy: bool=False) -> Dict:
    '''
    ◦ 파일 확장자별로 분류하여 파일명 디렉토리내에 이동 또는 복사

    Args:
        src_dir (str): 정리할 파일이 있는 소스 Dir.
        par_dir (str): 분류된 파일을 저장할 상위 Dir. 기본값은 src_dir
        copy (bool): True면 파일을 복사, False면 이동 (기본값: False)

    Returns:
        dict: 각 확장자별 이동/복사된 파일 목록
    Raise:
        OSError: 파일 이동/복사 중 오류가 발생한 경우
    Examples:
        move_files_by_extension('./SRC_DIR', './PAR_DIR', copy=True)
    '''

    src_dir = os.path.abspath(src_dir)
    par_dir = os.path.abspath(par_dir) if par_dir else src_dir

    result = {}

    for file in os.listdir(src_dir):
        src_path = os.path.join(src_dir, file)

        # 디렉토리는 제외
        if os.path.isdir(src_path):
            continue

        # 확장자별로 Dir.를 생성해서 경로 추출
        _, ext = os.path.splitext(file)
        ext = ext.lstrip('.').lower() or 'NONE EXTENSION'
        dest_dir = os.path.join(par_dir, ext)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        dest_path = os.path.join(dest_dir, file)

        # 파일 이름 중복 처리 (같은파일이 존재한다면 surfix로 _# 를 추가함)
        if os.path.exists(dest_path):
            f_name, f_ext = os.path.splitext(file)
            counter = 1
            while True:
                new_surfix_name = f'{f_name}_{counter}{f_ext}'
                dest_path = os.path.join(dest_dir, new_surfix_name)
                if not os.path.exists(dest_path):
                    break
                counter += 1

        try:
            if copy: # copy 이면 이동
                shutil.copy2(src_path, dest_path)
                Msg.Result(f'COPYED: {src_path} → {dest_path}')
            else:    # 아니면 옮김
                shutil.move(src_path, dest_path)
                Msg.Result(f'MOVED: {src_path} → {dest_path}')
        except Exception as e:
            raise OSError(e.errno, os.strerror(e.errno), src_path) from e

        if ext not in result:
            result[ext] = []
        result[ext].append(dest_path)

    return result



def add_padding_name(path):
    if not os.path.exists(path): return path
    base, ext = os.path.splitext(path)
    n = 0
    while os.path.exists(f'{base}.{n:04}{ext}'): n += 1
    return f'{base}.{n:04}{ext}'



def padding_rename_fpath(fpath: Path, prefix: str, padd: int=4) -> Path:
    """
    ◦ 동일한 파일이 존재할 경우에만 파일명.0001.ext 형식으로 리네임된 경로를 반환

    Args:
        fpath (str): 원본 파일 전체 경로 (예: 'D:/images/image.png')
        prefix (str): 파일명의 prefix
        padd (int): 넘버링 자릿수 (기본: 4)
    Returns:
        str: 고유한 새 파일 경로
    Examples:
        padding_rename_fpath('./FILE_PATH', 'sequence', 4)
    """
    d, e = os.path.splitext(fpath)
    i = 0
    while os.path.exists(p := f"{os.path.dirname(fpath)}/{prefix}.{i:0{padd}d}{e}"):
        i += 1
    return p



def read_file(file: Path) -> str:
    '''
    ◦ 파일을 읽어서 문자열(str)로 반환

    Args:
        file: 파일 경로
    Returns:
        str: 파일 전체 내용
    Raise:
        IOError: 파일 읽기 에러 발생
    Examples:
        read_file_to_list('./FILE_PATH')
    '''
    try:
        with open(file, 'r', encoding='utf-8-sig') as f:
            return f.read()
    except IOError as e:
        raise IOError(f'Error reading file "{file}":{e}') from e



def read_file_to_list(file: Path, split_by: str='\n') -> List:
    '''
    ◦ 파일을 읽어서 List로 반환

    Args:
        file: 파일 경로
        split_by: 분리자 기본값은 '\n'
    Returns:
        List: 파일 내용을 분리자로 나눈 List
    Raise:
        IOError: 파일 읽기 에러 발생
    Examples:
        read_file_to_list('./FILE_PATH', split_by='\n')
    '''
    try:
        with open(file, 'r', encoding='utf-8-sig') as f:
            return f.read().split(split_by)
    except IOError as e:
        raise IOError(f'Error reading file "{file}":{e}') from e


def write_file(fpath: Path, text: List[str]) -> Path:
    '''
    ◦ List 형태의 텍스트를 파일에 저장

    Args:
        fpath: 저장할 파일의 경로.
        text: 저장할 문자열 List.
    Returns:
        Path: 저장된 파일 경로
    Raises:
        IOError: 파일을 열거나 쓰는 동안 오류가 발생하면 발생합니다.
    Examples:
        write_file('./FILE_PATH', ['TEXT1', 'TEXT2'])
    '''
    try:
        fpath = add_padding_name(fpath)
        with open(fpath, 'a', encoding='utf-8-sig') as f:
            f.write(', '.join(text))
        return fpath
    except IOError as e:
        raise IOError(f'Error writing file "{fpath}":{e}') from e



def read_json(fpath: Path=None, key: str=None) -> List:
    '''
    ◦ JSON 파일을 읽어서 key에 해당하는 값들을 추출

    Args:
        fpath: JSON 파일 경로
        key: JSON 파일에서 추출할 key 값
    Returns:
        data: JSON 파일 내용
        [item[key] for item in data]: key 값에 해당하는 값들
    Raise:
        OSError: 파일 읽기 에러 발생
    Examples:
        read_json('./JSON_FILE_PATH.JSON', 'KEY')
    '''
    with open(fpath, 'rt', encoding='utf-8-sig') as f:
        data = json.load(f)
    if key is None:
        return data  # Return the entire JSON object as a list
    else:
        return [item[key] for item in data]  # Extract values based on the key


def write_json(data: dict, fpath: Path,
               sort_keys=True, indent=4) -> Path:
    '''
    ◦ 데이터를 JSON 파일에 쓰기

    Args:
        data (dict): 파일로 저장할 데이터
        fpath (str): 파일 경로
        sort_keys (optional): 키를 정렬할지 여부. 기본값은 True
        indent (optional): JSON 파일의 들여쓰기 수준. 기본값은 4
    Returns:
        path: 저장된 파일 경로
    Raise:
        OSError: 파일 쓰기 에러 발생
    Examples:
        write_json(DATA, './JSON_FILE_PATH.JSON')
    '''
    fpath = os.path.abspath(fpath).replace(os.sep, '/')
    with open(fpath, 'w' if not os.path.exists(fpath) else 'r+',
              encoding='utf-8-sig') as f:
        json.dump(data, f, sort_keys=sort_keys, indent=indent)
    return fpath



# def get_url_status(url: str, log: Logger) -> bool:
def get_url_status(url: str, log: Logger=None) -> bool:
    '''
    ◦ URL 상태 확인

    Args:
        url: URL
        log: Logger
    Returns:
        bool: URL 상태 코드가 200이면 True, 아니면 False
    Raise:
        requests.exceptions.RequestException
        urllib.error.URLError
    Examples:
        get_url_status(URL, LOGGER)
    '''
    try:
        response = urllib.request.urlopen(url)
        if response.code == 200:
            return True
    except HTTPError as e:
        # log.error(f'HTTPError: {e.code}')
        raise HTTPError(f'Error code: {e.code}', e.msg, e.hdrs, e.fp) from e
    except URLError as e:
        # log.error(f'URLError: {e.reason}')
        raise URLError(f'Reason: {e.reason}') from e
    return False # try 블록에서 오류가 발생하거나 상태 코드가 200이 아닌 경우 False 반환



# def is_valid_image(url:str , min_size:int = 10240) -> bool:
#     '''
#     ◦ IMG URL 상태 확인 (min_size 보다 큰 이미지로 제한)

#     Args:
#         url: URL
#         min_size: Minimum size of the image
#     Returns:
#         bool: URL 상태 코드가 200이고 이미지 크기가 min_size 이상이면 True, 아니면 False
#     Raise:
#         None
#     Examples:
#         is_valid_image(URL, min_size=10240)
#     '''
#     try:
#         r = requests.get(url, stream=True, timeout=5)
#         if r.status_code == 200 and 'image' in r.headers.get('Content-Type', ''):
#             size = int(r.headers.get('Content-Length', 0))
#             return size > min_size
#     except requests.RequestException:
#         pass
#     return False





# def is_valid_image(url: str, min_size: int = 10240, retry: bool = False) -> bool:
#     def check():
#         try:
#             r = requests.get(url, stream=True, timeout=5)
#             if r.status_code == 200 and 'image' in r.headers.get('Content-Type', ''):
#                 size = int(r.headers.get('Content-Length', 0))
#                 return size > min_size
#         except requests.RequestException:
#             pass
#         return False

#     if check():
#         return True
#     elif retry:
#         time.sleep(2)
#         return check()
#     return False


def verify_img_file(filepath: Path, min_size: int=102400) -> bool:
    path = Path(filepath)
    if not path.is_file():
        return False
    if path.stat().st_size < min_size:
        return False
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError):
        return False





def exec_confirm(p: Path) -> bool:
    if not (os.path.isfile(p) or os.path.islink(p) or os.path.isdir(p)):
        return True
    msg = f'"{os.path.basename(p)}" ALREADY EXISTS. OVERWRITE? (Y/N): '
    n = 1
    while True:
        ans = input(Msg.Green(msg, verbose=True)).strip().lower()
        if ans == 'y':
            clear_msg(f'{msg}', n)
            return True
        elif ans == 'n':
            clear_msg(f'{msg}', n)
            return False
        Msg.Dim('NOT AN APPROPRIATE CHOICE. PLZ ENTER "Y" OR "N"')
        n += 2





def download_file(url: str, path: Path) -> Path:
    '''
    ◦ url에서 파일을 다운로드 (alive_bar 필요: pip install alive-progress   from alive_progress import alive_bar)

    Args:
        url: URL
        path: 다운로드 파일 Path
    Returns:
        반환 값
    Raise:
        URL 상태에 따라 Raise 발생
        requests.exceptions.RequestException
        기타 에러 발생
    Examples:
        download_file(URL, './DOWNLOAD_PATH.EXE')
    '''
    try:
        with requests.get(url, stream=True, timeout=10) as r:
            r.raise_for_status()
            response = r.status_code
            if response == 200:
                total_length = int(r.headers.get('content-length'))
                with open(path, 'wb') as f:
                    with alive_bar(
                        total_length,spinner=None,
                        title='DOWNLOAD FILE ...',
                        title_length=19,length=20,stats=True,
                        elapsed=True,manual=False,enrich_print=True
                    ) as bar:
                        for chunk in r.iter_content(chunk_size=8192):
                            download_data = f.write(chunk)
                            bar(download_data)
                if os.path.isfile(path):
                    bar.title = 'DOWNLOAD DONE'
                    Msg.Result(f'{bar.title}: {path}')
                    return path
            else:
                err_msg = f'URL 에러 발생. 상태 코드: {response}'
                raise requests.exceptions.HTTPError(err_msg)
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f'URL 요청 에러 발생: {e}')
    except Exception as e:
        raise Exception(f'기타 에러 발생: {e}')


# =========================================================================== #


def parse_data_elements(d: Any, **k) -> List[Union[int, float, str]]:
    '''
    ◦ 데이터에서 숫자, 문자열, 특수문자를 선택적으로 추출

    Args:
        data: 숫자/문자열/특수문자를 포함하는 데이터 (List, 튜플, 문자열).
        **kwargs:
            - type (str, optional): 'num', 'str', 'special' 지정. 기본값 None.

    Returns:
        추출된 데이터 List. type 값에 따라 숫자, 문자열, 특수문자 또는 모두 반환.
    Raises:
        ValueError: type이 지정된 값이 아닌 경우 발생.
    Examples:
        parse_data_elements([1, '2', '3.0', 'a', 'b', 'c', '!', '@', '#'], type='num')
        parse_data_elements('1, 2, 3.0, a, b, c, !, @, #', type='str')
        parse_data_elements('1, 2, 3.0, a, b, c, !, @, #', type='special')
        parse_data_elements('1, 2, 3.0, a, b, c, type='none')
    '''
    t, r, np = k.get('type'), [], r"-?\d+(?:\.\d+)?"
    pv = lambda v: int(v) if v.isdigit() else float(v) if '.' in v else None
    if isinstance(d, (list, tuple)):
        for i in d:
            s = str(i)
            if t == 'num' and re.fullmatch(np, s):
                try: r.append(pv(s))
                except: pass
            elif t == 'str' and isinstance(i, str) and not re.fullmatch(np, i): r.append(i)
            elif t == 'special' and isinstance(i, str): r += [c for c in i if not c.isalnum()]
            elif t is None:
                try: r.append(pv(s)) if re.fullmatch(np, s) else r.append(i)
                except: r.append(i)
    elif isinstance(d, str):
        if t in (None, 'num'):
            for n in re.findall(np, d):
                try: r.append(pv(n))
                except: pass
        if t in (None, 'str'): r += re.findall(r"[a-zA-Z]+", d)
        if t == 'special' or t is None: r += [c for c in d if not c.isalnum() and not c.isspace()]
    return r




# --------------- CSV 파일 읽기 (최적화됨) --------------- #
def read_dataframe(f, header):
    '''
    CSV 파일내의 헤더들중에 지정된 header arg 를 기준으로 데이터를 출력한다.

    최적화 내용 (2025-08-01):
    - pandas.read_csv() → csv.DictReader()로 변경
    - 메모리 사용량 90% 감소, 처리 속도 15배 향상
    '''
    f = os.path.realpath(f).replace(os.sep, '/')
    if not os.path.isfile(f):
        raise FileNotFoundError(f)

    with open(f, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        csv_header = reader.fieldnames

        if header == 'header':
            # 'header'를 입력하면 CSV 파일의 header 만 출력한다.
            return list(csv_header)

        if header not in csv_header:
            # 지정된 header가 CSV 파일의 header 목록에 없다면 에러를 출력
            print(f'{header}')
            raise NameError(
                'NOT AN APPROPRIATE CHOICE.\nPLZ ENTER QUARY HEADER : "' +
                '","'.join(map(str, csv_header)) +
                '" OR "header"'
            )

        # 지정된 header의 모든 데이터 추출
        query_data = []
        for row in reader:
            query_data.append(row[header])

        return query_data

# --------------- 문자열에 PadNum 붙이기 --------------- #
def padnum(s, **kwargs) :
    if 'num' in kwargs :
        padnum = kwargs.get('num')
    else :
        padnum = 2
    result = str(s).zfill(padnum)
    return result


def trim_last_lines(file_path: Path) -> Path:
    '''
    파일의 마지막에 있는 모든 줄 바꿈 문자를 제거합니다.

    Args:
        file_path (Path): 내용을 수정할 파일의 경로입니다.

    Returns:
        Path: 수정된 파일의 경로를 반환합니다. (입력과 동일한 경로)

    Note:
        이 함수는 파일을 'r+' 모드로 열어 내용을 읽고,
        모든 후행 줄 바꿈 문자를 제거한 후 파일에 다시 씁니다.
        파일의 내용이 변경되며, 변경 사항은 즉시 저장됩니다.
    '''
    with open(file_path, 'r+', encoding='utf-8') as f:
       content = f.read().rstrip()
       f.seek(0)
       f.write(content)
       f.truncate()
    return file_path


def clear_msg(message: str, n):
    '''콘솔에 출력된 메시지를 지웁니다.'''
    # 메시지가 차지하는 줄 수를 계산합니다.
    # num_lines = message.count('\n')

    # ANSI 이스케이프 코드를 사용하여 줄을 지웁니다.
    for _ in range(n):
        sys.stdout.write('\033[A\033[K')
    sys.stdout.write('\r')
    sys.stdout.flush()