# import datetime
from datetime import datetime, timedelta, timezone
import re
from typing import List, Literal, Union


def validate_time_schedule(start: str, end: str) -> tuple[datetime, datetime]:

    try:
        start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
        end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M')
    except ValueError as e:
        raise ValueError(f'Invalid date format: {e}')

    if start_dt.minute % 10 != 0:
        raise ValueError(f'Start time minute must be in 10-minute units: "{start}"')

    if end_dt.minute % 10 != 0:
        raise ValueError(f'End time minute must be in 10-minute units: "{end}"')

    if end_dt <= start_dt:
        raise ValueError(f'End time ({end}) must be after start time ({start})')

    return start_dt, end_dt



def str_to_dt(start: str, end: str) -> dict[str, int]:

    start_dt, end_dt = validate_time_schedule(start, end)
    duration = get_duration(start, end)

    return {
        'year': start_dt.year,
        'month': start_dt.month,
        'day': start_dt.day,
        'hour': start_dt.hour,
        'minute': start_dt.minute,
        'duration': duration
    }


def str_to_timecode(time_str: str, as_str: bool = False):

    supported_formats = ['%Y-%m-%d %H:%M', '%Y%m%d%H%M', '%Y_%m_%d_%H_%M']

    for fmt in supported_formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.strftime('%Y-%m-%d %H:%M') if as_str else dt
        except ValueError:
            continue

    e = (f'Invalid datetime format: {time_str}. '
         f'Supported formats: {", ".join(supported_formats)}')

    raise ValueError(e)



def dt_to_str(dt: Union[datetime, str], fmt: str=None) -> str:

    if isinstance(dt, datetime):
        return dt.strftime('%Y%m%d%H%M')
    elif isinstance(dt, str):
        try:
            parsed_dt = datetime.strptime(dt, '%Y-%m-%d %H:%M')
            result = parsed_dt.strftime('%Y%m%d%H%M')
            # fmt 값이 지정된 경우 구분자 변환
            if fmt is not None:
                return re.sub(r'[-: ]', fmt, result).lower()
            return result
        except ValueError:
            raise ValueError('The format must be "YYYY-MM-DD HH:MM".')
    else:
        e = (f'Only datetime objects or strings in '
             f'"YYYY-MM-DD HH:MM" format are supported.')
        raise ValueError(e)



def get_duration(start: str, end: str) -> int:

    fmt = '%Y-%m-%d %H:%M'
    start_dt = datetime.strptime(start, fmt)
    end_dt = datetime.strptime(end, fmt)
    duration_minutes = int((end_dt - start_dt).total_seconds() // 60)

    return duration_minutes


def local_to_utc(local_time: str, fmt='_') -> str:

    local_tz = datetime.now().astimezone().tzinfo
    local_dt = datetime.strptime(local_time, '%Y%m%d%H%M').replace(tzinfo=local_tz)
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt.strftime('%Y_%m_%d_%H_%M') if fmt == '_' else utc_dt.strftime('%Y%m%d%H%M')


def utc_to_local(utc_time: str, fmt='_') -> str:

    local_tz = datetime.now().astimezone().tzinfo
    utc_dt = datetime.strptime(utc_time, '%Y%m%d%H%M').replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(local_tz)
    return local_dt.strftime('%Y_%m_%d_%H_%M') if fmt == '_' else local_dt.strftime('%Y%m%d%H%M')


def shift_timezone(time_str: str, dest: Literal['utc', 'local'], fmt='_') -> str:

    local_tz = datetime.now().astimezone().tzinfo
    src_tz = local_tz if dest == 'utc' else timezone.utc
    dst_tz = timezone.utc if dest == 'utc' else local_tz
    dt = datetime.strptime(time_str, '%Y%m%d%H%M').replace(tzinfo=src_tz)
    converted_dt = dt.astimezone(dst_tz)
    return converted_dt.strftime('%Y_%m_%d_%H_%M' if fmt == '_' else '%Y%m%d%H%M')


def generate_datatimes(year: int, month: int, day: int,
                       hour: int = None, minute: int = None,
                       duration: int = 1440,
                       interval: int = 10,  # ← 10-minute units
                       timezone: Literal['local', 'utc'] = 'local',
                       return_format: Literal['timestamps', 'formatted'] = 'timestamps'
                       ) -> Union[List[datetime], str]:


    base_datetime = datetime(year, month, day, hour or 0, minute or 0)

    if timezone == 'utc':
        local_str = base_datetime.strftime('%Y%m%d%H%M')
        utc_str = local_to_utc(local_str, fmt='')
        base_datetime = datetime.strptime(utc_str, '%Y%m%d%H%M')

    if return_format == 'formatted':
        if hour is not None and minute is not None:
            return base_datetime.strftime('%d %b %Y %H:%M')
        else:
            return base_datetime.strftime('%d %b %Y')

    elif return_format == 'timestamps':
        return [
            base_datetime + timedelta(minutes=m)
            for m in range(0, duration, interval)   # ← 10-minute units
        ]

    else:
        e = f'Return format must be "timestamps" or "formatted".'
        raise ValueError(e)




def get_time_schedule(start: str, end: str, interval: int=10):


    time_info = str_to_dt(start, end)

    utc_schedule = generate_datatimes(
        time_info['year'], time_info['month'], time_info['day'],
        time_info['hour'], time_info['minute'], time_info['duration'], interval,
        timezone='utc', return_format='timestamps'
    )

    local_schedule = generate_datatimes(
        time_info['year'], time_info['month'], time_info['day'],
        time_info['hour'], time_info['minute'], time_info['duration'], interval,
        timezone='local', return_format='timestamps'
    )

    return {
        'utc': utc_schedule,
        'local': local_schedule
    }


def main():
    utc_times = generate_datatimes(2024, 1, 15, 0, 0, 1440, 10, 'utc', 'timestamps')
    print(f"count: {len(utc_times)}")

if __name__ == "__main__":
    main()