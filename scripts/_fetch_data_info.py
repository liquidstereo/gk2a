import os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._data_map import LEVEL1B_MAP, LEVEL2_MAP


def _validate_or_default(value: str, valid_options: list[str]) -> str:
    return value if value in valid_options else valid_options[0]

# =========================================================================== #

def _remap_resolution(area: str, ch: str, resolution: str) -> str:

    hires_channels = {
        'tpw-um',
        'aii-ki-um', 'aii-li-um', 'aii-ssi-um', 'aii-tti-um', 'aii-cape-um',
        'tqprof-t300hpa-um', 'tqprof-t500hpa-um', 'tqprof-t850hpa-um',
        'tqprof-q300hpa-um', 'tqprof-q500hpa-um', 'tqprof-q850hpa-um'
    }
    if ch in hires_channels and area != 'ko' and resolution == '020':
        return '060'
    if ch == 'toz' and area == 'ko' and resolution == '060':
        return '020'
    return resolution


def _remap_proj(area: str, resolution: str) -> str:

    if resolution == 'zzz':
        return 'll'
    return 'ge' if area == 'fd' else 'lc'


def remap_timecode(timecode: str, fix: bool) -> str:
    return f'{timecode[:8]}0000' if fix else timecode


def generate_url(
    satellite: str, sensor: str, level: str, cat: str, ch: str, area: str,
    resolution: str, proj: str, year: str, month: str, day: str, hour: str,
    timecode: str, ext: str) -> str:

    LEVEL_MAPPING = {'LE2': 'L2', 'LE3': 'L3', 'LE4': 'L4', 'LE1B': 'L1B'}

    url_level = LEVEL_MAPPING.get(level, level)

    base_filename = f'{satellite}_{sensor}_{level}_{ch}_{area}{resolution}{proj}_{timecode}'.lower()

    if level == 'LE1B':
        url_base = (
            f'https://nmsc.kma.go.kr/IMG/{satellite}/{sensor}/PRIMARY/{url_level}/'
            f'COMPLETE/{area.upper()}/{year}{month}/{day}/{hour}'
        )
    else:
        url_base = (
            f'https://nmsc.kma.go.kr/IMG/{satellite}/{sensor}/{url_level}/'
            f'{cat}/{area.upper()}/{year}{month}/{day}/{hour}'
        )

    return f'{url_base}/{base_filename}{ext}'


def fetch_data_info(ch: str, area: str, ext: str) -> dict:

    merged_map = {**LEVEL1B_MAP, **LEVEL2_MAP}
    if ch not in merged_map:
        raise ValueError(f'Invalid channel name: "{ch}"')

    data = merged_map[ch]

    valid_area = _validate_or_default(area, data['area'])
    remapped_res = _remap_resolution(valid_area, ch, data['resolution'])
    remapped_proj = _remap_proj(valid_area, remapped_res)
    valid_ext = _validate_or_default(ext, data['ext'])

    return {
        'satellite': 'GK2A',
        'sensor': 'AMI',
        'level': data['level'],
        'cat': data['cat'],
        'ch': data['cat_ch'],
        'resolution': remapped_res,
        'area': valid_area,
        'proj': remapped_proj,
        'ext': valid_ext,
        'fix': data['fix']
    }


def main():

    return None

if __name__ == '__main__':
    main()