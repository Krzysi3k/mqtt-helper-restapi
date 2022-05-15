from fastapi import FastAPI, Response
import json
import docker
import uvicorn
from redis import Redis



app = FastAPI()
client = docker.from_env()
r = Redis('0.0.0.0', 6379)



@app.get('/docker-info')
def docker_info(items: str):
    if items == 'containers':
        ctrs = client.containers.list(all=True)
        return { i.name:i.status for i in ctrs }
    elif items == 'images':
        imgs = client.images.list()
        output = []
        [ output.extend(i.tags) for i in imgs ]
        return { 'images': output }



@app.get('/redis-info')
def redis_info():
    keys = r.keys()
    values = r.mget(keys)
    output = {}
    for k, v in zip(keys, values):
        if v is None:
            continue
        key = k.decode('utf-8')
        val = v.decode('utf-8')
        if "{" in val:
            obj = json.loads(val)
            if type(obj) is list:
                obj = obj[-1]
            output.update({key: obj})
        else:
            output.update({key: val})
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
#    uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level='error')