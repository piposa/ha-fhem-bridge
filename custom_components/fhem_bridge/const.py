"""FHEM Bridge constants."""

from homeassistant.const import Platform

DOMAIN = "fhem_bridge"
PLATFORMS = (Platform.SENSOR, Platform.SWITCH, Platform.BUTTON, Platform.EVENT, Platform.CLIMATE, Platform.COVER, Platform.LIGHT, Platform.SELECT, Platform.NUMBER, Platform.TEXT, Platform.BINARY_SENSOR)
CONF_DEVICES = "devices"
CONF_WRITABLE = "writable"
CONF_FINGERPRINT = "fingerprint"
CONF_QUERY = "query"
CONF_EDIT_ATTRIBUTES = "edit_attributes"
CONF_TECHNICAL = "technical"
CONF_DEVICE_GROUPS = "device_groups"
CONF_DEVICE_ALIASES = "device_aliases"
CONF_IMPORT_AREAS = "import_areas"
CONF_IMPORT_LABELS = "import_labels"
PANEL_PATH = "fhem-bridge-device"
