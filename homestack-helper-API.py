from fastapi import FastAPI, Response, status
import json
import docker
import uvicorn
import subprocess
import time
# from threading import Thread
from redis import Redis
# from prometheus_client import start_http_server, Gauge


app = FastAPI()
client = docker.from_env()
r = Redis('0.0.0.0', 6379)
# CPU_METRIC = Gauge('cpu_usage_percentage', 'usage of cpu percentage')
# MEM_METRIC = Gauge('mem_usage_percentage', 'usage of mem Megabytes')

# guwno_lista = ['ema', 'mordko', 'kurwa', 'chamie']

# gaugest_list = [Gauge(f'{i}_usage_percentage', 'usage of cpu percentage') for i in guwno_lista]


# def monitoring_runner():
#     while True:
#         try:
#             CPU_METRIC.set(random.randrange(0,100))
#             MEM_METRIC.set(random.randrange(100,500))
#         except Exception:
#             pass
#         time.sleep(5)


@app.get('/docker-info')
def docker_info(items: str):
    begin = time.time()
    if items == 'containers':
        cached_ctrs = r.get('docker-containers')
        if cached_ctrs:
            payload = cached_ctrs.decode('utf-8')
            output = json.loads(payload)
            return { 'containers': output }
        ctrs = client.containers.list(all=True)
        output = [ f'{i.name} : {i.status}' for i in ctrs ]
        r.set('docker-containers', json.dumps(output), ex=600)
        return { 'containers': output }
    elif items == 'images':
        cached_imgs = r.get('docker-images')
        if cached_imgs:
            payload = cached_imgs.decode('utf-8')
            images = json.loads(payload)
            return { 'images': images }
        cli_out = subprocess.run("docker images | awk 'NR>1 {print $1,$2, \"-\" ,$7}'", shell=True, capture_output=True, text=True).stdout.split('\n')
        images = [img for img in cli_out if img]
        payload = []
        for i in images:
            img_name, img_size = i.split(' - ')
            payload.append(
                f'{img_name}, {img_size}'
            )
        r.set('docker-images', json.dumps(payload), ex=600)
        return { 'images': payload }



@app.get('/redis-info')
def redis_info():
    keys = [
        'vibration-sensor',
        'door-state',
        'rotate-option',
        'washing-state'
        #'termometr-payload'
    ]
    values = r.mget(keys)
    output = {}
    for k, v in zip(keys, values):
        if v is None:
            continue
        val = v.decode('utf-8')
        if "{" in val:
            obj = json.loads(val)
            if type(obj) is list:
                obj = obj[-1]
            output.update({k: obj})
        else:
            output.update({k: val})
    return output


@app.get('/get-redis-data')
def get_redis_data(data: str, response: Response):
    try:
        payload = r.get(data).decode('utf-8')
    except AttributeError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return { data: 'Not found' }
    if data == 'docker-metrics-mem' or data == 'docker-metrics-cpu' or data == 'termometr-payload':
        return Response(content=payload, media_type='text/html')
    elif '{' in payload:
        return Response(content=payload, media_type='application/json')
    return { 'payload': payload }



if __name__ == '__main__':
    # start_http_server(5001)
    # Thread(target=monitoring_runner).start()
    uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level='error')
