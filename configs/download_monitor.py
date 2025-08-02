import time
import psutil
from typing import Optional
from .colorize import Msg

class DownloadMonitor:
    '''다운로드 성능 및 시스템 리소스 모니터링 클래스'''
    
    def __init__(self, total_files: int = 0):
        '''
        모니터링 초기화
        
        Args:
            total_files: 다운로드할 총 파일 수
        '''
        self.total_files = total_files
        self.completed_files = 0
        self.failed_files = 0
        
        # 시간 추적
        self.start_time = time.time()
        self.last_report_time = self.start_time
        
        # 메모리 추적
        self.start_memory = psutil.virtual_memory().used
        self.peak_memory = self.start_memory
        
        # 성능 통계
        self.total_bytes_downloaded = 0
        self.download_speeds = []
        
        Msg.Info('DOWNLOAD MONITOR INITIALIZED')
    
    def update_progress(self, success: bool = True, file_size: Optional[int] = None):
        '''
        다운로드 진행 상황 업데이트
        
        Args:
            success: 다운로드 성공 여부
            file_size: 다운로드된 파일 크기 (bytes)
        '''
        if success:
            self.completed_files += 1
            if file_size:
                self.total_bytes_downloaded += file_size
        else:
            self.failed_files += 1
        
        # 메모리 사용량 추적
        current_memory = psutil.virtual_memory().used
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
    
    def get_current_stats(self) -> dict:
        '''현재 통계 정보 반환'''
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # 진행률 계산
        if self.total_files > 0:
            progress_percent = (self.completed_files / self.total_files) * 100
        else:
            progress_percent = 0
        
        # 속도 계산
        if elapsed_time > 0:
            files_per_sec = self.completed_files / elapsed_time
            if self.total_bytes_downloaded > 0:
                mb_per_sec = (self.total_bytes_downloaded / (1024 * 1024)) / elapsed_time
            else:
                mb_per_sec = 0
        else:
            files_per_sec = 0
            mb_per_sec = 0
        
        # 메모리 사용량 계산
        current_memory = psutil.virtual_memory().used
        memory_overhead = (current_memory - self.start_memory) / (1024 * 1024)  # MB
        peak_memory_overhead = (self.peak_memory - self.start_memory) / (1024 * 1024)  # MB
        
        # 시스템 리소스
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_percent = psutil.virtual_memory().percent
        
        return {
            'elapsed_time': elapsed_time,
            'completed_files': self.completed_files,
            'failed_files': self.failed_files,
            'total_files': self.total_files,
            'progress_percent': progress_percent,
            'files_per_sec': files_per_sec,
            'mb_per_sec': mb_per_sec,
            'memory_overhead_mb': memory_overhead,
            'peak_memory_overhead_mb': peak_memory_overhead,
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent
        }
    
    def report_progress(self, force: bool = False):
        '''
        진행 상황 보고 (5초마다 또는 강제 실행)
        
        Args:
            force: 강제 보고 여부
        '''
        current_time = time.time()
        
        # 5초마다 또는 강제 실행
        if not force and (current_time - self.last_report_time) < 5.0:
            return
        
        stats = self.get_current_stats()
        self.last_report_time = current_time
        
        # 진행률 메시지
        progress_msg = (
            f'PROGRESS: {stats["completed_files"]}/{stats["total_files"]} '
            f'({stats["progress_percent"]:.1f}%) | '
            f'Speed: {stats["files_per_sec"]:.1f} files/sec'
        )
        
        if stats['mb_per_sec'] > 0:
            progress_msg += f', {stats["mb_per_sec"]:.1f} MB/sec'
        
        if stats['failed_files'] > 0:
            progress_msg += f' | Failures: {stats["failed_files"]}'
        
        Msg.Info(progress_msg)
        
        # 리소스 사용량 (메모리 오버헤드가 100MB 이상일 때만)
        if stats['memory_overhead_mb'] > 100:
            resource_msg = (
                f'RESOURCES: CPU: {stats["cpu_percent"]:.1f}%, '
                f'Memory: {stats["memory_percent"]:.1f}% '
                f'(+{stats["memory_overhead_mb"]:.1f}MB overhead)'
            )
            Msg.Dim(resource_msg)
    
    def final_report(self):
        '''최종 다운로드 완료 보고서'''
        stats = self.get_current_stats()
        
        # 시간 포맷팅
        elapsed_min = int(stats['elapsed_time']) // 60
        elapsed_sec = int(stats['elapsed_time']) % 60
        
        # 최종 보고서
        Msg.Green('=' * 60)
        Msg.Green('DOWNLOAD MONITORING FINAL REPORT')
        Msg.Green('=' * 60)
        
        # 기본 통계
        Msg.Info(f'Completed Files: {stats["completed_files"]}/{stats["total_files"]} ({stats["progress_percent"]:.1f}%)')
        if stats['failed_files'] > 0:
            Msg.Warn(f'Failed Files: {stats["failed_files"]}')
        
        # 성능 통계
        Msg.Info(f'Total Time: {elapsed_min}m {elapsed_sec}s')
        Msg.Info(f'Average Speed: {stats["files_per_sec"]:.2f} files/sec')
        
        if stats['mb_per_sec'] > 0:
            total_mb = self.total_bytes_downloaded / (1024 * 1024)
            Msg.Info(f'Data Transfer: {total_mb:.1f} MB ({stats["mb_per_sec"]:.2f} MB/sec)')
        
        # 리소스 사용량
        Msg.Info(f'Peak Memory Overhead: {stats["peak_memory_overhead_mb"]:.1f} MB')
        
        # 효율성 평가
        if stats['files_per_sec'] > 2.0:
            Msg.Green('Performance: EXCELLENT')
        elif stats['files_per_sec'] > 1.0:
            Msg.Info('Performance: GOOD')
        elif stats['files_per_sec'] > 0.5:
            Msg.Warn('Performance: MODERATE')
        else:
            Msg.Error('Performance: SLOW - Consider checking network or system resources')
        
        Msg.Green('=' * 60)
    
    def get_eta(self) -> Optional[str]:
        '''예상 완료 시간 계산'''
        stats = self.get_current_stats()
        
        if stats['files_per_sec'] <= 0 or self.total_files <= 0:
            return None
        
        remaining_files = self.total_files - self.completed_files
        if remaining_files <= 0:
            return 'COMPLETED'
        
        eta_seconds = remaining_files / stats['files_per_sec']
        eta_min = int(eta_seconds) // 60
        eta_sec = int(eta_seconds) % 60
        
        return f'{eta_min}m {eta_sec}s'