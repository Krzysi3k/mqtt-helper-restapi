redis-cli del docker-metrics-mem docker-metrics-cpu
./env/bin/python homestack-helper-API.py &
./env/bin/python docker-perf-mon.py &
