import cv2
import numpy as np
import time

N = 30
FPS = 60
WIDTH = 1920
HEIGHT = 1080


frame_count = 0
delay = 1.0 / FPS

cv2.namedWindow("ScreenOutput", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(
    "ScreenOutput",
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

while True:
    frame_count += 1

    if frame_count % N == 0:
        frame = np.full((HEIGHT, WIDTH, 3), 255, dtype=np.uint8)
    else:
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    cv2.imshow("ScreenOutput", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    time.sleep(delay)

cv2.destroyAllWindows()

