import sys, os
sys.path.append(os.path.join(os.path.dirname( os.getcwd()), "magic_bulb") )


import magic_bulb
import asyncio
import logging
import colorsys

print(dir(magic_bulb))
logging.basicConfig(level=logging.DEBUG)

async def ColorCycle():
    light = magic_bulb.RBGCWBulb("10.0.0.21")
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


asyncio.run(ColorCycle())