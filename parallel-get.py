#!/usr/bin/env python3

import multiprocessing
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

curdir = os.path.abspath(os.path.dirname(__file__))

def read_targets():
    targets = []
    with open(os.path.join(curdir, 'get')) as f:
        for line in f.readlines():
            if line.startswith('get_current_ubuntu'):
                targets.append(line)
            if line.startswith('get_all_ubuntu'):
                targets.append(line)
    return targets

def handler(signum, frame):
    p = subprocess.Popen(['pkill', '-TERM', '-P', str(os.getpid())])
    p.wait()

def init():
    signal.signal(signal.SIGINT, handler)

def make_script(tempdir, content):
    fd, path = tempfile.mkstemp(dir=tempdir)
    fp = os.fdopen(fd, 'w')
    fp.write('#!/bin/bash\ncd {}\n. common/libc.sh\n'.format(curdir))
    fp.write(content)
    fp.close()
    return path

def get_links(tempdir, line):
    path = make_script(tempdir, line)
    output = subprocess.check_output(['bash', path], env={'LIBC_DRY_RUN':'1'})
    return output.decode('utf-8')

def get_lib(tempdir, line):
    path = make_script(tempdir, line)
    subprocess.check_output(['bash', path])

def run_parallel(func, items):
    tempdir = tempfile.mkdtemp()
    size = min(len(items), 16)
    pool = multiprocessing.Pool(size, init)
    try:
        results = []
        for item in items:
            results.append(pool.apply_async(func, [tempdir, item]))
        pool.close()
        pool.join()
        return list(map(lambda r: r.get(), results))
    except KeyboardInterrupt:
        pool.terminate()
    finally:
        shutil.rmtree(tempdir)

def main():
    targets = read_targets()
    commands = run_parallel(get_links, targets)
    libs = []
    for command in commands:
        libs += command.splitlines()
    run_parallel(get_lib, libs)

if __name__ == '__main__':
    main()
