#!/usr/bin/env python
from __future__ import print_function
import sys
import times
from redis import from_url
from rq import use_connection, requeue_job, Queue
from rq.job import Job
from rq.registry import FailedJobRegistry
from datetime import datetime
import argparse

INTERVAL = 7200  # Seconds
MAX_ATTEMPTS = 5
QUEUES_TO_REQUEUE = ['cups_cch', 'tm_validate', 'make_invoices']
QUEUES_TO_DELETE = ['jobspool-autoworker']
EXECINFO_TO_DELETE = ['Work-horse process was terminated unexpectedly', 'es mes petita que la data inicial', 'ValueError: start date not found in coefficients',
        'No s\'han trobat versions de preus', 'InFailedSqlTransaction: current transaction is aborted, commands ignored until end of transaction block']

redis_conn = from_url(sys.argv[1])
use_connection(redis_conn)

all_queues = Queue().all()


def main(redis_conn, interval, max_attempts):
    use_connection(redis_conn)
    all_queues = Queue().all()
    print("{}: Try to requeu jobs".format(str(datetime.now())))
    for queue in all_queues:
        fq = FailedJobRegistry(queue.name)
        for job_id in fq.get_job_ids():
            try:
                job = Job.fetch(job_id)
            except:
                print("Job {} not exist anymore. We will delete from FailedJobRegistry".format(job_id))
                try:
                    key_registry = fq.key
                    redis_conn.zrem(key_registry,job_id)
                except Exception as e:
                    print("We cannot delete job in FailedJobRegistry")
                    print(job_id)
                    print(e)
            #if not job.meta.get('requeue', True):
            #    print("Job {} of Queue {} was marked as job.meta.requeue=false but we requeue it.".format(job_id, queue.name))
            #    #continue
            if job.is_finished:
                key_registry = fq.key
                redis_conn.zrem(key_registry,job_id)
            if queue.name in QUEUES_TO_REQUEUE:
                job.meta.setdefault('attempts', 0)
                if job.meta['attempts'] > max_attempts:
                    print("Job %s %s attempts. MAX ATTEMPTS %s limit exceeded on %s" % (
                            job.id, job.meta['attempts'], max_attempts, job.origin
                    ))
                    print(job.description)
                    print(job.exc_info)
                    continue
                else:
                    ago = (times.now() - job.enqueued_at).seconds
                    if ago >= interval:
                        print("%s: attemps: %s enqueued: %ss ago on %s (Requeue)" % (
                            job.id, job.meta['attempts'], ago, job.origin
                        ))
                        job.meta['attempts'] += 1
                        job.save()
                        requeue_job(job.id, connection=redis_conn)
                        continue
            if queue.name in QUEUES_TO_DELETE:
                try:
                    key_registry = fq.key
                    redis_conn.zrem(key_registry,job_id)
                    continue
                except Exception as e:
                    print("We cannot delete job in FailedJobRegistry")
                    print(job_id)
                    print(e)
            if any(substring in job.exc_info  for substring in EXECINFO_TO_DELETE):
                try:
                    key_registry = fq.key
                    redis_conn.zrem(key_registry,job_id)
                    continue
                except Exception as e:
                    print("We cannot delete job in FailedJobRegistry")
                    print(job_id)
                    print(e)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
            description="Requeue failed jobs"
    )

    parser.add_argument(
        'redis_conn',
        type=str,
        default='somenergia-redis.somenergia.lan',
        help="Connection address to Redis",
    )
    parser.add_argument(
        '--interval',
        dest='interval',
        default=INTERVAL,
        type=int,
        help="Interval before requeu (in seconds)",
    )
    parser.add_argument(
        '--max-attempts',
        dest='max_attempts',
        default=MAX_ATTEMPTS,
        type=int,
        help="Max attemps before move to permanent failed",
    )

    args = parser.parse_args()
    main(from_url(args.redis_conn), args.interval, args.max_attempts)

# vim: et ts=4 sw=4

