import cv2
import numpy as np

class QRDetector:
    def __init__(self):
        self.detector = cv2.QRCodeDetector()

    def process(self, frame, center_x):
        retval, points = self.detector.detect(frame)
        
        if retval and points is not None:
            pts = points[0].astype(int)
            qr_cx = int(np.mean(pts[:, 0]))
            qr_cy = int(np.mean(pts[:, 1]))
            
            
            cv2.polylines(frame, [pts], True, (0, 255, 0), 3)
            cv2.circle(frame, (qr_cx, qr_cy), 5, (0, 0, 255), -1)
            cv2.line(frame, (center_x, qr_cy), (qr_cx, qr_cy), (255, 0, 0), 2)
            
            error = float(qr_cx - center_x)
            return True, error
            
        return False, 0.0
