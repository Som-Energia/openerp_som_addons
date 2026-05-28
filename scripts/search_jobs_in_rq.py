#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function  # Garanteix que print() funcioni igual a Python 2 i 3
import re
from redis import Redis
from rq import Queue
from erppeek import Client
import configdb
import zlib


REDIS_URL = configdb.redis.redis_url
BATCH_SIZE = 1000
QUEUE_NAME = 'cch_loader'

erp_conn = Client(**configdb.erppeek)
total = erp_conn.TgComerReaderRegister.search([])
total_read = []
for curve_id in total:
    total_read.append(erp_conn.TgComerReaderRegister.read(curve_id, ['name'])['name'])

# Llista de fitxers a buscar
# Format: 'F5D_0022_0762_20240430.0.bz2',
FILENAMES = total_read if total_read else []
FILENAME_RE = re.compile(
    r'[A-Z0-9]+_\d{4}_\d{4}_\d{8}(?:_\d{8})?\.\d+(?:\.bz2)?'
)

redis_conn = Redis.from_url(REDIS_URL)
queue = Queue(QUEUE_NAME, connection=redis_conn)

wanted = set(FILENAMES)
queued = set()

filename_to_job = {}

job_ids = redis_conn.lrange(queue.key, 0, -1)

print("Jobs pendents:", len(job_ids))

for i in range(0, len(job_ids), BATCH_SIZE):
    batch_ids = job_ids[i:i + BATCH_SIZE]
    job_keys = ['rq:job:%s' % job_id for job_id in batch_ids]
    jobs_data = redis_conn.mget(job_keys)

    for job_id, job_data in zip(batch_ids, jobs_data):
        if not job_data:
            continue

        try:
            job_data = zlib.decompress(job_data)
        except zlib.error as e:
            print("Error descomprimint job_id %s: %s" % (job_id, e))

        matches = FILENAME_RE.findall(job_data)

        for filename in matches:
            queued.add(filename)
            if filename not in filename_to_job:
                filename_to_job[filename] = job_id

    if i and i % 10000 == 0:
        print("Revisats:", i, "jobs")

found = wanted.intersection(queued)
missing = wanted.difference(queued)

print("")
print("----- TROBATS -----")
for filename in sorted(found):
    print("[OK ]", filename, "->", filename_to_job.get(filename))

print("")
print("----- NO TROBATS -----")
for filename in sorted(missing):
    print("[NO ]", filename)

print("Resum: ", str(len(found)), " trobats i ", str(len(missing)), " no trobats.")
