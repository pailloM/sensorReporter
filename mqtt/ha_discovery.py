# mqtt/ha_discovery.py
"""Optional Home Assistant discovery bridge built on ha-mqtt-discoverable."""
import json
import re
from typing import Any

try:
    from ha_mqtt_discoverable import DeviceInfo
    from ha_mqtt_discoverable import sensors as hads
    HAVE_HAD = True
except ImportError:
    HAVE_HAD = False

_PUBLISHED: dict[str, dict[str, str]] = {}   # namespace -> {topic: payload}


class HADiscoveryBridge:
    """Emits HA discovery configs using an existing paho client.

    Only the discovery/config messages go through ha-mqtt-discoverable.
    State publication stays in MqttConnection so the generic Connection
    interface (shared with openHAB REST) is untouched.
    """

    COMPONENT_MAP = {
        "sensor": ("Sensor", "SensorInfo"),
        "binary_sensor": ("BinarySensor", "BinarySensorInfo"),
        "switch": ("Switch", "SwitchInfo"),
        "light": ("Light", "LightInfo"),
        "number": ("Number", "NumberInfo"),
        "select": ("Select", "SelectInfo"),
        "button": ("Button", "ButtonInfo"),
        "cover": ("Cover", "CoverInfo"),
    }

    def __init__(self, client, conn_cfg: dict[str, Any], log):
        self.client = client
        self.log = log
        self.log.debug("HADiscoveryBridge initialized with config:\n%s", json.dumps(conn_cfg, indent=2))
        self.client_name = conn_cfg["Client"]
        self.node_id = re.sub(r"[^A-Za-z0-9_]", "_", self.client_name)
        self.root_topic = conn_cfg["RootTopic"]
        self.prefix = conn_cfg.get("HAPrefix", "homeassistant")
        self.enabled = bool(conn_cfg.get("HADiscovery", False)) and HAVE_HAD
        self.availability = None      # set by MqttConnection once known
        self.published: dict[str, str] = {}   # topic -> payload
        self._seen: set = set()

        self.device_info = None
        if HAVE_HAD:
            name = self.client_name
            ident = "{}_{}".format(
                name,
                conn_cfg["User"].replace(" ", "_").lower(),
            )
            self.device_info = DeviceInfo(name=name, identifiers=ident)

        if conn_cfg.get("HADiscovery", False) and not HAVE_HAD:
            log.warning("HADiscovery requested but ha-mqtt-discoverable is "
                        "not installed; run ./install_dependencies.sh hadiscovery")

    def set_availability(self, topic: str, online: str, offline: str) -> None:
        self.availability = {"availability_topic": topic,
                             "payload_available": online,
                             "payload_not_available": offline}

    def announce(self, cfg: dict[str, Any]) -> None:
        if not self.enabled:
            return

        component = cfg.pop("component", "sensor")
        if component not in self.COMPONENT_MAP:
            self.log.error("Unsupported HADiscovery component: %s", component)
            return

        _, info_cls_name = self.COMPONENT_MAP[component]
        info_cls = getattr(hads, info_cls_name)

        name = cfg.pop("name", None)
        state_dest = cfg.pop("state_dest", None)
        command_src = cfg.pop("command_src", None)
        #object_id = (unique_id
        #             or re.sub(r"[^A-Za-z0-9_]", "_",
        #                       str(state_dest or command_src)))
        tmp_object_id = re.sub(
            r"[^A-Za-z0-9_]", "_",str(state_dest or command_src)
        )
        unique_id = cfg.pop(
            "unique_id", 
            f"{self.client_name}_{tmp_object_id}"
        )
        kwargs = dict(cfg)                       # device_class, units, templates...
        kwargs["name"] = name or tmp_object_id       # required by every *Info class
        kwargs[""] = tmp_object_id
        kwargs["device"] = self.device_info
        if unique_id:
            kwargs["unique_id"] = unique_id
        if self.availability:
            kwargs.update(self.availability)
        if state_dest:
            kwargs["state_topic"] = "{}/{}".format(
                self.root_topic, state_dest)
        if command_src:
            kwargs["command_topic"] = "{}/{}/set".format(
                self.root_topic, command_src)

        try:
            info = info_cls(**kwargs)
            payload = json.loads(
                info.model_dump_json(exclude_none=True, by_alias=True)
            )
            self.log.debug("HADiscovery payload for %s: %s", object_id, payload)
        except Exception as exc:
            self.log.error("Bad HADiscovery config for %s: %s", object_id, exc)
            return

        # The library's auto-generated topics are useless here; point HA
        # at the topics sensorReporter actually publishes to.
        if state_dest:
            payload["state_topic"] = "{}/{}".format(
                self.root_topic, state_dest)
            payload.pop("json_attributes_topic", None)
        if command_src:
            payload["command_topic"] = "{}/{}/set".format(
                self.root_topic, command_src)

        if self.availability:
            payload.update(self.availability)

        cfg_topic = "{}/{}/{}/{}/config".format(
            self.prefix, component, self.node_id, object_id)
        body = json.dumps(payload)

        self.client.publish(cfg_topic, body, qos=1, retain=True)
        self.log.debug("HADiscovery announced %s: %s", cfg_topic, body)
        self.published[cfg_topic] = body
        self._seen.add(cfg_topic)

    def withdraw_all(self) -> None:
        """Blank out retained configs before a config reload."""
        for topic in self.published:
            self.client.publish(topic, "", qos=1, retain=True)
        self.published.clear()

    def republish_all(self):
        if not self.enabled:
            return
        for topic, payload in self.published.items():
            self.client.publish(topic, payload, qos=1, retain=True)

    def withdraw_stale(self) -> None:
        """Call after all devices have re-registered."""
        for topic, _ in self.published.items():
            if topic not in self._seen:
                self.client.publish(topic, "", qos=1, retain=True)
                del self.published[topic]
                self.log.debug("HADiscovery withdrawing stale configs: %s",
                            self.published[topic]
                )
        self._seen.clear()