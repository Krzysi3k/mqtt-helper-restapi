import re
import timeit


sample = '1,2,3\n1,1,1,10\n'
obj = re.compile('[a-zA-Z]')


def benchmark_one():
    # if not obj.match(sample):
        # pass
    sample = '1,2,3\n1,1,1,10\n'
    if not (re.match('[a-zA-Z]', sample)):
        pass


if __name__ == '__main__':
    for i in range(5):
        v = timeit.timeit('benchmark_one()', setup='from __main__ import benchmark_one', number=1_000_000)
        print(v)