import logging
import colorsys
import asyncio
from time import sleep

logging.basicConfig(format='%(levelname)s %(message)s', level=logging.INFO)


class LedBulb():
    def __init__(self, ipAddr, port=5577, timeout=5):
        self.ipAddress = ipAddr
        self.port = port
        self.reader = None
        self.writer = None
        self.rawState = None
        self.MessageLength = 14
        self.StateMessage = self.addCheckSum(bytearray([0x81, 0x8a, 0x8b]))
        self.PowerOn = self.addCheckSum(bytearray([0x71, 0x23, 0x0f]))
        self.PowerOff = self.addCheckSum(bytearray([0x71, 0x24, 0x0f]))

    async def setup(self):
        logging.debug(
            f"Creating Connection to light [{self.ipAddress}:{self.port}]")
        reader, writer = await asyncio.open_connection(self.ipAddress, self.port)
        self.reader = reader
        self.writer = writer

    def __del__(self):
        if(self.writer is not None):
            asyncio.ensure_future(self.dispose())

    async def dispose(self):
        if(self.writer is not None):
            logging.debug(
                f"Disposing Connection [{self.ipAddress}:{self.port}]")
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None
            self.reader = None

    async def _send(self, msg, refreshState=True):
        if (self.writer is None):
            logging.debug(f"Creating Connection to light [{self.ipAddress}:{self.port}]")
            (self.reader, self.writer) = await asyncio.open_connection(self.ipAddress, self.port)

        logging.debug(
            f"Request Data: '{msg!r}' to [{self.ipAddress}:{self.port}]")
        self.writer.write(msg)
        await self.writer.drain()
        if(refreshState):
            data = await self.reader.read(self.MessageLength)
            logging.debug(
                f"Response Data: '{data!r}' to [{self.ipAddress}:{self.port}]")
            return data

    async def getState(self):
        self.rawState = await self._send(self.StateMessage)
        logging.info(str(self.rawState))
        return self.rawState

    async def on(self, refreshState=True):
        await self._send(self.PowerOn)
        if(refreshState):
            await asyncio.sleep(1)
            await self.getState()

    async def off(self, refreshState=True):
        await self._send(self.PowerOff)
        if(refreshState):
            await asyncio.sleep(1)
            await self.getState()

    async def setRgbw(self, r=None, g=None, b=None, w=None, persist=True, brightness=None, retry=2, w2=None):
        """
        # sample message for 9-byte LEDENET protocol (w/ checksum at end)
        #  0  1  2  3  4  5  6  7
        # 31 bc c1 ff 00 00 f0 0f
        #  |  |  |  |  |  |  |  |
        #  |  |  |  |  |  |  |  terminator
        #  |  |  |  |  |  |  write mode (f0 colors, 0f whites, 00 colors & whites)
        #  |  |  |  |  |  cold white
        #  |  |  |  |  warm white
        #  |  |  |  blue
        #  |  |  green
        #  |  red
        #  persistence (31 for true / 41 for false)
        #
        """
        if (r or g or b) and (w or w2) and not self.IsRGBWCapable:
            raise Exception("RGBW command sent to non-RGBW device")

        if brightness != None:
            hsv = colorsys.rgb_to_hsv(r, g, b)
            (r, g, b) = colorsys.hsv_to_rgb(hsv[0], hsv[1], brightness)

        if self.UseOriginalLEDENET:
            msg = bytearray([0x56])
            msg.append(int(r))
            msg.append(int(g))
            msg.append(int(b))
            msg.append(0xaa)
        else:
            # assemble the message
            if persist:
                msg = bytearray([0x31])
            else:
                msg = bytearray([0x41])

            if r is not None:
                msg.append(int(r))
            else:
                msg.append(int(0))
            if g is not None:
                msg.append(int(g))
            else:
                msg.append(int(0))
            if b is not None:
                msg.append(int(b))
            else:
                msg.append(int(0))
            if w is not None:
                msg.append(int(w))
            else:
                msg.append(int(0))

            if self.UseLEDENET:
                # LEDENET devices support two white outputs for cold and warm. We set
                # the second one here - if we're only setting a single white value,
                # we set the second output to be the same as the first
                if w2 is not None:
                    msg.append(int(w2))
                elif w is not None:
                    msg.append(int(w))
                else:
                    msg.append(0)

            # write mask, default to writing color and whites simultaneously
            write_mask = 0x00
            # rgbwprotocol devices always overwrite both color & whites
            if not self.UsesRGBWProtocol:
                if w is None and w2 is None:
                    # Mask out whites
                    write_mask |= 0xf0
                elif r is None and g is None and b is None:
                    # Mask out colors
                    write_mask |= 0x0f
            msg.append(write_mask)
            # Message terminator
            msg.append(0x0f)
        await self._send(LedBulb.addCheckSum(msg))
        await asyncio.sleep(1)
        await self.getState()
        await asyncio.sleep(1)
        await self.getState()
        await asyncio.sleep(1)
        await self.getState()
        await asyncio.sleep(1)
        await self.getState()
        await asyncio.sleep(1)
        await self.getState()

    async def setRgb(self, r=None, g=None, b=None, brightness=None, persist=True, refreshState=True):
        if brightness != None:
            hsv = colorsys.rgb_to_hsv(r, g, b)
            (r, g, b) = colorsys.hsv_to_rgb(hsv[0], hsv[1], brightness)

        # assemble the message
        msg = bytearray([0x31] if persist else [0x41])  # 0: persistence
        msg.append(int(r or 0))                         # 1: red
        msg.append(int(g or 0))                         # 2: green
        msg.append(int(b or 0))                         # 3: blue
        # 4: warn white - not use in RGB
        msg.append(0)
        # 5: cold white - not use in RGB
        msg.append(0)
        # 6: write mode - color 0xf0
        msg.append(0xf0)
        msg.append(0x0f)                                # 7: terminator bit
        await self._send(LedBulb.addCheckSum(msg), refreshState)
        if(refreshState):
            await asyncio.sleep(1)
            await self.getState()

    async def setCw(self, w=None, c=None, brightness=None, persist=True, refreshState=True):
        # assemble the message
        msg = bytearray([0x31] if persist else [0x41])  # 0: persistence
        # 1: red    - not used in white mode
        msg.append(0)
        # 2: green  - not used in white mode
        msg.append(0)
        # 3: blue   - not used in white mode
        msg.append(0)
        msg.append(int(w or 0))                         # 4: warn white
        msg.append(int(c or 0))                         # 5: cold white
        # 6: write mode - white mode 0x0f
        msg.append(0x0f)
        msg.append(0x0f)                                # 7: terminator bit
        await self._send(LedBulb.addCheckSum(msg))
        if(refreshState):
            await asyncio.sleep(1)
            await self.getState()

    @property
    def UsesRGBWProtocol(self):
        """Devices that don't require a separate rgb/w bit"""
        return self.rawState[1] == 0x04 or self.rawState[1] == 0x33 or self.rawState[1] == 0x81

    @property
    def IsRGBWCapable(self):
        """Devices that actually support rgbw"""
        return (self.rawState[1] == 0x04
                or self.rawState[1] == 0x25
                or self.rawState[1] == 0x33
                or self.rawState[1] == 0x81
                or self.rawState[1] == 0x44)

    @property
    def UseLEDENET(self):
        """Devices that use an 8-byte protocol"""
        return (self.rawState[1] == 0x25
                or self.rawState[1] == 0x27
                or self.rawState[1] == 0x35)

    @property
    def UseOriginalLEDENET(self):
        """Devices that use the original LEDENET protocol"""
        return (self.rawState[1] == 0x01)

    @property
    def PowerState(self):
        """The Current Preset Pattern"""
        return self.rawState[2]

    @property
    def isOn(self):
        """Is the light on?"""
        return self.PowerState == 0x23

    @property
    def isOff(self):
        """Is the light off"""
        return self.PowerState == 0x24

    @property
    def Pattern(self):
        """The Current Preset Pattern"""
        return (self.rawState[3])

    @property
    def rgb(self):
        """Returns an rgb tuple"""
        return (self.rawState[6], self.rawState[7], self.rawState[8])

    @property
    def WhiteLevel(self):
        return self.rawState[9]

    @property
    def WhitePercentage(self):
        return LedBulb.byteToPercent(self.rawState[9])

    @property
    def Delay(self):
        return self.rawState[5]

    @property
    def brightness(self):
        """Return current brightness 0-255.

        For warm white return current led level. For RGB
        calculate the HSV and return the 'value'.
        """
        if self.mode == "ww":
            return int(self.WhiteLevel)
        else:
            _, _, v = colorsys.rgb_to_hsv(*self.rgb)
            return v

    @property
    def mode(self):
        mode = "unknown"
        if self.Pattern in [0x61, 0x62]:
            if self.IsRGBWCapable:
                mode = "color"
            elif self.WhiteLevel != 0:
                mode = "ww"
            else:
                mode = "color"
        elif self.Pattern == 0x60:
            mode = "custom"
        elif self.Pattern == 0x41:
            mode = "color"
        # elif PresetPattern.valid(pattern_code):
        #     mode = "preset"
        # elif BuiltInTimer.valid(pattern_code):
        #     mode = BuiltInTimer.valtostr(pattern_code)
        return mode

    def __str__(self):
        power_str = "Unknown power state"
        if self.isOn:
            power_str = "ON "
        elif self.isOff:
            power_str = "OFF "

        # delay = rx[5]
        # speed = utils.delayToSpeed(delay)
        if self.mode == "color":
            mode_str = f"Color: {self.rgb}"
            if self.IsRGBWCapable:
                mode_str += f" White: {self.WhiteLevel}"
            else:
                mode_str += f" Brightness: {self.brightness}"
        elif self.mode == "ww":
            mode_str = f"Warm White: {self.WhitePercentage}%"
        # elif mode == "preset":
        #     pat = PresetPattern.valtostr(pattern)
        #     mode_str = "Pattern: {} (Speed {}%)".format(pat, speed)
        # elif mode == "custom":
        #     mode_str = "Custom pattern (Speed {}%)".format(speed)
        # elif BuiltInTimer.valid(pattern):
        #     mode_str = BuiltInTimer.valtostr(pattern)
        else:
            mode_str = f"Unknown mode 0x{self.Pattern}"
        if self.Pattern == 0x62:
            mode_str += " (tmp)"
        rawStateStr = " | raw state:"
        for _r in self.rawState:
            rawStateStr += str(_r) + ","
        return f"{power_str} [{mode_str} {rawStateStr}]"

    @staticmethod
    def addCheckSum(bytes):
        csum = sum(bytes) & 0xFF
        bytes.append(csum)
        return bytes

    @staticmethod
    def delayToSpeed(delay):
        max_delay = 0x1f
        # speed is 0-100, delay is 1-31
        # 1st translate delay to 0-30
        delay = delay - 1
        if delay > max_delay - 1:
            delay = max_delay - 1
        if delay < 0:
            delay = 0
        inv_speed = int((delay * 100)/(max_delay - 1))
        speed = 100-inv_speed
        return speed

    @staticmethod
    def speedToDelay(speed):
        # speed is 0-100, delay is 1-31
        max_delay = 0x1f
        if speed > 100:
            speed = 100
        if speed < 0:
            speed = 0
        inv_speed = 100-speed
        delay = int((inv_speed * (max_delay-1))/100)
        # translate from 0-30 to 1-31
        delay = delay + 1
        return delay

    @staticmethod
    def byteToPercent(byte):
        if byte > 255:
            byte = 255
        if byte < 0:
            byte = 0
        return int((byte * 100)/255)

    @staticmethod
    def percentToByte(percent):
        if percent > 100:
            percent = 100
        if percent < 0:
            percent = 0
        return int((percent * 255)/100)


async def Run():
    light = LedBulb("10.0.0.21")
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
    # logging.info(str(light.rawState))
    # print(light)

    # print("sleep...")
    # await asyncio.sleep(1)

    # print("")
    # print("Set CW...")
    # await light.setCw(w=100,c=100)
    # logging.info(str(light.rawState))
    # print(light)

    # print("sleep...")
    # await asyncio.sleep(1)

    print("")
    print("Turning OFF...")
    await light.off()
    logging.info(str(light.rawState))
    print(light)

    print("Cleaning up...")
    await light.dispose()


async def ColorCycle():
    light = LedBulb("10.0.0.21")
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
    logging.info(str(light.rawState))
    print(light)

    print("Cleaning up...")
    await light.dispose()


# asyncio.run(Run())
asyncio.run(ColorCycle())
