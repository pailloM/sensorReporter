# Copyright 2020 Aymeric Pallottini
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Report system info

Classes:
    - SystemInfoSensor: Class that collects system info data
"""
import json
import psutil
import time
from core.sensor import Sensor


class SysInfoSensor(Sensor):
    """Collects an publishes systems info"""

    def __init__(self, publishers, params):
        """Initialize the sensor. This is not a self running sensor so Poll must
        be a positive number."""
        super().__init__(publishers, params)

        self.log.info("Configuing System Info Sensor")
        if self.poll <= 0:
            raise ValueError(
                "SystemInfoSensor requires a positive Poll value: " "%s", self.poll
            )

        self.sys_info_dict = {}

        # Get configuration
        self.destination = params("Destination").replace(" ", "").strip().split(",")
        self.log.debug("Info required: " + str(self.destination))
        # Kickoff a poll for the configured sensors.
        self.check_state()

    def disk_usg(self):
        dsk_usg = {"root": psutil.disk_usage("/")[3]}
        dsk_usg["home"] = psutil.disk_usage("/home")[3]
        dsk_usg["var"] = psutil.disk_usage("/var")[3]
        self.log.debug(str(json.dumps(dsk_usg)))
        return dsk_usg

    def curr_temp(self):
        """
        Reports the current temperature of the first sensor
        """
        temps = psutil.sensors_temperatures()
        for name, entries in temps.items():
            for entry in entries:
                curr_temp = entry.current
                break
            break
        return curr_temp

    def check_state(self):
        """Calculate all required system information and request publish"""
        if "nb_core" in self.destination:
            self.sys_info_dict["core_nb"] = psutil.cpu_count(logical=False)
        if "cpu_per" in self.destination:
            self.sys_info_dict["CPU_per"] = psutil.cpu_percent(1)
        if "uptime" in self.destination:
            self.sys_info_dict["uptime"] = time.time() - psutil.boot_time()
        if "mem_per" in self.destination:
            self.sys_info_dict["mem_per"] = psutil.virtual_memory()[2]
        if "disk_usage" in self.destination:
            self.sys_info_dict["disk_usage"] = self.disk_usg()
        if "swap_per" in self.destination:
            self.sys_info_dict["swap_per"] = psutil.swap_memory()
        if "temp" in self.destination:
            self.sys_info_dict["Temperature"] = self.curr_temp()
        if "load_avg" in self.destination:
            self.sys_info_dict["load_avg"] = psutil.getloadavg()

        self.publish_state()
        """Publishes the system info data."""
        self._send(json.dumps(self.sys_info_dict), self.destination)
