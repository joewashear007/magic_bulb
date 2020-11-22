import sys, os, random
sys.path.append(os.path.join(os.path.dirname( os.getcwd()), "magic_bulb") )


import magic_bulb
import asyncio
import logging
import colorsys

logging.basicConfig(level=logging.INFO, format=logging.BASIC_FORMAT)
logging.root.setLevel(logging.INFO)

async def ColorCycle():
    print("")
    light = magic_bulb.RBGCWBulb("10.0.0.26")

    print("Turning ON...")
    await light.on()
    await light.state()
    print(light)

    for x in range(0, 100, 2):
        print("")
        i = x / 100
        # brightness=random.randint(25,100)
        brightness=255
        rgb = colorsys.hsv_to_rgb(i, 1.0, 100)
        print(f"Set Color {i}, {brightness} ({rgb!s})")
        await light.setRgb(*rgb, brightness=brightness)
        print(light)
        await asyncio.sleep(0.05)

    print("")
    print("Turning OFF...")
    await light.off()
    await light.state()
    print(light)

    print("Cleaning up...")
    await light.dispose()


asyncio.run(ColorCycle())