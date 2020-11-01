
from magic_bulb import RGBCWBulb
import asyncio
import logging

async def Run():
    light = RGBCWBulb("10.0.0.21")
    print("Config Bulb...")

    print("")
    print("Turning ON...")
    await light.on()
    print(light)

    print("sleep...")
    await asyncio.sleep(1)

    # print("")
    # print("Set Color Red...")
    # await light.setRgb(255, 0, 0)
    # logging.info(str(light._raw_state))
    # print(light)

    # print("sleep...")
    # await asyncio.sleep(1)

    # print("")
    # print("Set CW...")
    # await light.setCw(w=100,c=100)
    # logging.info(str(light._raw_state))
    # print(light)

    # print("sleep...")
    # await asyncio.sleep(1)

    print("")
    print("Turning OFF...")
    await light.off()
    logging.info(str(light._raw_state))
    print(light)

    print("Cleaning up...")
    await light.dispose()


async def ColorCycle():
    light = RGBCWBulb("10.0.0.21")
    print("Config Bulb...")

    print("")
    print("Turning ON...")
    await light.on()
    print(light)

    for x in range(0, 100, 1):
        print("")
        i = x / 100
        rgb = colorsys.hsv_to_rgb(i, 1.0, 255)
        print(f"Set Color {i} ({rgb!s})")
        await light.setRgb(*rgb, refreshState=False)
        await asyncio.sleep(0.1)

    print("")
    print("Turning OFF...")
    await light.off()
    logging.info(str(light._raw_state))
    print(light)

    print("Cleaning up...")
    await light.dispose()


# asyncio.run(Run())
asyncio.run(ColorCycle())
