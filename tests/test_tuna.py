import unittest
import pg_tuna.wizard
import dataclasses
import typing


@dataclasses.dataclass
class Config:
    db_type: str = "web"
    db_version: int = 11
    connections: typing.Optional[int] = 100
    total_memory: int = 6
    cpu_num: int = 16
    disk_type: str = "ssd"


class TestPGTuna(unittest.TestCase):
    def test_aws(self):
        settings = pg_tuna.wizard.wizard_tune(Config())
        ret = settings.to_aws()
        self.assertEqual(
            ret,
            {
                "max_connections": {"value": 100, "unit": None},
                "random_page_cost": {"value": 1.1, "unit": None},
                "shared_buffers": {"value": 196608, "unit": "pages (8kB)"},
                "effective_cache_size": {"value": 589824, "unit": "pages (8kB)"},
                "work_mem": {"value": 3932, "unit": "kB"},
                "maintenance_work_mem": {"value": 393216, "unit": "kB"},
                "min_wal_size": {"value": 1024, "unit": "MB"},
                "max_wal_size": {"value": 4096, "unit": "MB"},
                "checkpoint_completion_target": {"value": 0.9, "unit": None},
                "wal_buffers": {"value": 2048, "unit": "pages (8kB)"},
                "default_statistics_target": {"value": 100, "unit": None},
                "max_parallel_workers_per_gather": {"value": 4, "unit": None},
                "max_worker_processes": {"value": 16, "unit": None},
                "max_parallel_workers": {"value": 16, "unit": None},
                "max_parallel_maintenance_workers": {"value": 4, "unit": None},
            },
        )

    def test_pg(self):
        settings = pg_tuna.wizard.wizard_tune(Config())
        ret = settings.to_pg()
        self.assertEqual(
            ret,
            {
                "max_connections": {"value": 100, "unit": None},
                "random_page_cost": {"value": 1.1, "unit": None},
                "shared_buffers": {"value": 1536, "unit": "MB"},
                "effective_cache_size": {"value": 4608, "unit": "MB"},
                "work_mem": {"value": 3932, "unit": "kB"},
                "maintenance_work_mem": {"value": 384, "unit": "MB"},
                "min_wal_size": {"value": 1024, "unit": "MB"},
                "max_wal_size": {"value": 4096, "unit": "MB"},
                "checkpoint_completion_target": {"value": 0.9, "unit": None},
                "wal_buffers": {"value": 16, "unit": "MB"},
                "default_statistics_target": {"value": 100, "unit": None},
                "max_parallel_workers_per_gather": {"value": 4, "unit": None},
                "max_worker_processes": {"value": 16, "unit": None},
                "max_parallel_workers": {"value": 16, "unit": None},
                "max_parallel_maintenance_workers": {"value": 4, "unit": None},
            },
        )
