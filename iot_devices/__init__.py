
from iot_devices.light import LightDevice
from iot_devices.door import DoorDevice
from iot_devices.fan import FanDevice
from iot_devices.coffee_maker import CoffeeMakerDevice
from iot_devices.window import WindowDevice


DEVICE_HANDLERS = {
    LightDevice.MODEL: LightDevice,
    DoorDevice.MODEL: DoorDevice,
    FanDevice.MODEL: FanDevice,
    CoffeeMakerDevice.MODEL: CoffeeMakerDevice,
    WindowDevice.MODEL: WindowDevice,
}
