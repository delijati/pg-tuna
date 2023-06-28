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
pip install pg-tuna
```

Run it like:

```
pg-tuna --db-type web  --db-version 11 --memory 8 --cpu-num 8 --disk-type ssd

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
docker build -t pg_tuna/pgbench .
```
Set settings in `env.list` to connect to your PostgreSQL instance

We use a query defined in `bench/select_count.sql` to run our performance
tests.

Run
```
docker run -it --env-file ./env.list -v `pwd`/bench:/var/bench pg_tuna/pgbench pgbench -c 10 -j 4 -t 100 -f /var/bench/select_count.sql
```

Run via local jumphost
```
docker run -it --network="host" --env-file ./env.list -v `pwd`/bench:/var/bench pg_tuna/pgbench pgbench -c 10 -j 4 -t 100 -f /var/bench/select_count.sql
```
