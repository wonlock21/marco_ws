import cv2
import numpy as np

from .opencl_lane import OpenClLaneMask

class LaneDetector:
    def __init__(self, use_opencl=False):
        self.use_opencl = use_opencl
        self.gpu_mask = OpenClLaneMask() if use_opencl else None
        self.lower_color = np.array([0, 0, 0])
        self.upper_color = np.array([180, 255, 50])
        self.kernel = np.ones((5, 5), np.uint8)

    def process(self, frame, center_x):
        if self.use_opencl:
            mask = self.gpu_mask.process(
                frame, value_max=int(self.upper_color[2]))
        else:
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(
                hsv_frame, self.lower_color, self.upper_color)
            mask = cv2.erode(mask, self.kernel, iterations=1)
            mask = cv2.dilate(mask, self.kernel, iterations=1)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 0:
            biggest_contour = max(contours, key=cv2.contourArea)
            M = cv2.moments(biggest_contour)
            
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Görselleştirme çizimleri
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)
                cv2.line(frame, (center_x, cy), (cx, cy), (0, 255, 0), 2)
                
                error = float(cx - center_x)
                return True, error
                
        return False, 0.0
