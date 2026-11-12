#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import re
from redis import Redis
from rq import Queue

REDIS_HOST = 'strds2.somenergia.lan'
REDIS_URL = 'redis://strds2.somenergia.lan/0'
REDIS_PORT = 6379
REDIS_DB = 0
BATCH_SIZE = 1000

QUEUE_NAME = 'cch_loader'

from erppeek import Client
O = Client('http://localhost:18069', 'somenergia', 'Oriol','shah9Nu+')
total = O.TgComerReaderRegister.search([])
total_read = []
for curve_id in total:
    total_read.append(O.TgComerReaderRegister.read(curve_id, ['name'])['name'])

# Llista de fitxers a buscar
FILENAMES = [
    'F5D_0022_0762_20240430.0.bz2',
    'F5D_0022_0763_20240430.0.bz2',
    'F5D_0022_0764_20240430.0.bz2',
]
FILENAMES = total_read

FILENAME_RE = re.compile(
    r'[A-Z0-9]+_\d{4}_\d{4}_\d{8}(?:_\d{8})?\.\d+(?:\.bz2)?'
)


def main():
    conn = Redis.from_url(REDIS_URL)
    queue = Queue(QUEUE_NAME, connection=conn)

    wanted = set(FILENAMES)
    queued = set()

    filename_to_job = {}

    job_ids = conn.lrange(queue.key, 0, -1)

    print "Jobs pendents:", len(job_ids)

    for i in xrange(0, len(job_ids), BATCH_SIZE):
        batch_ids = job_ids[i:i + BATCH_SIZE]
        job_keys = ['rq:job:%s' % job_id for job_id in batch_ids]
        jobs_data = conn.mget(job_keys)

        for job_id, job_data in zip(batch_ids, jobs_data):
            if not job_data:
                continue

            matches = FILENAME_RE.findall(job_data)

            for filename in matches:
                queued.add(filename)

                if filename not in filename_to_job:
                    filename_to_job[filename] = job_id

        if i and i % 10000 == 0:
            print "Revisats:", i, "jobs"
    import pudb;pu.db
    found = wanted.intersection(queued)
    missing = wanted.difference(queued)

    print ""
    print "----- TROBATS -----"
    for filename in sorted(found):
        print "[OK ]", filename, "->", filename_to_job.get(filename)

    print ""
    print "----- NO TROBATS -----"
    for filename in sorted(missing):
        print "[NO ]", filename

    print "Resum: ", str(len(found)), " trobats i ",str(len(missing))," no trobats."

if __name__ == '__main__':
    main()
