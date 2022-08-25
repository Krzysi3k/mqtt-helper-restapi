import subprocess
from datetime import datetime
from typing import Any
from redis import Redis
from time import sleep
import io
import csv


r = Redis('0.0.0.0', 6379)


def generate_csv(value_row: list[Any], header_row: list[Any] = [], existing_values: str = '') -> str:
    in_memory = io.StringIO()
    w = csv.writer(in_memory)
    if not existing_values:
        w.writerow(header_row)
    w.writerow(value_row)
    current_values = in_memory.getvalue()
    if existing_values:
        existing_values += current_values
        return existing_values
    return current_values


def gather_metrics(cnt_num):
    cmd = 'docker stats --format "{{.Name}} ; {{.CPUPerc}} ; {{.MemUsage}}" --no-stream'
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    containers = p.stdout.splitlines()
    if len(containers) == cnt_num:
        current_ts = round(datetime.now().timestamp(), 0)
        header_row = [ i.split(';')[0].strip() for i in containers ]
        header_row.append('ts')
        cpu_values = [ round(float(i.split(';')[1].strip().replace('%','')),2) for i in containers ]
        cpu_values.append(current_ts)
        mem_values = [ round(float(i.split(';')[2].split('/')[0].strip().replace('MiB','')),2) for i in containers ]
        mem_values.append(current_ts)

        push_to_redis('cpu', cpu_values, header_row)
        push_to_redis('mem', mem_values, header_row)


def push_to_redis(keyname: str, metric_values: list[Any], header: list[str]):
    current_metrics = r.get(f'docker-metrics-{keyname}')
    if current_metrics:
        updated_metrics = generate_csv(metric_values, header, current_metrics.decode('utf-8'))
    else:
        updated_metrics = generate_csv(metric_values, header)
    r.set(f'docker-metrics-{keyname}', updated_metrics)



if __name__ == '__main__':
    sleep(60) # warmup
    out = subprocess.run('docker ps -q | wc -l', shell=True, capture_output=True, text=True)
    cnt_num = int(out.stdout)
    while True:
        try:
            gather_metrics(cnt_num)
        except Exception as ex:
            print(str(ex))
        sleep(60)
