from configparser import NoOptionError
import json
import socket
import ssl
import traceback
from time import sleep
from core.utils import get_sequential_params


def get_mqtt_config(params, log):
    DEVICE_CLASS_DICT = {
        "binary_sensor": {"class": ["binary_sensor", "motion", "door", "window"],
                          "req_params": ["Sensor", "Destination"],
                          "opt_params": ["DiscoveryPrefix", "PayLoadOn", "PayLoadOff",
                                         "PayLoadOpen", "PayLoadClosed", "ValueTemplate"]},
        "sensor": {"class": ["sensor", "humidity", "temperature", "battery"],
                   "req_params": ["Sensor", "Destination", "Unit"],
                   "opt_params": ["DiscoveryPrefix", "ValueTemplate"]},
    }
    TRANSLATION_DICT = {"DeviceClass": "device_class", "Sensor": "name",
                        "PayLoadOn": "payload_on", "PayLoadOff": "payload_off",
                        "PayLoadOpen": "payload_open", "PayLoadClosed": "payload_closed",
                        "Unit": "unit_of_measurement", "DiscoveryPrefix": "DiscoveryPrefix"}

    sensors = get_sequential_params(params, "Sensors")
    log.info(f"Sensors are: {sensors}")
    configs = []
    for index, sensor in enumerate(sensors):
        index += 1
        # get parameters to construct homeassistant config message
        config_dict = {}
        try:
            config_dict["device_class"] = get_sequential_params(
                params, "DeviceClass")
            log.info(f"Sensor device class is: {config_dict['device_class']}")
        except NoOptionError:
            log.debug(
                f"Missing DeviceClass parameter in config file for {sensors}{index}")
            return []

        if config_dict["device_class"] in DEVICE_CLASS_DICT["binary_sensor"]["class"]:
            sensor_type = "binary_sensor"
        elif config_dict["device_class"] in DEVICE_CLASS_DICT["sensor"]["class"]:
            sensor_type = "sensor"
        else:
            log.warning(
                f"Unknown DeviceClass for {sensors}{index}")
            return []
        # loop through the required parameters and get the info from the config file
        for param in DEVICE_CLASS_DICT[sensor_type]["req_params"]:
            try:
                config_dict[TRANSLATION_DICT[param]
                            ] = get_sequential_params(params, param)
            except NoOptionError:
                log.error(
                    f"Missing {param} in config file for {sensors}{index}")
                return None
        # loop through the optional parameters and get the info from the config file
        for param in DEVICE_CLASS_DICT[sensor_type]["opt_params"]:
            try:
                config_dict[TRANSLATION_DICT[param]
                            ] = get_sequential_params(params, param)
            except NoOptionError:
                log.debug(f"{param} not in config file for {sensors}{index}")
                # assign defaults values:
                DEFAULT_OPTIONS = {"DiscoveryPrefix": "homeassistant",
                                   "ValueTemplate": "",
                                   "PayLoadOn": "on",
                                   "PayLoadOff": "off", }
                config_dict[TRANSLATION_DICT[param]
                            ] = DEFAULT_OPTIONS[param]
        conf_topic = f"{config_dict['DiscoveryPrefix']}/{sensor_type}"
        del config_dict["DiscoveryPrefix"]
        configs.append(tuple(config_dict, conf_topic))
    return configs
