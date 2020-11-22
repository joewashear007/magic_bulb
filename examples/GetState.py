import sys, os, random
sys.path.append(os.path.join(os.path.dirname( os.getcwd()), "magic_bulb") )


import magic_bulb
import asyncio
import logging
import colorsys

logging.basicConfig(level=logging.INFO, format=logging.BASIC_FORMAT)
logging.root.setLevel(logging.INFO)

async def ColorCycle():
    light = magic_bulb.RBGCWBulb("10.0.0.26")

    print("")
    await light.state()
    print(f"> Light Brightness: {light.brightness}")
    print(light)

    print("")
    print("Cleaning up...")
    await light.dispose()


asyncio.run(ColorCycle())