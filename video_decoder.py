import cv2 as cv
import importlib


class VideoDecoder:
  def __init__(self, filepath):
    self.filepath = filepath
    self.cap = cv.VideoCapture(self.filepath)
    if not self.cap.isOpened():
      print("Error opening video file")

    self.frame_rate = self.cap.get(cv.CAP_PROP_FPS)
    self.total_frames = round(self.cap.get(cv.CAP_PROP_FRAME_COUNT))
    self.current_frame = 0

    common = importlib.import_module('common')
    self.header = common.header
    self.time_interval = common.time_interval
    self.frame_bits_num_per_interval = round(self.time_interval * self.frame_rate)

    print(f"Frames per time interval: {self.frame_bits_num_per_interval}")
    print(f"Frame Rate: {self.frame_rate}, Total Frames: {self.total_frames}")


  def grab_frame_bits(self):
    frame_bits = []

    while self.current_frame < self.total_frames:
      frame_bit = self.decode_bit_from_frame()
      if frame_bit is None:
        break

      frame_bits.append(frame_bit)

    return frame_bits


  def wait_for_zero(self, frame_bits):
    for i, bit in enumerate(frame_bits):
      if bit == 0:
        frame_bits = frame_bits[i:]
        break

    return frame_bits


  def correct_frame_bits(self, frame_bits):
    corrected_frame_bits = frame_bits.copy()
    kill_while_loop = False
    kill_for_loop = False

    while kill_while_loop == False:
      for i in range(0, len(corrected_frame_bits), self.frame_bits_num_per_interval):
        interval_bits = corrected_frame_bits[i:i+self.frame_bits_num_per_interval]
        if len(interval_bits) < self.frame_bits_num_per_interval:
          kill_while_loop = True
          break

        if sum(interval_bits) != 0 or sum(interval_bits) != self.frame_bits_num_per_interval:
          majority_bit = 1 if sum(interval_bits) > (self.frame_bits_num_per_interval / 2) else 0
          for j in range(len(interval_bits) - 1, -1, -1):
            if interval_bits[j] != majority_bit:
              corrected_frame_bits.pop(i + j)
              kill_for_loop = True
              break

        if kill_for_loop:
          kill_for_loop = False
          break

        if i + self.frame_bits_num_per_interval >= len(corrected_frame_bits):
          kill_while_loop = True
          break

      for i, bit in enumerate(corrected_frame_bits):
        print(bit, end='' if (i + 1) % self.frame_bits_num_per_interval != 0 else '\n')
      print("")

    return corrected_frame_bits


  def find_header_in_frame_bits(self, frame_bits):
    header_frame_bits = []
    header_bits = []

    for c in chr(self.header):
      for i in range(8):
        bit = (ord(c) >> (7 - i)) & 1
        header_bits.append(bit)
        for _ in range(self.frame_bits_num_per_interval):
          header_frame_bits.append(bit)

    print(f"Header bits: {header_bits}")
    print(f"Header frame bits: {len(header_frame_bits)} bits")

    # Search for header in frame bits
    for i in range(len(frame_bits) - len(header_frame_bits) + 1):
      if frame_bits[i:i+len(header_frame_bits)] == header_frame_bits:
        print(f"Header found at frame index: {i}")
        return frame_bits[i:]


  def decode_bit_from_frame(self):
    ret, frame = self.cap.read()
    if not ret:
      return None # No more frames to read

    # Example decoding logic: Check the brightness of the center pixel
    height, width, _ = frame.shape
    center_pixel = frame[height // 2, width // 2]
    brightness = sum(center_pixel) / 3  # Average RGB value

    # Threshold to determine bit value
    bit = 1 if brightness > 128 else 0

    # cv.namedWindow('Frame', cv.WINDOW_NORMAL)
    # cv.putText(frame, f'Bit: {bit}', (100, 300), cv.FONT_HERSHEY_SIMPLEX, 10, (0, 255, 0), 20)
    # cv.imshow('Frame', frame)
    # cv.waitKey(0)

    self.current_frame += 1
    return bit


  def release(self):
    if self.cap.isOpened():
      self.cap.release()


  def __del__(self):
    self.release()


def main():
  # vd = VideoDecoder('Very secret message! (0xFF, 0.1s).mp4')
  vd = VideoDecoder('Secret (0xFF, 0.1s).mp4')
  # vd = VideoDecoder('20251213_220234.mp4')

  frame_bits = vd.grab_frame_bits()
  # frame_bits = vd.wait_for_zero(frame_bits)
  # frame_bits = vd.correct_frame_bits(frame_bits)
  print("Frame bits:")
  for i, bit in enumerate(frame_bits):
    print(bit, end='' if (i + 1) % vd.frame_bits_num_per_interval != 0 else '\n')
  print("")

  frame_bits = vd.find_header_in_frame_bits(frame_bits)
  frame_bits = vd.correct_frame_bits(frame_bits)

  bits = []
  for i, _ in enumerate(frame_bits):
    if i % vd.frame_bits_num_per_interval == 0:
      try:
        bits.append(frame_bits[i + vd.frame_bits_num_per_interval // 2])
      except IndexError:
        break

  print("Decoded bits:", bits)

  bytes = []
  for i in range(0, len(bits), 8):
    byte_bits = bits[i:i+8]
    if len(byte_bits) < 8:
      break
    byte_value = 0
    for j, b in enumerate(byte_bits):
      byte_value |= (b << (7 - j))
    bytes.append(byte_value)

  print("Decoded bytes:", bytes)
  bytes_as_chars = [chr(b) for b in bytes]
  print("Decoded message:", ''.join(bytes_as_chars))
  vd.release()

if __name__ == "__main__":
  main()