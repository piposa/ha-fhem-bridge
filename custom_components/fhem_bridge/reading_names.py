"""Names for equivalent HA measurements across FHEM protocols."""

SENSOR_READING_NAMES = {
    "temperature": "temperature",
    "measured-temp": "temperature",
    "actual_temperature": "temperature",
    "desired-temp": "target_temperature",
    "set_point_temperature": "target_temperature",
    "humidity": "humidity",
    "dewpoint": "dew_point",
    "pressure": "pressure",
    "wind": "wind_speed",
    "windspeed": "wind_speed",
    "wind_direction": "wind_direction",
    "winddirection": "wind_direction",
    "rain": "rain",
    "rain_cum": "rain",
    "lux": "illuminance",
    "power": "power",
    "power_kw": "power",
    "voltage": "voltage",
    "frequency": "frequency",
    "m3ph": "gas_flow",
    "wfrcurrent": "flow",
    "valveposition": "valve_position",
    "actuator": "valve_position",
    "batterylevel": "battery_level",
    "battery": "battery",
    "batterystate": "battery",
}

TYPED_READING_NAMES = {
    "brightness": {"illuminance": "illuminance"},
    "luminosity": {"illuminance": "illuminance"},
    "gaspower": {"volume_flow_rate": "gas_flow"},
    "current": {"power": "power", "current": "current"},
}

BINARY_READING_NAMES = {
    "opening": "opening",
    "window": "opening",
    "door": "opening",
    "motion": "motion",
    "smoke": "smoke",
    "moisture": "moisture",
}


def sensor_reading_name(reading, device_class, mode):
    """Keep distinct quantities distinct, even when HA shares one device class."""
    point = reading.rsplit(".", 1)[-1].casefold()
    if point in TYPED_READING_NAMES:
        return TYPED_READING_NAMES[point].get(device_class)
    if point == "battery" and device_class == "battery":
        return "battery_level"
    if mode == "diagnostic":
        if point == "state":
            return "raw_state"
        if point == "contact":
            return "radio_message"
    return SENSOR_READING_NAMES.get(point)
