redis-cli del docker_metrics_mem docker_metrics_cpu
./env/bin/python homestack-helper-API.py &
./env/bin/python docker-perf-mon.py &
