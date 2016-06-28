from __future__ import print_function

# Configuration
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
import config

import db
import db.dataset
import sqlalchemy


def generate_snapshots():
    db.init_db_engine(config.SQLALCHEMY_DATABASE_URI)
    with db.engine.connect() as connection:
        for job in get_all_jobs(connection):
            set_snapshot_id(
                connection=connection,
                job_id=job["job_id"],
                snapshot_id=db.dataset.create_snapshot(job["dataset_id"])
            )


def get_all_jobs(connection):
    result = connection.execute("""
        SELECT dataset_eval_jobs.id as job_id, dataset_eval_jobs.dataset_id as dataset_id
          FROM dataset_eval_jobs
    """)
    return [dict(j) for j in result.fetchall()]


def set_snapshot_id(connection, job_id, snapshot_id):
    connection.execute(sqlalchemy.text("""
        UPDATE dataset_eval_jobs
           SET dataset_id = :snapshot_id
         WHERE id = :job_id
    """), {
        "snapshot_id": snapshot_id,
        "job_id": job_id,
    })


if __name__ == "__main__":
    generate_snapshots()
