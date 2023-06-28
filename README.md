# pg-tuna

[![Build](https://github.com/delijati/pg-tuna/workflows/pg-tuna/badge.svg)](https://github.com/delijati/pg-tuna)
[![PyPI version fury.io](https://badge.fury.io/py/pg-tuna.svg)](https://pypi.python.org/pypi/pg-tuna/)

```
PostgreSQL + <({(>(
```

pg-tuna is a cli program to generate optimal PostgreSQL and AWS PostgreSQL RDS
settings. It outputs for AWS RDS already the needed units conversion so the
settings can be easily applied.

It is based on excelent work of:

- https://github.com/le0pard/pgtune
- https://github.com/gregs1104/pgtune

This tool only supports Linux there is no option to choose any other platform
and why ;)

## Install && run

```
$ pip install pg-tuna
```

Run it like:

```
$ pg-tuna --db-type web  --db-version 11 --memory 8 --cpu-num 8 --disk-type ssd

#-------------------------------------------------------------------------------------------------------------------------
# pg-tuna run on 2023-06-28
# Settings used: db_type = web | db_version = 11 | connections = None | total_memory = 8 | cpu_num = 8 | disk_type = ssd 
# Based on 8 GB RAM, platform Linux, 200 clients and web workload
#---------------------------------------------------------- PG ----------------------------------------------------------

 max_connections = 200
 random_page_cost = 1.1
 shared_buffers = 2048 MB
 effective_cache_size = 6144 MB
 work_mem = 2621 kB
 maintenance_work_mem = 512 MB
 min_wal_size = 1024 MB
 max_wal_size = 4096 MB
 checkpoint_completion_target = 0.9
 wal_buffers = 16 MB
 default_statistics_target = 100
 max_parallel_workers_per_gather = 4.0
 max_worker_processes = 8
 max_parallel_workers = 8
 max_parallel_maintenance_workers = 4.0

#---------------------------------------------------------- AWS ----------------------------------------------------------

 max_connections = 200
 random_page_cost = 1.1
 shared_buffers = 262144 pages (8kB)
 effective_cache_size = 786432 pages (8kB)
 work_mem = 2621 kB
 maintenance_work_mem = 524288 kB
 min_wal_size = 1024 MB
 max_wal_size = 4096 MB
 checkpoint_completion_target = 0.9
 wal_buffers = 2048 pages (8kB)
 default_statistics_target = 100
 max_parallel_workers_per_gather = 4.0
 max_worker_processes = 8
 max_parallel_workers = 8
 max_parallel_maintenance_workers = 4.0

```

## Debugging performance

To debug performance issues we first need to indentify the slow queries. Then
we can start benchmarking them and apply changes to our code (adding indexes,
modify our ERM , or apply optimized settings to PostgreSQL)

To test queries PostgreSQL has a nice tool `pgbench`. If you like me can't ssh into
the PostgreSQL server and you don't like to install PostgreSQL to get `pgbench`
use the included `Dockerfile` (it will only create a 8MB image).

https://www.PostgreSQLql.org/docs/10/pgbench.html

### pgbench
```bash
$ docker build -t pg_tuna/pgbench .
```
Set settings in `env.list` to connect to your PostgreSQL instance

We use a query defined in `bench/select_count.sql` to run our performance
tests.

Run
```
$ docker run -it --env-file ./env.list -v `pwd`/bench:/var/bench pg_tuna/pgbench pgbench -c 10 -j 4 -t 100 -f /var/bench/select_count.sql
```

Run via local jumphost
```
$ docker run -it --network="host" --env-file ./env.list -v `pwd`/bench:/var/bench pg_tuna/pgbench pgbench -c 10 -j 4 -t 100 -f /var/bench/select_count.sql
```
