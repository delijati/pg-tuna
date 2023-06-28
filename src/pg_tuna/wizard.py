import argparse
import typing
import sys
import datetime
import dataclasses


# Memory constants
KB = 1024
MB = 1024 * KB
GB = 1024 * MB
TB = 1024 * GB

PLATFORM = "Linux"
AWS_FACTOR = 0.87


@dataclasses.dataclass
class Setting:
    max_connections: int
    random_page_cost: float
    shared_buffers: int
    effective_cache_size: int
    work_mem: int
    maintenance_work_mem: int
    min_wal_size: int
    max_wal_size: int
    checkpoint_completion_target: float
    wal_buffers: int
    default_statistics_target: int
    max_parallel_workers_per_gather: typing.Optional[int] = None
    max_worker_processes: typing.Optional[int] = None
    max_parallel_workers: typing.Optional[int] = None
    max_parallel_maintenance_workers: typing.Optional[int] = None

    def to_aws(self):
        ret = {}
        # DBInstanceClassMemory = options.total_memory * AWS_FACTOR
        # Print AWS out settings
        for field in dataclasses.fields(self):
            key = field.name
            value = getattr(self, field.name)
            # if key in ("max_connections"):
            #     factor = DBInstanceClassMemory / s["max_connections"]
            # print(f"{key} = DBInstanceClassMemory/{factor}")
            if key in ("shared_buffers", "effective_cache_size", "wal_buffers"):
                value = int(binaryround(value / 8))
                ret[key] = {"value": value, "unit": "pages (8kB)"}
                # factor = DBInstanceClassMemory / value
                # print(f"{key} = DBInstanceClassMemory/{factor}")
            elif key in ("work_mem"):
                value = int(value)
                ret[key] = {"value": value, "unit": "kB"}
            elif key in ("maintenance_work_mem"):
                value = int(binaryround(value))
                ret[key] = {"value": value, "unit": "kB"}
            elif key in ("min_wal_size", "max_wal_size"):
                value = int(binaryround(value / 1024))
                ret[key] = {"value": value, "unit": "MB"}
            else:
                if value:
                    ret[key] = {"value": value, "unit": None}
        return ret

    def to_pg(self):
        ret = {}
        for field in dataclasses.fields(self):
            key = field.name
            value = getattr(self, field.name)
            if key in (
                "shared_buffers",
                "effective_cache_size",
                "maintenance_work_mem",
                "wal_buffers",
                "min_wal_size",
                "max_wal_size",
            ):
                value = int(binaryround(value / 1024))
                # value = value / 1024
                ret[key] = {"value": value, "unit": "MB"}
            elif key in ("work_mem",):
                ret[key] = {"value": value, "unit": "kB"}
            else:
                if value:
                    ret[key] = {"value": value, "unit": None}
        return ret


DB_PARALLEL_DEFAULT = {
    10: {
        "max_parallel_workers_per_gather": 2,
    },
    11: {
        "max_parallel_workers_per_gather": 2,
    },
    12: {
        "max_parallel_workers_per_gather": 2,
    },
    13: {
        "max_parallel_workers_per_gather": 2,
    },
    14: {
        "max_parallel_workers_per_gather": 2,
    },
    15: {
        "max_parallel_workers_per_gather": 2,
    },
}

CONNECTIONS_DEFAULT = {
    "web": 200,
    "oltp": 300,
    "dw": 20,
    "mixed": 100,
    "desktop": 5,
}

DISK_DEFAULT = {"ssd": 1.1, "san": 1.1, "hdd": 4}


def parse_args(args=sys.argv[1:]):
    """Parse arguments."""

    parser = argparse.ArgumentParser(
        description="Postgres tuner also shows data as AWS RDS datatypes",
    )

    parser.add_argument(
        "--db-type",
        dest="db_type",
        default="mixed",
        type=str,
        choices=["web", "oltp", "mixed", "desktop"],
        help="specify db_type",
    )

    parser.add_argument(
        "--db-version",
        dest="db_version",
        default=list(DB_PARALLEL_DEFAULT.keys())[0],
        type=int,
        choices=list(DB_PARALLEL_DEFAULT.keys()),
        help="specify db_version",
    )

    parser.add_argument(
        "--connections",
        dest="connections",
        type=int,
        help="specify connections count if None we set by db_type",
    )

    parser.add_argument(
        "--memory",
        dest="total_memory",
        default=2,
        type=int,
        help="specify total memory in GB",
    )

    parser.add_argument(
        "--cpu-num",
        dest="cpu_num",
        default=2,
        type=int,
        help="specify total cpu cores",
    )

    parser.add_argument(
        "--disk-type",
        dest="disk_type",
        default=list(DISK_DEFAULT.keys())[0],
        type=str,
        choices=list(DISK_DEFAULT.keys()),
        help="specify disk_type",
    )

    ret = parser.parse_args(args)
    if ret.connections and ret.connections < 20:
        parser.error("Minimum number of connections is 20")
    return ret


def binaryround(value):
    """
    Keeps the 4 most significant binary bits, truncates the rest so
    that SHOW will be likely to use a larger divisor
    >>> binaryround(22)
    22
    >>> binaryround(1234567)
    1179648
    """
    multiplier = 1
    while value > 16:
        value = int(value / 2)
        multiplier = multiplier * 2
    return multiplier * value


def wizard_tune(options):
    db_type = options.db_type

    s = {"max_connections": CONNECTIONS_DEFAULT[db_type]}

    # Allow overriding the maximum connections
    if options.connections is not None:
        s["max_connections"] = options.connections

    # Estimate memory on this system via parameter or system lookup
    total_memory = options.total_memory * GB

    # Memory allocation
    # Extract some values just to make the code below more compact
    # The base unit for memory types is the kB, so scale system memory to that
    mem = int(total_memory) / KB
    con = int(s["max_connections"])

    if total_memory >= (256 * MB):
        s["random_page_cost"] = DISK_DEFAULT[options.disk_type]
        s["shared_buffers"] = {
            "web": mem / 4,
            "oltp": mem / 4,
            "dw": mem / 4,
            "mixed": mem / 4,
            "desktop": mem / 16,
        }[db_type]

        s["effective_cache_size"] = {
            "web": mem * 3 / 4,
            "oltp": mem * 3 / 4,
            "dw": mem * 3 / 4,
            "mixed": mem * 3 / 4,
            "desktop": mem / 4,
        }[db_type]

        workers_per_gather = DB_PARALLEL_DEFAULT[int(options.db_version)][
            "max_parallel_workers_per_gather"
        ]

        if options.cpu_num >= 4:
            workers_per_gather = options.cpu_num / 2
            # no clear evidence, that each new worker will provide big benefit for each noew core
            if options.db_type != "dw" and workers_per_gather > 4:
                workers_per_gather = 4

            if options.db_version >= 11:
                parallel_worker = options.cpu_num / 2
                # no clear evidence, that each new worker will provide big benefit for each noew core
                if parallel_worker > 4:
                    parallel_worker = 4
                s["max_parallel_maintenance_workers"] = parallel_worker

            s["max_parallel_workers_per_gather"] = workers_per_gather
            s["max_worker_processes"] = options.cpu_num
            s["max_parallel_workers"] = options.cpu_num

        # better calculation taken from le0pard
        # https:/github.com/le0pard/pgtune/blob/8bb05286aa63c2cc0673514b285ba747c7c2dbcb/assets/selectors/configuration.js#L321
        # work_mem should be ((RAM - shared_buffers) / (max_connections * 3) /
        # max_parallel_workers_per_gather).

        work_mem = int((mem - s["shared_buffers"]) / (con * 3) / workers_per_gather)

        s["work_mem"] = {
            "web": work_mem,
            "oltp": work_mem,
            "dw": work_mem / 2,
            "mixed": work_mem / 2,
            "desktop": work_mem / 6,
        }[db_type]

        s["maintenance_work_mem"] = {
            "web": mem / 16,
            "oltp": mem / 16,
            "dw": mem / 8,
            "mixed": mem / 16,
            "desktop": mem / 16,
        }[db_type]

        # Cap maintenance RAM at 2GB on servers with lots of memory
        # (Remember that the setting is in terms of kB here)
        if s["maintenance_work_mem"] > (2 * GB / KB):
            s["maintenance_work_mem"] = 2 * GB / KB

    else:
        raise Exception("This tool not being optimal for low memory systems")

    s["min_wal_size"] = {
        "web": (1 * GB / KB),
        "oltp": (2 * GB / KB),
        "dw": (4 * GB / KB),
        "desktop": (100 * MB / KB),
        "mixed": (1 * GB / KB),
    }[db_type]

    s["max_wal_size"] = {
        "web": (4 * GB / KB),
        "oltp": (8 * GB / KB),
        "dw": (16 * GB / KB),
        "desktop": (200 * MB / KB),
        "mixed": (4 * GB / KB),
    }[db_type]

    # based on https:/github.com/postgres/postgres/commit/bbcc4eb2
    s["checkpoint_completion_target"] = {
        "web": 0.9,
        "oltp": 0.9,
        "dw": 0.9,
        "mixed": 0.9,
        "desktop": 0.9,
    }[db_type]

    # For versions < 9.1, follow auto-tuning guideline for wal_buffers added
    # in 9.1, where it's set to 3% of shared_buffers up to a maximum of 16MB.
    # Starting with 9.1, the default value of -1 should be fine.
    s["wal_buffers"] = 3 * s["shared_buffers"] / 100
    if s["wal_buffers"] > 16 * MB / KB:
        s["wal_buffers"] = 16 * MB / KB
    # It's nice if wal_buffers is an even 16MB if it's near that number.  Since
    # that is a common case on Windows, where shared_buffers is clipped to 512MB,
    # round upwards in that situation
    if s["wal_buffers"] > 14 * MB / KB and s["wal_buffers"] < 16 * MB / KB:
        s["wal_buffers"] = 16 * MB / KB

    # TODO Eliminate setting this needlessly when on a version that
    # defaults to 100
    s["default_statistics_target"] = {
        "web": 100,
        "oltp": 100,
        "dw": 500,
        "mixed": 100,
        "desktop": 100,
    }[db_type]
    ret = Setting(**s)
    return ret


def print_settings(options, s):
    def print_settings_dict(data):
        for key, value in data.items():
            val = value["value"]
            unit = value["unit"]
            if unit:
                print(f" {key} = {val} {unit}")
            else:
                print(f" {key} = {val}")

    # Header to identify when the program ran, before any new settings
    used_settings = "# Settings used: %s " % " | ".join(
        [f"{arg} = {getattr(options, arg)}" for arg in vars(options)]
    )
    print(f"\n#{'-'*len(used_settings)}")
    print(f"# pg-tuna run on {datetime.date.today()}")
    print(used_settings)
    print(
        "# Based on %s GB RAM, platform %s, %s clients and %s workload"
        % (options.total_memory, PLATFORM, s.max_connections, options.db_type)
    )
    print(
        f"#{'-'*(int(len(used_settings)/2)-2)} PG {'-'*(int(len(used_settings)/2)-2)}\n"
    )

    print_settings_dict(s.to_pg())

    print(
        f"\n#{'-'*(int(len(used_settings)/2)-2)} AWS {'-'*(int(len(used_settings)/2)-2)}\n"
    )

    print_settings_dict(s.to_aws())

    print("")


def main():
    options = parse_args()
    s = wizard_tune(options)
    print_settings(options, s)


if __name__ == "__main__":
    main()
