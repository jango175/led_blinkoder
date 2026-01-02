import subprocess
import re
import sys
from typing import Optional
import importlib
import time


def precise_sleep(duration, get_now=time.perf_counter):
  now = get_now()
  end = now + duration
  while now < end:
    now = get_now()


class TouchpadLEDCoder:
  def __init__(self):
    self.BRIGHT_VAL = [hex(val) for val in [31, 24, 1]]

    self.touchpad: Optional[str] = None
    self.keyboard: Optional[str] = None
    self.device_id: Optional[str] = None

    self.model = 'm433ia' # Model used in the derived script (with symbols)
    if len(sys.argv) > 1:
      self.model = sys.argv[1]

    self.model_layout = importlib.import_module('numpad_layouts.'+ self.model)
    self.tries = self.model_layout.try_times


  def find_devices(self):
    while self.tries > 0:
      keyboard_detected = 0
      touchpad_detected = 0

      with open('/proc/bus/input/devices', 'r') as f:
        lines = f.readlines()
        for line in lines:
          # Look for the touchpad
          if touchpad_detected == 0 and ("Name=\"ASUE" in line or "Name=\"ELAN" in line) and "Touchpad" in line:
            touchpad_detected = 1
            print(f'Detect touchpad from {line.strip()}')

          if touchpad_detected == 1:
            if "S: " in line:
              # search device id
              self.device_id=re.sub(r".*i2c-(\d+)/.*$", r'\1', line).replace("\n", "")
              print(f'Set touchpad device id {self.device_id} from {line.strip()}')

            if "H: " in line:
              self.touchpad = line.split("event")[1]
              self.touchpad = self.touchpad.split(" ")[0]
              touchpad_detected = 2
              print(f'Set touchpad id {self.touchpad} from {line.strip()}')

          # Look for the keyboard (numlock) # AT Translated Set OR Asus Keyboard
          if keyboard_detected == 0 and ("Name=\"AT Translated Set 2 keyboard" in line or "Name=\"Asus Keyboard" in line):
            keyboard_detected = 1
            print(f'Detect keyboard from {line.strip()}')

          if keyboard_detected == 1:
            if "H: " in line:
              self.keyboard = line.split("event")[1]
              self.keyboard = self.keyboard.split(" ")[0]
              keyboard_detected = 2
              print(f'Set keyboard {self.keyboard} from {line.strip()}')

          # Stop looking if both have been found #
          if keyboard_detected == 2 and touchpad_detected == 2:
            break

      if keyboard_detected != 2 or touchpad_detected != 2:
        tries -= 1
        if tries == 0:
          if keyboard_detected != 2:
            self.log.error("Can't find keyboard (code: %s)", keyboard_detected)
          if touchpad_detected != 2:
            self.log.error("Can't find touchpad (code: %s)", touchpad_detected)
          if touchpad_detected == 2 and not self.device_id.isnumeric():
            self.log.error("Can't find device id")
          sys.exit(1)
      else:
        break

      time.sleep(self.model_layout.try_sleep)


  def activate_numlock(self, brightness):
    numpad_cmd = "i2ctransfer -f -y " + self.device_id + " w13@0x15 0x05 0x00 0x3d 0x03 0x06 0x00 0x07 0x00 0x0d 0x14 0x03 " + self.BRIGHT_VAL[brightness] + " 0xad"
    subprocess.call(numpad_cmd, shell=True)


  def deactivate_numlock(self):
    numpad_cmd = "i2ctransfer -f -y " + self.device_id + " w13@0x15 0x05 0x00 0x3d 0x03 0x06 0x00 0x07 0x00 0x0d 0x14 0x03 0x00 0xad"
    subprocess.call(numpad_cmd, shell=True)


def main():
  common = importlib.import_module('common')
  msg = common.msg
  time_interval = common.time_interval
  header = common.header

  tpledc = TouchpadLEDCoder()
  tpledc.find_devices()
  tpledc.deactivate_numlock()
  precise_sleep(time_interval)

  # prepend header to the message
  msg = chr(header) + msg

  for c in msg:
    for i in range(8):
      bit = (ord(c) >> (7 - i)) & 1
      if bit == 1:
        tpledc.activate_numlock(2)
        # print("LED ON")
      else:
        tpledc.deactivate_numlock()
        # print("LED OFF")

      # print(f"{bit}, ", end='', flush=True)
      precise_sleep(time_interval)

    # print(f"Char: {intc(ord(c))}, '{c}'")

  tpledc.deactivate_numlock()
  print("Done.")


if __name__ == "__main__":
  main()
