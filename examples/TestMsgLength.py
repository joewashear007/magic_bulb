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
    light = magic_bulb.RBGCWBulb("10.0.0.21")


    print("Turning ON...")
    await light.on(wait=True)
    await light.state()
    print(light)

    print("")
    print("Turning OFF...")
    await light.off(wait=True)
    await light.state()
    print(light)

    print("Cleaning up...")
    await light.dispose()


asyncio.run(ColorCycle())