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
    await light.state()


    print("Turning ON...")
    if not light.is_on:
        await light.on()
    print(light)
    print()
    print("======================================================")

    for x in range(50, 250, 50):
        print("")
        print("")
        print(f"---------------------- Iteration: x = {x} --------------------")
        await light.setCw(brightness= x)
        print(light)
        if light.brightness != x:
            raise Exception("Failed to Match")
        print(f" > Light Brightness: {light.brightness} [before]")
        # await light.state()
        # print(f" > Light Brightness: {light.brightness} [after]")
        # print(light)
        # await asyncio.sleep(5)
        # await light.state()
        # print(f" > Light Brightness: {light.brightness} [sleep]")
        # print(light)
        input("Press Enter to continue...")

    # print("Turning OFF...")
    # await light.off()
    # await light.state()
    # print(light)

    print("Cleaning up...")
    await light.dispose()


asyncio.run(ColorCycle())