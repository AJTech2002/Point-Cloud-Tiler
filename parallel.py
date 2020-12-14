import concurrent.futures
from multiprocessing import Process, Queue
import time


class v:
    def __init__(self, valueInitial):
        self.value = valueInitial

    def increment(self):
        self.value += 1
        print("New : " + self.value)


numb = 271508852


def inc(q):
    for i in range(0, numb):
        q.put(i)
    q.put('done')


elapsedA = 0
elapsedB = 0


def attemptLoad():

    q = Queue()
    p = Process(target=inc, args=(q,))
    p.start()

    res = q.get()
    start = time.time()
    while (res != 'done'):
        # print(res)
        res = q.get()
        if (str(res) != 'done'):
            v = int(res) + 1
    end = time.time()
    q.close()
    p.join()

    elapsedA = end - start
    print("ELAPSED : " + str(end - start))


def defaultLoad():
    start = time.time()
    count = 0
    for i in range(0, numb):
        # print(i)
        if (str(i) != 'done'):
            v = int(i) + 1
        count += 1

    end = time.time()
    elapsedB = str(end - start)
    print("ELAPSED : " + str(end - start) + " at " + str(count))


if __name__ == '__main__':
    # attemptLoad()
    defaultLoad()
