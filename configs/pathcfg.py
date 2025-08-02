"""
configs/pathcfg.py

이 모듈은 프로젝트의 작업 디렉토리 경로를 관리하기 위한 WorkDirs 클래스와
관련 유틸리티 함수를 제공합니다.

주요 기능:
- 프로젝트 루트 디렉토리를 기준으로 동적으로 경로를 설정하고 관리합니다.
- 요청 시 디렉토리를 자동으로 생성하여 경로 설정의 번거로움을 줄입니다.
- `WorkDirs.add()` 메서드를 통해 런타임에 새로운 디렉토리 경로를 추가할 수 있습니다.
- `WorkDirs.make()` 메서드를 통해 기본 디렉토리들을 일괄 생성할 수 있습니다.
"""
import os, errno
from pathlib import Path
import shutil
from datetime import datetime
from typing import Union, Optional, Callable, Dict, List

class WorkDirConfigs:

    '''작업 디렉토리 경로 관리 클래스: Working directory path management class'''

    # 모든 디렉토리 생성
    # paths = WorkDirs.init()

    # # 특정 디렉토리만 생성
    # paths = WorkDirs.init(['logs', 'data', 'results'])
    # paths = WorkDirs.init('logs, data, results')
    # paths = WorkDirs.init('logs')

    # # 경로만 조회 (생성하지 않음)
    # log_path = WorkDirs.get_paths('logs')  # 단일 경로 문자열 반환
    # paths = WorkDirs.get_paths(['logs', 'data'])  # 딕셔너리 반환

    # # 사용 가능한 디렉토리 목록 확인
    # available = WorkDirs.list_available_dirs()


    def __init__(self, root: Optional[Path] = None):
        '''루트 경로 및 하위 경로 키 설정: Set root path and sub-path keys.'''
        self.root = Path(root or Path(__file__).parent.parent).resolve()
        self._paths = {
            'data_dir':     'data',
            'download_dir': 'downloads',
            'input_dir':    'input',
            'output_dir':   'output',
            'result_dir':   'results',
            'temp_dir':     'temp',
            'log_dir':      'logs',
            'error_dir':    'errors',
            'backup_dir':   'backup',
            'test_dir':     'test'
        }

    def __str__(self) -> str:
        '''모든 경로 딕셔너리 출력: Return a string representation of all path dictionaries.'''
        return str({
            'root_dir': str(self.root),
            **{k: str(self.root / v) for k, v in self._paths.items()}
        })

    def _resolve(self, sub: str) -> Path:
        '''루트와 결합된 절대경로 Path 객체 반환 및 생성: Return an absolute path Path object and create it if it doesn't exist.'''
        path = self.root / sub
        path.mkdir(parents=True, exist_ok=True)
        return path.resolve()


    def init(self, *dirs) -> Union[Dict[str, str], List[str], str]:
        '''기본 디렉토리들을 자동으로 생성하고 경로를 반환합니다: Automatically creates default directories and returns their paths.

        Args:
            *dirs (str): 생성할 디렉토리 이름들.
                - 인자 없음: 모든 디렉토리 생성 후 딕셔너리 반환.
                - 여러 문자열 인자 (e.g., 'data', 'logs'): 여러 디렉토리 생성 후 경로 리스트 반환.
                - 단일 문자열 인자 (e.g., 'data,logs'): 쉼표로 구분된 디렉토리 생성 후 경로 리스트 반환.
                - 리스트 인자 (e.g., ['data', 'logs']): 리스트에 포함된 디렉토리 생성 후 경로 리스트 반환.
                - 단일 디렉토리 인자 (e.g., 'data'): 단일 디렉토리 생성 후 경로 문자열 반환.
                Available directory names: data, downloads, input, output, temp, logs, errors, results, backup, test

        Returns:
            Union[Dict[str, str], List[str], str]: 생성된 디렉토리 경로들 (단일: 문자열, 여러개: 리스트, 인자 없음: 딕셔너리)
        '''
        created_paths = {}

        if not dirs:
            # 매개변수가 없으면 모든 self._paths 디렉토리 생성
            for key, dir_name in self._paths.items():
                created_path = self._resolve(dir_name)
                created_paths[dir_name] = str(created_path)
                # print(f'Directory "{dir_name}" created at: "{created_path}"')
            return created_paths

        dir_names = []
        # 다양한 입력 형식 처리 (가변 인자, 리스트, 쉼표로 구분된 문자열)
        if len(dirs) == 1:
            if isinstance(dirs[0], list):
                dir_names = dirs[0]
            elif isinstance(dirs[0], str):
                dir_names = [name.strip() for name in dirs[0].split(',')]

        if not dir_names:
            dir_names = list(dirs)

        # 각 디렉토리 이름에 대해 처리
        for dir_name in dir_names:
            if not isinstance(dir_name, str):
                print(f'Warning: Directory name must be a string, but got {type(dir_name)}.')
                continue

            found_key = any(value == dir_name for value in self._paths.values())

            if found_key:
                # 디렉토리 생성 및 경로 저장
                created_path = self._resolve(dir_name)
                created_paths[dir_name] = str(created_path)
                # print(f'Directory "{dir_name}" created at: "{created_path}"')
            else:
                print(f'Warning: Directory name "{dir_name}" not found in predefined paths.')

        # 요청된 디렉토리 수에 따라 반환 유형 결정
        if len(dir_names) == 1:
            # 단일 디렉토리면 문자열 반환
            return created_paths.get(dir_names[0])

        # 여러 디렉토리를 지정한 경우, 순서대로 리스트 반환
        ordered_paths = []
        for dir_name in dir_names:
            if dir_name in created_paths:
                ordered_paths.append(created_paths[dir_name])
        return ordered_paths


    def add(self, d: str, role: Optional[str] = None) -> str:
        '''지정된 키로 디렉토리를 생성하고 경로를 설정 및 출력합니다: Creates a directory with the specified key, then sets and prints its path.'''
        # role이 지정되면 해당 키 사용, 아니면 기본값
        key = role if role else f'{d}_dir'

        self._paths[key] = d
        created_path = self._resolve(d)
        print(f'Directory "{d}" created at: "{created_path}"')
        return str(created_path)


    def make(self, dir_name: str) -> str:
       '''지정된 디렉토리를 생성하고 절대경로를 반환합니다: Create specified directory and return absolute path.'''
       created_path = self._resolve(dir_name)
       return str(created_path)


    def remove(self, dir_name: str) -> bool:
        '''디렉토리를 완전히 삭제합니다: Completely remove directory.'''

        for key, value in self._paths.items():
            if value == dir_name:
                dir_path = self.root / dir_name
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    print(f'Directory "{dir_name}" removed from: "{dir_path}"')
                    return True
                else:
                    print(f'Directory "{dir_name}" does not exist.')
                    return False
        raise ValueError(f'Directory name "{dir_name}" not found in predefined paths.')


    def exists(self, dir_name: str) -> bool:
       '''디렉토리 존재 여부를 확인합니다: Check if directory exists.'''
       for key, value in self._paths.items():
           if value == dir_name:
               return (self.root / dir_name).exists()
       raise ValueError(f'Directory name "{dir_name}" not found in predefined paths.')


    def clean(self, dir_name: str) -> bool:
        '''디렉토리 내용물을 삭제합니다 (디렉토리는 유지): Clean directory contents while keeping the directory.'''
        import shutil

        for key, value in self._paths.items():
            if value == dir_name:
                dir_path = self.root / dir_name
                if dir_path.exists():
                    for item in dir_path.iterdir():
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                    print(f'Directory "{dir_name}" contents cleaned at: "{dir_path}"')
                    return True
                else:
                    print(f'Directory "{dir_name}" does not exist.')
                    return False
        raise ValueError(f'Directory name "{dir_name}" not found in predefined paths.')


    def backup(self, src: str, dst: Optional[str] = None) -> str:
        '''디렉토리를 백업/복사합니다: Backup/copy directory.

        WorkDirs.backup('logs')  # logs_backup_20250726_143022 형태로 자동 생성
        WorkDirs.backup('logs', 'logs_old')  # 직접 백업명 지정

        '''
        # src 경로 확인
        src_path = self.root / src
        if not src_path.exists():
            raise FileNotFoundError(f'Source directory "{src}" does not exist.')

        # dst가 없으면 timestamp로 백업명 생성
        if dst is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dst = f"{src}_backup_{timestamp}"

        dst_path = self.root / dst
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        print(f'Directory "{src}" backed up to: "{dst_path}"')
        return str(dst_path)


    def tree(self, dir_name: Optional[str] = None, max_depth: int = 3) -> None:
        '''디렉토리 구조를 트리 형태로 출력합니다: Display directory structure as tree.'''
        def _print_tree(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return

            if not path.exists():
                return

            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item.name}")

                if item.is_dir() and depth < max_depth:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    _print_tree(item, next_prefix, depth + 1)

        if dir_name is None:
            print(f"📁 {self.root.name}/")
            _print_tree(self.root)
        else:
            for key, value in self._paths.items():
                if value == dir_name:
                    dir_path = self.root / dir_name
                    if dir_path.exists():
                        print(f"📁 {dir_name}/")
                        _print_tree(dir_path)
                    else:
                        raise OSError(
                            errno.ENOENT, os.strerror(errno.ENOENT), dir_name)
                    return
            raise ValueError(f'Directory name "{dir_name}" not found in predefined paths.')


    def get_paths(self, dirs: Optional[Union[str, List[str]]] = None) -> Union[Dict[str, str], str]:
            '''디렉토리 경로들을 반환합니다 (생성하지 않음): Returns directory paths without creating them.

            Args:
                dirs (Optional[Union[str, List[str]]]): 경로를 가져올 디렉토리 이름들
                    - None: 모든 경로 반환
                    - str: 단일 디렉토리 이름 또는 쉼표로 구분된 이름들
                    - List[str]: 디렉토리 이름 리스트

            Returns:
                Union[Dict[str, str], str]: 디렉토리 경로들 (단일 경로인 경우 문자열, 여러 경로인 경우 딕셔너리)
            '''
            if dirs is None:
                # 모든 경로 반환
                return {dir_name: str(self.root / dir_name) for dir_name in self._paths.values()}

            # 문자열인 경우 파싱
            if isinstance(dirs, str):
                if ',' in dirs:
                    dir_names = [name.strip() for name in dirs.split(',')]
                else:
                    # 단일 디렉토리인 경우
                    single_dir = dirs.strip()
                    for key, value in self._paths.items():
                        if value == single_dir:
                            return str(self.root / single_dir)
                    raise ValueError(f'Directory name "{single_dir}" not found in predefined paths.')
            else:
                dir_names = dirs

            # 여러 디렉토리 경로 반환
            paths = {}
            for dir_name in dir_names:
                found = False
                for key, value in self._paths.items():
                    if value == dir_name:
                        paths[dir_name] = str(self.root / dir_name)
                        found = True
                        break
                if not found:
                    raise ValueError(f'Directory name "{dir_name}" not found in predefined paths.')

            return paths


    def list_available_dirs(self) -> List[str]:
        '''사용 가능한 디렉토리 이름 목록을 반환합니다: Returns a list of available directory names.'''
        return list(self._paths.values())

    def __getattr__(self, name: str) -> Callable[[], str]:
        '''설정된 경로에 대한 접근자 메서드를 동적으로 생성합니다: Create dynamic accessors for the configured paths.'''
        if name in self._paths:
            # e.g. self.data_dir() will call self._resolve('data')
            return lambda: str(self._resolve(self._paths[name]))
        raise AttributeError(f'"{type(self).__name__}" object has no attribute "{name}".')

WorkDirs = WorkDirConfigs()