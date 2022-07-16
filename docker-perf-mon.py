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
    current_ts = datetime.now().timestamp()
    cpu_metrics = {'ts': current_ts}
    mem_metrics = {'ts': current_ts}
    containers = [ i for i in p.stdout.split('\n') if i ]
    if containers:
        for container in containers:
            name, cpu_usage, mem_usage = container.split(';')
            name = name.strip()
            mem_usage = mem_usage.split('/')[0]
            cpu_metrics.update({
                name: float(cpu_usage.replace('%',''))
            })
            mem_metrics.update({
                name: float(re.sub('[a-zA-Z]', '', mem_usage))
            })

    return {
        'cpu': cpu_metrics,
        'mem': mem_metrics
    }


def push_to_redis(metrics, keyname):
    prev_metrics = r.get(f'docker_metrics_{keyname}')
    if prev_metrics:
        metrics_list = json.loads(prev_metrics.decode('utf-8'))
        metrics_list.append(metrics)
        r.set(f'docker_metrics_{keyname}', json.dumps(metrics_list))
    else:
        r.set(f'docker_metrics_{keyname}', json.dumps([metrics]))



if __name__ == '__main__':
    while True:
        sleep(60)
        try:
            metrics = gather_metrics()
            if metrics:
                push_to_redis(metrics['cpu'], keyname='cpu')
                push_to_redis(metrics['mem'], keyname='mem')
        except Exception as ex:
            print(str(ex))
