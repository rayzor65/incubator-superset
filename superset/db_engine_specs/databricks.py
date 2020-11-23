# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from superset import app, conf
from superset.db_engine_specs.hive import HiveEngineSpec
from superset.utils import core as utils

if TYPE_CHECKING:
    # prevent circular imports
    from superset.models.core import Database

QueryStatus = utils.QueryStatus
config = app.config
logger = logging.getLogger(__name__)

tracking_url_trans = conf.get("TRACKING_URL_TRANSFORMER")
hive_poll_interval = conf.get("HIVE_POLL_INTERVAL")


class DatabricksEngineSpec(HiveEngineSpec):
    """Reuses HiveEngineSpec functionality."""

    engine = "databricks"
    engine_name = "Databricks"
    max_column_name_length = 767
    # pylint: disable=line-too-long
    _time_grain_expressions = {
        None: "{col}",
        "PT1S": "from_unixtime(unix_timestamp({col}), 'yyyy-MM-dd HH:mm:ss')",
        "PT1M": "from_unixtime(unix_timestamp({col}), 'yyyy-MM-dd HH:mm:00')",
        "PT1H": "from_unixtime(unix_timestamp({col}), 'yyyy-MM-dd HH:00:00')",
        "P1D": "from_unixtime(unix_timestamp({col}), 'yyyy-MM-dd 00:00:00')",
        "P1W": "date_format(date_sub({col}, CAST(7-from_unixtime(unix_timestamp({col}),'u') as int)), 'yyyy-MM-dd 00:00:00')",
        "P1M": "from_unixtime(unix_timestamp({col}), 'yyyy-MM-01 00:00:00')",
        "P0.25Y": "date_format(add_months(trunc({col}, 'MM'), -(month({col})-1)%3), 'yyyy-MM-dd 00:00:00')",
        "P1Y": "from_unixtime(unix_timestamp({col}), 'yyyy-01-01 00:00:00')",
        "P1W/1970-01-03T00:00:00Z": "date_format(date_add({col}, INT(6-from_unixtime(unix_timestamp({col}), 'u'))), 'yyyy-MM-dd 00:00:00')",
        "1969-12-28T00:00:00Z/P1W": "date_format(date_add({col}, -INT(from_unixtime(unix_timestamp({col}), 'u'))), 'yyyy-MM-dd 00:00:00')",
    }

    # Scoping regex at class level to avoid recompiling
    # 17/02/07 19:36:38 INFO ql.Driver: Total jobs = 5
    jobs_stats_r = re.compile(r".*INFO.*Total jobs = (?P<max_jobs>[0-9]+)")
    # 17/02/07 19:37:08 INFO ql.Driver: Launching Job 2 out of 5
    launching_job_r = re.compile(
        ".*INFO.*Launching Job (?P<job_number>[0-9]+) out of " "(?P<max_jobs>[0-9]+)"
    )
    # 17/02/07 19:36:58 INFO exec.Task: 2017-02-07 19:36:58,152 Stage-18
    # map = 0%,  reduce = 0%
    stage_progress_r = re.compile(
        r".*INFO.*Stage-(?P<stage_number>[0-9]+).*"
        r"map = (?P<map_progress>[0-9]+)%.*"
        r"reduce = (?P<reduce_progress>[0-9]+)%.*"
    )
