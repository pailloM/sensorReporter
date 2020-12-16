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
import json
import logging
from configparser import NoOptionError
from core.utils import set_log_level


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
            try:
                self.nb_of_values = int(params("NbOfValues"))
            except NoOptionError:
                self.nb_of_values = 0
            self.device_class_dict = {
                "binary_sensor": ["binary_sensor", "motion", "door", "window"],
                "sensor": ["sensor", "humidity", "temperature", "battery"],
            }
            # get parameters to construct homeassistant config message
            self.config_dict = {}
            try:
                self.sensor_name = params(class).split(".")[0]
                self.config_dict["name"] = (
                    params("Destination").replace(" ", "").strip().split(",")
                )
                self.log.debug("Config dict: " + str(self.config_dict))
                try:
                    self.config_dict["device_class"] = params("DeviceClass")
                    # cannot reconstruct state topic. Missing root topic in this class
                    self.config_dict["state_topic"] = params("StateTopic")
                    if (
                        self.config_dict["device_class"]
                        in self.device_class_dict["binary_sensor"]
                    ):
                        self.sensor_type = "binary_sensor"
                        try:
                            self.config_dict["payload_on"] = "on"
                            self.config_dict["payload_on"] = params("PayLoadOn")
                        except NoOptionError:
                            try:
                                self.config_dict["payload_closed"] = params(
                                    "PayLoadClosed"
                                )
                                del self.config_dict["payload_on"]
                            except NoOptionError:
                                self.config_dict["payload_on"] = "on"
                        try:
                            self.config_dict["payload_off"] = "off"
                            self.config_dict["payload_off"] = params("PayLoadOff")
                        except NoOptionError:
                            try:
                                self.config_dict["payload_open"] = params("PayLoadOpen")
                                del self.config_dict["payload_off"]
                            except NoOptionError:
                                self.config_dict["payload_off"] = "off"
                        # construct topic msg
                        self.conf_topic = (
                            params("DiscoveryPrefix")
                            + "/"
                            + "binary_sensor"
                            + "/" 
                            + self.sensor_name
                            + self.config_dict["name"][0]
                            + "/config"
                        )
                        self.log.debug("Config dict: " + str(self.config_dict))
                    elif (
                        self.config_dict["device_class"]
                        in self.device_class_dict["sensor"]
                    ):
                        self.sensor_type = "sensor"
                        try:
                            self.config_dict["unit_of_measurement"] = params("Unit")
                            self.config_dict["unit_of_measurement"] = self.config_dict[
                                "unit_of_measurement"
                            ].split(",")
                            self.log.debug(
                                "Unit: " + str(self.config_dict["unit_of_measurement"])
                            )
                        except NoOptionError:
                            self.config_dict["unit_of_measurement"] = ""
                        try:
                            self.config_dict["value_template"] = params("ValueTemplate")
                            self.config_dict["value_template"] = self.config_dict[
                                "value_template"
                            ].split(",")
                            self.log.debug(
                                "Template: " + str(self.config_dict["value_template"])
                            )
                        except NoOptionError:
                            self.config_dict["value_template"] = ""

                        self.log.debug("Config dict: " + str(self.config_dict))
                except NoOptionError:
                    self.config_dict = {}
                    self.conf_topic = ""
                # config payload and config topic:
                # only sensor_type supports multiple sensors
                if self.config_dict != {}:
                    if self.sensor_type == "sensor":
                        for conf_item in range(0, self.nb_of_values):
                            # construct topic msg
                            self.conf_topic = (
                                params("DiscoveryPrefix")
                                + "/"
                                + "sensor"
                                + "/" 
                                + self.sensor_name
                                + self.config_dict["name"][conf_item].strip()
                                + "/config"
                            )
                            self.conf_payload = self.config_dict.copy()
                            self.conf_payload["name"] = self.config_dict["name"][
                                conf_item
                            ].strip()
                            self.conf_payload["unit_of_measurement"] = self.config_dict[
                                "unit_of_measurement"
                            ][conf_item].strip()
                            self.conf_payload["value_template"] = self.config_dict[
                                "value_template"
                            ][conf_item].strip()
                            self.log.debug("conf_payload: " + str(self.conf_payload))
                            self.conf_payload = json.dumps(self.conf_payload)
                            self._send_config(self.conf_payload, self.conf_topic)
                    else:
                        self.log.debug("conf_payload: " + str(self.config_dict))
                        self.conf_payload = json.dumps(self.config_dict)
                        self._send_config(self.conf_payload, self.conf_topic)

            except NoOptionError:
                del self.config_dict

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
