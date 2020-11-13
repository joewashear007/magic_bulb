import logging
import colorsys
import asyncio
from time import sleep
from abc import ABC, abstractmethod, abstractproperty
from timeit import default_timer as timer
from datetime import timedelta

logging.basicConfig(format='%(levelname)s %(message)s', level=logging.INFO)


class BaseBulb(ABC):
    """Abstract class for the Magic LED bulbs
    Should be able to subclass for the different type of bulbs
    """

    @abstractproperty
    def _power_on_msg(self) -> bytearray:
        """The Byte Array to turn on the light"""
        pass

    @abstractproperty
    def _power_off_msg(self) -> bytearray:
        """The Byte Array to turn off the light"""
        pass

    @abstractproperty
    def _state_msg(self) -> bytearray:
        """The Byte Array to get the state of the light"""
        pass

    @abstractproperty
    def _msg_length(self) -> int:
        """The length of expected messages from the light"""
        pass

    def __init__(self, ipAddr, port=5577):
        self.ipAddress = ipAddr
        self.port = port
        self._reader = None
        self._writer = None
        self._raw_state = bytearray(14)

    def __del__(self):
        if(self._writer is not None):
            asyncio.ensure_future(self.dispose())

    async def dispose(self):
        """closes connection """
        if(self._writer is not None):
            logging.debug(
                f"Disposing Connection [{self.ipAddress}:{self.port}]")
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

    async def _send(self, msg, wait=False):
        """Send Command to Light Bulb"""
        # if (self._writer is None):
        logging.debug(
            f"Creating Connection to light [{self.ipAddress}:{self.port}]")
        (reader, writer) = await asyncio.open_connection(self.ipAddress, self.port)

        start = timer()
        logging.debug(
            f"Request Data: '{msg!r}' to [{self.ipAddress}:{self.port}] {start}")
        writer.write(msg)
        await writer.drain()
        reqEnd = timer()
        if (wait):
            data = await reader.read(self._msg_length)
        else:
            data = None
        writer.close()
        await writer.wait_closed()
        end = timer()
        logging.debug(
            f"Response Data: '{data!r}' to [{self.ipAddress}:{self.port}] [request End {reqEnd} -> {timedelta(seconds=reqEnd-start)}; End {end} -> {timedelta(seconds=end-start)}")
        return data

    async def state(self):
        """
        Get the state of the light bulb

        typical response:
        #pos  0  1  2  3  4  5  6  7  8  9 10
             66 01 24 39 21 0a ff 00 00 01 99
              |  |  |  |  |  |  |  |  |  |  |
              |  |  |  |  |  |  |  |  |  |  checksum
              |  |  |  |  |  |  |  |  |  warmwhite
              |  |  |  |  |  |  |  |  blue
              |  |  |  |  |  |  |  green 
              |  |  |  |  |  |  red
              |  |  |  |  |  speed: 0f = highest f0 is lowest
              |  |  |  |  <don't know yet>
              |  |  |  preset pattern             
              |  |  off(23)/on(24)
              |  type
              msg head

        response from a 5-channel LEDENET controller:
        pos  0  1  2  3  4  5  6  7  8  9 10 11 12 13
            81 25 23 61 21 06 38 05 06 f9 01 00 0f 9d
             |  |  |  |  |  |  |  |  |  |  |  |  |  |
             |  |  |  |  |  |  |  |  |  |  |  |  |  checksum
             |  |  |  |  |  |  |  |  |  |  |  |  color mode (f0 colors were set, 0f whites, 00 all were set)
             |  |  |  |  |  |  |  |  |  |  |  cold-white
             |  |  |  |  |  |  |  |  |  |  <don't know yet>
             |  |  |  |  |  |  |  |  |  warmwhite
             |  |  |  |  |  |  |  |  blue
             |  |  |  |  |  |  |  green
             |  |  |  |  |  |  red
             |  |  |  |  |  speed: 0f = highest f0 is lowest
             |  |  |  |  <don't know yet>
             |  |  |  preset pattern
             |  |  off(23)/on(24)
             |  type
             msg head

        """
        raw_response = await self._send(self._state_msg, wait=True)
        self._raw_state = bytearray(raw_response)
        logging.debug(str(self._raw_state))
        return self._raw_state

    async def on(self, refreshState=False):
        """
        Turn the light bulb on

        * ON = 0x23
        * OFF = 0x24
        """
        await self._send(self._power_on_msg)
        self._raw_state[2] = 0x23
        if(refreshState):
            await self.state()
        return self

    async def off(self, refreshState=False):
        """
        Turn the light bulb on

        * ON = 0x23
        * OFF = 0x24
        """
        await self._send(self._power_off_msg)
        self._raw_state[2] = 0x24
        if(refreshState):
            await self.state()
        return self

    @property
    def is_on(self) -> bool:
        """Is the light on? 
        you will want to call state() first
        * ON = 0x23
        * OFF = 0x24
        """
        return self._raw_state[2] == 0x23

    @property
    def mode(self) -> str:
        mode = "unknown"
        if self._raw_state[3] in [0x61, 0x62]:
            if (self._raw_state[9] != 0 or self._raw_state[11] != 0):
                mode = "white"
            else:
                mode = "color"
        elif self._raw_state[3] == 0x60:
            mode = "custom"
        elif self._raw_state[3] == 0x41:
            mode = "color"
        # elif PresetPattern.valid(pattern_code):
        #     mode = "preset"
        # elif BuiltInTimer.valid(pattern_code):
        #     mode = BuiltInTimer.valtostr(pattern_code)
        return mode

    @property
    def rgb(self):
        """Returns an rgb tuple"""
        return (self._raw_state[6], self._raw_state[7], self._raw_state[8])

    @property
    def color_temp(self):
        """Return the CT color value in mireds."""
        if self.mode == "white":
            # these calulatoins could be bad...
            # the sum of these never goes over 255.. so brightness is the sum scaled between 0-255
            b = int(self._raw_state[9]) + int(self._raw_state[11])

            # should give values in precents
            warm = (self._raw_state[9]/b)/255
            logging.info(
                f"-- Calculate Brightness [{self._raw_state[9]}, {self._raw_state[11]}] -> ratio: {warm} -> {153 + int((370-153) * warm)}")
            return 153 + int((370-153) * warm)
        else:
            return None

    @property
    def brightness(self) -> int:
        """Return current brightness 0-255.

        For white mood return current led level. 
        For RGB calculate the HSV and return the 'value'.
        """
        if self.mode == "white":
            return max(int(self._raw_state[9]) + int(self._raw_state[11]), 255)
        else:
            _, _, v = colorsys.rgb_to_hsv(*self.rgb)
            return v * 2.55

    def __str__(self):
        out = f"{self.__class__.__name__} [{self.ipAddress}:{self.port}] "
        if self.is_on:
            out += "ON"
        else:
            out += f"OFF ({self._raw_state[2]})"

        if self.mode == "color":
            out += f" | COLOR {self.rgb}"
        elif self.mode == "white":
            out += f" | WHITE ({int(self._raw_state[9]) + int(self._raw_state[11])})"
        out += f" {self.brightness}% "

        mode_str = " Raw State: "
        for _r in self._raw_state:
            mode_str += str(_r) + ","
        return f"{out} [{mode_str}]"
