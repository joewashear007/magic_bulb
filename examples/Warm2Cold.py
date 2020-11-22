import sys, os
sys.path.append(os.path.join(os.path.dirname( os.getcwd()), "magic_bulb") )

import magic_bulb
import asyncio
import logging
import colorsys

print(dir(magic_bulb))
logging.basicConfig(level=logging.INFO)


async def Run():
    light = magic_bulb.RBGCWBulb("10.0.0.26")
    print("Config Bulb...")

    print("")
    print("Turning ON...")
    await light.on()
    print(light)

    x = 335
    for x in range(153, 370, 10):
        for y in range(1, 255, 10):
            print("")
            print(f"Set Color: white color = {x}; brightness = {y}")
            await light.setCw(x, y, ensure=False)
            await asyncio.sleep(0.05)

    await asyncio.sleep(1)
    print("")
    print("Turning OFF...")
    await light.off()
    logging.info(str(light._raw_state))
    print(light)

    print("Cleaning up...")
    await light.dispose()

asyncio.run(Run())
