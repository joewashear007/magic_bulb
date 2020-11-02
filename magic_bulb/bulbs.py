from . import baseBulb
from . import helpers
import colorsys
import asyncio

class RBGCWBulb(baseBulb.BaseBulb):

    @property
    def _power_on_msg(self) -> bytearray: 
        return helpers.addCheckSum(bytearray([0x71, 0x23, 0x0f]))

    @property
    def _power_off_msg(self) -> bytearray: 
        return helpers.addCheckSum(bytearray([0x71, 0x24, 0x0f]))

    @property
    def _state_msg(self) -> bytearray: 
        return helpers.addCheckSum(bytearray([0x81, 0x8a, 0x8b]))

    @property
    def _msg_length(self) -> int: 
        return 14

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
        await self._send(helpers.addCheckSum(msg), refreshState)
        if(refreshState):
            await self.state()
        return self

    async def setCw(self, w=None, brightness=None, persist=True, refreshState=True):
        """
        * Cold-White on scale 1-100%
        * Brightness on scale 1-100%

        """

        warm_light = (255 * w) * brightness
        cold_light = (255 * (1 - w)) * brightness

        # assemble the message
        msg = bytearray([0x31] if persist else [0x41])  # 0: persistence
        # 1: red    - not used in white mode
        msg.append(0)
        # 2: green  - not used in white mode
        msg.append(0)
        # 3: blue   - not used in white mode
        msg.append(0)
        msg.append(int(warm_light or 0))                         # 4: warn white
        msg.append(int(cold_light or 0))                         # 5: cold white
        # 6: write mode - white mode 0x0f
        msg.append(0x0f)
        msg.append(0x0f)                                # 7: terminator bit
        await self._send(helpers.addCheckSum(msg), refreshState)
        if(refreshState):
            await self.state()
        return self
