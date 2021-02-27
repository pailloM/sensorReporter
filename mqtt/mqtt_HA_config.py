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
                          "req_params": [], "opt_params": []},
        "sensor": {"class": ["sensor", "humidity", "temperature", "battery"],
                   "req_params": [], "opt_params": []},
    }

    sensors = get_sequential_params(params, "Sensor")
    for index, sensor in enumerate(sensors):
        index += 1
        # get parameters to construct homeassistant config message
        config_dict = {}
        try:
            log.debug(
                f"Parameters: {get_sequential_params(params, f'sensor{index}')}")
            sensor_name = get_sequential_params(params, f"class{index}")
            config_dict["name"] = (
                get_sequential_params(params, f"Sensor{index}").replace(
                    " ", "").strip().split(",")
            )
            log.debug(f"Config dict: {config_dict}")
            try:
                config_dict["device_class"] = get_sequential_params(
                    params, "DeviceClass")
                config_dict["state_topic"] = get_sequential_params(
                    params, "Destination")
                if (
                    config_dict["device_class"]
                    in DEVICE_CLASS_DICT["binary_sensor"]["class"]
                ):
                    sensor_type = "binary_sensor"
                    try:
                        if config_dict["device_class"] == "binary_sensor":
                            del config_dict["device_class"]
                        config_dict["name"] = config_dict["name"][0]
                        config_dict["payload_on"] = "on"
                        config_dict["payload_on"] = get_sequential_params(params,
                                                                          "PayLoadOn")
                    except NoOptionError:
                        try:
                            config_dict["payload_closed"] = get_sequential_params(params,
                                                                                  "PayLoadClosed"
                                                                                  )
                            del config_dict["payload_on"]
                        except NoOptionError:
                            config_dict["payload_on"] = "on"
                    try:
                        config_dict["payload_off"] = "off"
                        config_dict["payload_off"] = get_sequential_params(params,
                                                                           "PayLoadOff")
                    except NoOptionError:
                        try:
                            config_dict["payload_open"] = get_sequential_params(params,
                                                                                "PayLoadOpen")
                            del config_dict["payload_off"]
                        except NoOptionError:
                            config_dict["payload_off"] = "off"
                    # construct initial part of topic msg final part added in mqtt_conn.py
                    conf_topic = (
                        get_sequential_params(params,
                                              "DiscoveryPrefix") + "/" + "binary_sensor"
                    )
                    log.debug("Config dict: " + str(config_dict))
                elif (
                    config_dict["device_class"]
                    in DEVICE_CLASS_DICT["sensor"]["class"]
                ):
                    sensor_type = "sensor"
                    try:
                        if config_dict["device_class"] == "sensor":
                            del config_dict["device_class"]
                        config_dict["unit_of_measurement"] = get_sequential_params(params,
                                                                                   "Unit")
                        config_dict["unit_of_measurement"] = config_dict[
                            "unit_of_measurement"
                        ].split(",")
                        log.debug(
                            "Unit: " +
                            str(config_dict["unit_of_measurement"])
                        )
                    except NoOptionError:
                        config_dict["unit_of_measurement"] = ""
                    try:
                        config_dict["value_template"] = get_sequential_params(params,
                                                                              "ValueTemplate")
                        config_dict["value_template"] = config_dict[
                            "value_template"
                        ].split(",")
                        log.debug(
                            "Template: " +
                            str(config_dict["value_template"])
                        )
                    except NoOptionError:
                        config_dict["value_template"] = ""
                    # construct initial part of topic msg final part added in mqtt_conn.py
                    conf_topic = get_sequential_params(params,
                                                       "DiscoveryPrefix") + "/" + "sensor"
                    log.debug("Config dict: " + str(config_dict))
            except NoOptionError:
                config_dict = {}
                conf_topic = ""
            # config payload:
            # only sensor_type supports multiple sensors
            if config_dict != {}:
                if sensor_type == "sensor":
                    for conf_item in range(
                        0, len(config_dict["value_template"])
                    ):
                        conf_payload = config_dict.copy()
                        conf_payload["name"] = config_dict["name"][
                            conf_item
                        ].strip()
                        conf_payload["unit_of_measurement"] = config_dict[
                            "unit_of_measurement"
                        ][conf_item].strip()
                        conf_payload["value_template"] = config_dict[
                            "value_template"
                        ][conf_item].strip()
                        log.debug("conf_payload: " +
                                  str(conf_payload))
                    return config_dict, conf_topic
                else:
                    log.debug("conf_payload: " +
                              str(config_dict))
                    return config_dict, conf_topic

        except NoOptionError:
            del config_dic
