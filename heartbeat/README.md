# heartbeat.heartbeat.Heartbeat

The Heartbeat sensor is a utility to report the sensor_reporter uptime.
This reliable scheduled reporting could be used as a heartbeat and the messages can be used to see how long sensor_reporter has been online.

## Dependencies

None.

## Parameters

Parameter | Required | Restrictions | Purpose
-|-|-|-
`Class` | X | `heartbeat.heartbeat.Heartbeat` |
`Connection` | X | Comma separated list of Connections | Where the ON/OFF messages are published.
`Level` | | DEBUG, INFO, WARNING, ERROR | When provided, sets the logging level for the sensor.
`Poll` | X | Positive number in seconds | How often to publish the uptime.
`Num-Dest` | X | | Destination to publish the uptime in milliseconds.
`Str-Dest` | X | | Destinationt to pubnlish dd:hh:mm:ss.

## Example Config

```ini
[Logging]
Syslog = YES
Level = INFO

[Connection1]
Class = openhab_rest.rest_conn.OpenhabREST
Name = openHAB
URL = http://localhost:8080
RefreshItem = Test_Refresh
Level = INFO

[Sensor1]
Class = heartbeat.heartbeat.Heartbeat
Connection = openHAB
Poll = 60
Num-Dest = heartbeat/num
Str-Dest = heartbeat/str
Level = INFO
```
