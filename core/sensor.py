# Copyright 2020 Richard Koshak
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

"""Contains the parent class for Sensors.

Classes: Sensor
"""

from abc import ABC
import logging
from configparser import NoOptionError
from core.utils import set_log_level, get_sequential_params
from mqtt.mqtt_HA_config import get_mqtt_config


class Sensor(ABC):
    """Abstract class from which all sensors should inherit. check_state and/or
    publish_state should be overridden.
    """

    def __init__(self, publishers, params):
        """
        Sets all the passed in arguments as data members. If params("Poll")
        exists self.poll will be set to that. If not it is initialized to -1.
        self.last_poll is initialied to None.

        Arguments:
        - publishers: list of Connection objects to report to.
        - params: parameters from the section in the .ini file the sensor is created
        from.
        """
        self.log = logging.getLogger(type(self).__name__)
        self.publishers = publishers
        self.params = params
        try:
            self.poll = float(params("Poll"))
        except NoOptionError:
            self.poll = -1
        self.last_poll = None
        set_log_level(params, self.log)
        # MQTT config topic
        self.log.info(str(publishers))
        for con in publishers:
            if "mqtt" in str(con):
                self.mqtt_publisher = True
            else:
                self.mqtt_publisher = False
        self.log.debug("mqtt_publisher: " + str(self.mqtt_publisher))
        if self.mqtt_publisher:
            configs = get_mqtt_config(params, self.log)
            for config in configs:
                self.log.debug(f"mqtt config to publish: {config}")
                self._send_config(config[0], config[1])

    def check_state(self):
        """Called to check the latest state of sensor and publish it. If not
        overridden it just calls publish_state().
        """
        self.publish_state()

    def publish_state(self):
        """Called to publish the current state to the publishers. The default
        implementation is a pass.
        """

    def _send(self, msg, dest):
        """Sends msg to the dest on all publishers."""
        for conn in self.publishers:
            conn.publish(msg, dest)

    def _send_config(self, msg, dest):
        """Sends msg to the dest on all publishers."""
        for conn in self.publishers:
            if "mqtt" in str(conn):
                conn.publish(msg, dest, config=True)

    def cleanup(self):
        """Called when shutting down the sensor, give it a chance to clean up
        and release resources."""
