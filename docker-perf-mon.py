import subprocess
import re
from datetime import datetime
import json
from redis import Redis
from time import sleep


r = Redis('0.0.0.0', 6379)


def gather_metrics():
    cmd = 'docker stats --format "{{.Name}} ; {{.CPUPerc}} ; {{.MemUsage}}" --no-stream'
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    obj = {}
    containers = [ i for i in p.stdout.split('\n') if i ]
    if len(containers) > 0:
        obj.update({'ts': datetime.now().timestamp()})
        for container in containers:
            name, cpu_usage, mem_usage = container.split(';')
            name = name.strip()
            mem_usage = mem_usage.split('/')[0]
            obj.update({
                name + '-cpu': float(cpu_usage.replace('%','')),
                name + '-mem': float(re.sub('[a-zA-Z]', '', mem_usage)),
            })

    return obj


def push_to_redis(metrics):
    prev_metrics = r.get('docker_metrics')
    if prev_metrics:
        metrics_list = json.loads(prev_metrics.decode('utf-8'))
        metrics_list.append(metrics)
        r.set('docker_metrics', json.dumps(metrics_list))
    else:
        r.set('docker_metrics', json.dumps([metrics]))



if __name__ == '__main__':
    while True:
        sleep(120)
        try:
            metrics = gather_metrics()
            if metrics:
                push_to_redis(metrics)
        except Exception as ex:
            print(str(ex))
