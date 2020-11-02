
def addCheckSum(bytes) -> bytearray:
    """Adds a checksum byte to the end of a ByteArray"""
    checkByte = sum(bytes) & 0xFF
    bytes.append(checkByte)
    return bytes

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

def byteToPercent(byte):
    if byte > 255:
        byte = 255
    if byte < 0:
        byte = 0
    return int((byte * 100)/255)

def percentToByte(percent):
    if percent > 100:
        percent = 100
    if percent < 0:
        percent = 0
    return int((percent * 255)/100)