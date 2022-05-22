from fastapi import FastAPI, Response
import json
import docker
# import uvicorn
from redis import Redis



app = FastAPI()
client = docker.from_env()
r = Redis('0.0.0.0', 6379)



@app.get('/docker-info')
def docker_info(items: str):
    if items == 'containers':
        ctrs = client.containers.list(all=True)
        output = [ f'{i.name} : {i.status}' for i in ctrs ]
        return { 'containers': output }
    elif items == 'images':
        imgs = client.images.list()
        output = []
        [ output.extend(i.tags) for i in imgs ]
        return { 'images': output }



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



# if __name__ == '__main__':
#    uvicorn.run(app=app, host='0.0.0.0', port=5003, log_level='error')