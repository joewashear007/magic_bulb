from . import baseBulb
from . import helpers
import logging
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
        await self._send(helpers.addCheckSum(msg))
        self._raw_state[9] = 0
        self._raw_state[11] = 0
        self._raw_state[6] = int(r or 0)
        self._raw_state[7] = int(g or 0)
        self._raw_state[8] = int(b or 0)
        if(refreshState):
            await self.state()
        return self

    async def setCw(self, w=None, brightness=None, persist=True, refreshState=True):
        """
        * Cold-White in mireds 153-370
        * Brightness on scale 0-255
        """
        if w is None:
            w = self.color_temp
            logging.info(f"Color Temp is not given, using existing color temp {w}")

        if w < 153 or w > 370:
            raise Exception(f"Color Temp '{w}' out of range [137-370]")
        if brightness < 0 or brightness > 256:
            raise Exception(f"Brightness '{brightness}' out of range [0-256]")

        color_ratio = (w - 153)/(370-153)

        warm_light = int(color_ratio * brightness)
        cold_light = int((1-color_ratio) * brightness)

        logging.info(f"Setting Color temp: {w} mireds & {brightness}")
        logging.info(f" -> [153-({w})-370] => {round(color_ratio * 100, 2)}%")
        logging.info(f" -> Warm: {warm_light} ({color_ratio} * {brightness})")
        logging.info(f" -> Cold: {cold_light} ((1 - {color_ratio}) * {brightness})")

        # assemble the message
        msg = bytearray([0x31] if persist else [0x41])  # 0: persistence
        # 1: red    - not used in white mode
        msg.append(0)
        # 2: green  - not used in white mode
        msg.append(0)
        # 3: blue   - not used in white mode
        msg.append(0)
        # 4: warn white
        msg.append(int(warm_light or 0))
        # 5: cold white
        msg.append(int(cold_light or 0))
        # 6: write mode - white mode 0x0f
        msg.append(0x0f)
        msg.append(0x0f)                                # 7: terminator bit
        await self._send(helpers.addCheckSum(msg))
        self._raw_state[9] = warm_light
        self._raw_state[11] = cold_light
        self._raw_state[6] = 0
        self._raw_state[7] = 0
        self._raw_state[8] = 0
        logging.info(f"Set [warm,cold] = [{self._raw_state[9]},{self._raw_state[11]}]")
        logging.info(f"Set CW Bytes:           {self._raw_state}")
        if(refreshState):
            await self.state()
        return self
