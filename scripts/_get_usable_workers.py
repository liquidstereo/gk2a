import os
import psutil

def get_usable_mem(mem_per_worker:int=3000,
                   mem_reserved:int=8192) -> int:

    total_mem_mb = psutil.virtual_memory().total // (1024 * 1024)
    usable_mem_mb = max(total_mem_mb - mem_reserved, 0)
    return max(1, usable_mem_mb // mem_per_worker)


def get_usable_cpu(reserved_core:int=1) -> int:

    cpu_count = psutil.cpu_count(logical=False) or 1    # ← BASED ON PHYSICAL CORE COUNT
    return max(1, cpu_count - reserved_core)


def get_usable_workers(mem_per_worker:int=3000,
                       reserved_mem:int=8192,
                       reserved_core:int=1) -> int:

    workers_by_mem = get_usable_mem(mem_per_worker, reserved_mem)
    workers_by_cpu = get_usable_cpu(reserved_core)
    return min(workers_by_mem, workers_by_cpu)

if __name__ == '__main__':
    workers = get_usable_workers()
    print(f'Optimal aerender workers (RAM + CPU): {workers}')