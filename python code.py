import cv2
import numpy as np
import serial
import time


arduino = serial.Serial('COM3', 115200, timeout=0.05)  
time.sleep(2) 

cap = cv2.VideoCapture(0)


lower_red1 = np.array([0, 120, 70])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([170, 120, 70])
upper_red2 = np.array([180, 255, 255])
min_contour_area = 700

sim_pan = 90
sim_tilt = 90
gain_pan = 40.0
gain_tilt = 40.0
max_step = 5
dead_zone_frac = 0.03

invert_x = False
invert_y = False
rotate90 = False
show_debug = True

prev_pan = sim_pan
prev_tilt = sim_tilt
alpha = 0.6

print("Tracking Red Object. Press 'q' to quit, 's' to FIRE.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    if rotate90:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

    h, w = frame.shape[:2]
    center_x, center_y = w // 2, h // 2
    dead_x = int(w * dead_zone_frac)
    dead_y = int(h * dead_zone_frac)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cx = None; cy = None; found = False

    if contours:
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        if area > min_contour_area:
            M = cv2.moments(c)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                found = True
                x, y, ww, hh = cv2.boundingRect(c)
                cv2.rectangle(frame, (x,y), (x+ww, y+hh), (0,255,0), 2)
                cv2.circle(frame, (cx, cy), 6, (0,0,255), -1)

    cv2.line(frame, (center_x-15, center_y), (center_x+15, center_y), (255,255,255), 1)
    cv2.line(frame, (center_x, center_y-15), (center_x, center_y+15), (255,255,255), 1)

    fire_flag = 0   

    if found:
        dx = cx - center_x
        dy = cy - center_y

        nx = float(dx) / float(center_x)
        ny = float(dy) / float(center_y)

        if invert_x: nx = -nx
        if invert_y: ny = -ny

        if abs(dx) < dead_x: nx = 0.0
        if abs(dy) < dead_y: ny = 0.0

        target_pan = 90 + int(-nx * gain_pan)
        target_tilt = 90 + int(ny * gain_tilt)

        delta_pan = np.clip(target_pan - prev_pan, -max_step, max_step)
        delta_tilt = np.clip(target_tilt - prev_tilt, -max_step, max_step)
        sim_pan = int(prev_pan + delta_pan)
        sim_tilt = int(prev_tilt + delta_tilt)

        sim_pan = int(alpha * prev_pan + (1-alpha) * sim_pan)
        sim_tilt = int(alpha * prev_tilt + (1-alpha) * sim_tilt)

        prev_pan = sim_pan
        prev_tilt = sim_tilt

        
        cmd = f"{sim_pan},{sim_tilt},{fire_flag}\n"
        arduino.write(cmd.encode())

        if show_debug:
            cv2.putText(frame, f"dx={dx} dy={dy}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
            cv2.putText(frame, f"sim_pan={sim_pan} sim_tilt={sim_tilt}", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    else:
        cv2.putText(frame, "No target", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    cv2.imshow("Tracker", frame)
    cv2.imshow("Mask", mask)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):  
        fire_flag = 1
        cmd = f"{sim_pan},{sim_tilt},{fire_flag}\n"
        arduino.write(cmd.encode())
        print("FIRE!")

cap.release()
arduino.close()
cv2.destroyAllWindows()


