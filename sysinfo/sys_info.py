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
from core.utils import parse_values, get_sequential_params


class SysInfoSensor(Sensor):
    """Collects an publishes systems info"""

    def __init__(self, publishers, params):
        """Initialize the sensor. This is not a self running sensor so Poll must
        be a positive number."""
        super().__init__(publishers, params)

        self.log.info("Configuring System Info Sensor")
        sensors = get_sequential_params(params, "Sensor")
        destinations = get_sequential_params(params, "Destination")
        templates = get_sequential_params(params, "Template")
        laststates = [None] * len(sensors)
        if len(sensors) != len(destinations) != len(templates):
            raise ValueError(
                "List of addresses and destinations do not match up!")
        self.devices = dict(zip(sensors, destinations))
        self.states = dict(zip(sensors, laststates))
        self.log.debug(f"Info required: {self.devices}")

        if self.poll <= 0:
            raise ValueError(
                "SystemInfoSensor requires a positive Poll value: " "%s", self.poll
            )

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
        if "nb_core" in self.devices:
            self.states["core_nb"] = psutil.cpu_count(logical=False)
        if "cpu_per" in self.devices:
            self.states["cpu_per"] = psutil.cpu_percent(1)
        if "uptime" in self.devices:
            self.states["uptime"] = time.time() - psutil.boot_time()
        if "mem_per" in self.devices:
            self.states["mem_per"] = psutil.virtual_memory()[2]
        if "disk_usage" in self.devices:
            self.states["disk_usage"] = self.disk_usg()
        if "swap_per" in self.devices:
            self.states["swap_per"] = psutil.swap_memory()
        if "temp" in self.devices:
            self.states["temp"] = self.curr_temp()
        if "load_avg" in self.devices:
            self.states["load_avg"] = psutil.getloadavg()

        self.publish_state()
        """Publishes the system info data."""
        for key in self.devices:
            self._send(self.states[key], self.devices[key])
