from fastapi import FastAPI, Response
import json
import docker
import uvicorn
import subprocess
from redis import Redis



app = FastAPI()
client = docker.from_env()
r = Redis('0.0.0.0', 6379)



@app.get('/docker-info')
def docker_info(items: str):
    if items == 'containers':
        cached_ctrs = r.get('docker_containers')
        if cached_ctrs:
            payload = cached_ctrs.decode('utf-8')
            output = json.loads(payload)
            return { 'containers': output }
        ctrs = client.containers.list(all=True)
        output = [ f'{i.name} : {i.status}' for i in ctrs ]
        r.set('docker_containers', json.dumps(output), ex=600)
        return { 'containers': output }
    elif items == 'images':
        cached_imgs = r.get('docker_images')
        if cached_imgs:
            payload = cached_imgs.decode('utf-8')
            images = json.loads(payload)
            return { 'images': images }
        cli_out = subprocess.run("docker images | awk 'NR>1 {print $1,$2, \"-\" ,$7}'", shell=True, capture_output=True, text=True).stdout.split('\n')
        images = [img for img in cli_out if img]
        payload = []
        for i in images:
            img_name, img_size = i.split(' - ')
            payload.append({
                'image': img_name,
                'size': img_size
            })
        r.set('docker_images', json.dumps(payload), ex=600)
        return { 'images': payload }



@app.get('/redis-info')
def redis_info():
    keys = [
        'vibration_sensor',
        'door_state',
        'rotate_option',
        'washing_state',
        'termometr_payload'
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
def get_redis_data(data: str):
    try:
        payload = r.get(data).decode('utf-8')
    except:
        return { data: 'Not found' }
    if '{' in payload:
        return Response(content=payload, media_type='application/json')
    return { 'payload': payload }



if __name__ == '__main__':
   uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level='error')
