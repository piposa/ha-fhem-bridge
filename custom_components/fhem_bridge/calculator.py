"""Interpret the configurable native units of the FHEM calculators."""

from html import unescape

from .profiles import finite_number

CALCULATOR_UNITS = {
    "Currency": ("EUR", {"€": "EUR", "£": "GBP", "$": "USD"}),
    "Volume": ("m³", {"m³": "m³", "ft³": "ft³"}),
    "SiPrefixPower": ("W", {unit: unit for unit in ("W", "kW", "MW", "GW")}),
    "WFRUnit": ("L/min", {"l/min": "L/min", "m³/min": "m³/min", "m³/h": "m³/h"}),
}

_CALCULATOR_ATTRIBUTES = {
    "GasCalculator": (
        "Currency", "Volume", "SiPrefixPower", "GasPricePerKWh", "GaszValue", "GasNominalHeatingValue",
    ),
    "ElectricityCalculator": ("Currency", "SiPrefixPower", "ElectricityPricePerKWh"),
    "WaterCalculator": ("Currency", "WFRUnit", "WaterPricePerCubic"),
}
_PRICE_ATTRIBUTES = {
    "GasCalculator": ("GasPricePerKWh", "kWh"),
    "ElectricityCalculator": ("ElectricityPricePerKWh", "kWh"),
    "WaterCalculator": ("WaterPricePerCubic", "m³"),
}


def calculator_attributes(profile):
    return _CALCULATOR_ATTRIBUTES.get(profile.get("type"), ())


def calculator_metadata(profile, metadata, attribute):
    if attribute not in calculator_attributes(profile):
        return metadata
    default, mapping = CALCULATOR_UNITS[attribute]
    raw = profile.get("calculator_units", {}).get(attribute)
    if raw is None and attribute not in profile.get("attribute_names", ()):
        unit = default
    else:
        unit = mapping.get(unescape(raw).rstrip(";")) if isinstance(raw, str) else None
    return {**metadata, "unit_of_measurement": unit} if unit else {}


def calculator_prices(profile):
    """Return configured tariffs in the units HA's energy cost calculator accepts."""
    tariff = _PRICE_ATTRIBUTES.get(profile["type"])
    if tariff is None:
        return {}
    attribute, unit = tariff
    attributes = profile.get("calculator_units", {})
    price = finite_number(attributes.get(attribute))
    currency = calculator_metadata(profile, {}, "Currency").get("unit_of_measurement")
    if price is None or currency is None:
        return {}
    prices = {unit: (price, f"{currency}/{unit}")}
    if profile["type"] == "GasCalculator":
        volume = calculator_metadata(profile, {}, "Volume").get("unit_of_measurement")
        heating_value = finite_number(attributes.get("GasNominalHeatingValue"))
        correction = finite_number(attributes.get("GaszValue"))
        if volume and heating_value and correction and heating_value > 0 and correction > 0:
            if (volume_price := finite_number(price * heating_value * correction)) is not None:
                prices[volume] = (volume_price, f"{currency}/{volume}")
    return prices
