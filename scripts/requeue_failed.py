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

INTERVAL = 1200  # Seconds
MAX_ATTEMPTS = 5
QUEUES_TO_REQUEUE = ["cups_cch", "sii", "mailchimp_tasks"]
QUEUES_TO_DELETE = ["jobspool-autoworker", "profiling", "make_invoices", "tm_validate", "cch_loaderX"]  # noqa: E501
EXECINFO_TO_DELETE = [
    "Work-horse process was terminated unexpectedly",
    "es mes petita que la data inicial",
    "ValueError: start date not found in coefficients",
    "No s'han trobat versions de preus",
    "InFailedSqlTransaction: current transaction is aborted, commands ignored until end of transaction block",  # noqa: E501
    "RepresenterError: ('cannot represent an object', <osv.orm.browse_null object at 0x7f3148f11a90>)",  # noqa: E501
    "You try to write on an record that doesn't exist",
    "cursor, uid, line_id, ['import_phase'])['import_phase']\nTypeError: 'bool' object has no attribute '__getitem__'",  # noqa: E501
]
QUEUES_TO_DELETE_AFETER_REQUE = ["sii", "cups_cch"]

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
            except Exception:
                print(
                    "Job {} not exist anymore. We will delete from FailedJobRegistry".format(job_id)
                )
                try:
                    key_registry = fq.key
                    redis_conn.zrem(key_registry, job_id)
                except Exception as e:
                    print("We cannot delete job in FailedJobRegistry")
                    print(job_id)
                    print(e)
                continue
            # if not job.meta.get('requeue', True):
            #    print("Job {} of Queue {} was marked as job.meta.requeue=false but we requeue it.".format(job_id, queue.name))   # noqa: E501
            #    #continue
            if job.is_finished:
                key_registry = fq.key
                redis_conn.zrem(key_registry, job_id)
            if queue.name in QUEUES_TO_REQUEUE:
                job.meta.setdefault("attempts", 0)
                if job.meta["attempts"] > max_attempts:
                    print(
                        "Job %s %s attempts. MAX ATTEMPTS %s limit exceeded on %s"
                        % (job.id, job.meta["attempts"], max_attempts, job.origin)
                    )
                    print(job.description)
                    print(job.exc_info)
                    if queue.name in QUEUES_TO_DELETE_AFETER_REQUE:
                        print("deleting: %s from %s (Requeue)" % (job.id, job.origin))
                        key_registry = fq.key
                        redis_conn.zrem(key_registry, job_id)
                        continue
                else:
                    ago = (times.now() - job.enqueued_at).seconds
                    if ago >= interval:
                        if any(substring in job.exc_info for substring in EXECINFO_TO_DELETE):
                            try:
                                print("deleting: %s from %s (Requeue)" % (job.id, job.origin))
                                print(job.exc_info)
                                key_registry = fq.key
                                redis_conn.zrem(key_registry, job_id)
                                continue
                            except Exception as e:
                                print("We cannot delete job %s in FailedJobRegistry" % job.id)
                                print(e)
                        print(
                            "%s: attemps: %s enqueued: %ss ago on %s (Requeue)"
                            % (job.id, job.meta["attempts"], ago, job.origin)
                        )
                        job.meta["attempts"] += 1
                        job.save()
                        requeue_job(job.id, connection=redis_conn)
                        continue
            if (
                queue.name in QUEUES_TO_DELETE
                or any(substring in job.exc_info for substring in EXECINFO_TO_DELETE)
                or job.exc_info == ""
            ):
                try:
                    print("deleting: %s from %s (Requeue)" % (job.id, job.origin))
                    print(job.exc_info)
                    key_registry = fq.key
                    redis_conn.zrem(key_registry, job_id)
                    continue
                except Exception as e:
                    print("We cannot delete job %s in FailedJobRegistry" % job.id)
                    print(e)

    print("{}: End of requeu/delete jobs".format(str(datetime.now())))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Requeue failed jobs")

    parser.add_argument(
        "redis_conn",
        type=str,
        default="somenergia-redis.somenergia.lan",
        help="Connection address to Redis",
    )
    parser.add_argument(
        "--interval",
        dest="interval",
        default=INTERVAL,
        type=int,
        help="Interval before requeu (in seconds)",
    )
    parser.add_argument(
        "--max-attempts",
        dest="max_attempts",
        default=MAX_ATTEMPTS,
        type=int,
        help="Max attemps before move to permanent failed",
    )

    args = parser.parse_args()
    main(from_url(args.redis_conn), args.interval, args.max_attempts)

# vim: et ts=4 sw=4
