import sys, os
sys.path.append(os.path.join(os.path.dirname( os.getcwd()), "magic_bulb") )

import magic_bulb
import asyncio
import logging
import colorsys

print(dir(magic_bulb))
logging.basicConfig(level=logging.DEBUG)


async def Run():
    light = magic_bulb.RBGCWBulb("10.0.0.21")
    print("Config Bulb...")

    print("")
    print("Turning ON...")
    await light.on()
    print(light)

    for x in range(0, 100, 10):
        for y in range(0, 100, 10):
            print("")
            i = x / 100
            j = y / 100
            print(f"Set Color: white color = {i}; brightness = {j}")
            await light.setCw(i, j, refreshState=False)
            await asyncio.sleep(0.1)

    print("")
    print("Turning OFF...")
    await light.off()
    logging.info(str(light._raw_state))
    print(light)

    print("Cleaning up...")
    await light.dispose()

asyncio.run(Run())
