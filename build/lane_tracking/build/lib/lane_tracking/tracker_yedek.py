import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import cv2
import numpy as np

class LaneTracker(Node):
    def __init__(self):
        super().__init__('lane_tracker_node')
        
        # error değerlerini yayınlayacağımız İKİ AYRI kanal (hsv ve otsu için ayrı kanallar)
        self.pub_otsu = self.create_publisher(Float32, '/lane_error_otsu', 10)
        self.pub_hsv = self.create_publisher(Float32, '/lane_error_hsv', 10)
        
        # V4L2 arka ucu sart. Varsayilan GStreamer arka ucu bu kamerada
        # pipeline kuramiyor ("Internal data stream error") ve tek kare bile
        # gelmiyor, dugum sadece "Kamerada sorun var" basip duruyor.
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

        # Kamera 320x240 DESTEKLEMIYOR. Desteklenenler:
        #   MJPG 1920x1080 / 1280x720 / 1280x400 / 1280x320 / 640x480
        #   YUYV 640x360
        # (v4l2-ctl -d /dev/video0 --list-formats-ext)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # 0.1 saniyede bir kameradan görüntü çek
        self.timer = self.create_timer(0.1, self.timer_callback)
   

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warning("Kamerada sorun var")
            return
            
        try:
           
      
    
            height, width, _ = frame.shape
            center_x = width // 2  # Genişliğin tam yarısı 
            
            display_frame = frame.copy()
            
           
            # YÖNTEM 1: OTSU  
     
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            M_otsu = cv2.moments(thresh_otsu)
            if M_otsu["m00"] > 0:
                cx_otsu = int(M_otsu["m10"] / M_otsu["m00"])
                cy_otsu = int(M_otsu["m01"] / M_otsu["m00"])
                
                # Otsu'nun bulduğu merkezi ve sapma çizgisini çiz (kırmızı)
                cv2.circle(display_frame, (cx_otsu, cy_otsu), 8, (0, 0, 255), -1) 
                cv2.line(display_frame, (center_x, cy_otsu), (cx_otsu, cy_otsu), (0, 0, 255), 2)
                
                # Otsu yayını
                error_otsu = float(cx_otsu - center_x)
                msg_otsu = Float32()
                msg_otsu.data = error_otsu
                self.pub_otsu.publish(msg_otsu)
                
           
            # YÖNTEM 2: HSV + GÜRÜLTÜ FİLTRELEME 
          
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Renk Filtresi (SİYAH renge ayarlı)
            lower_color = np.array([0, 0, 0])
            upper_color = np.array([180, 255, 50])
            mask_hsv = cv2.inRange(hsv, lower_color, upper_color)
            
            # Gürültü temizleme 
            kernel = np.ones((5,5), np.uint8)
            mask_hsv = cv2.erode(mask_hsv, kernel, iterations=1)
            mask_hsv = cv2.dilate(mask_hsv, kernel, iterations=1)
            
            # En büyük şeridi (konturu) bul
            contours, _ = cv2.findContours(mask_hsv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) > 0:
                biggest_contour = max(contours, key=cv2.contourArea)
                M_hsv = cv2.moments(biggest_contour)
                
                if M_hsv["m00"] > 0:
                    cx_hsv = int(M_hsv["m10"] / M_hsv["m00"])
                    cy_hsv = int(M_hsv["m01"] / M_hsv["m00"])
                    
                    # HSV merkezini ve sapma çizgisi (yeşil)
                    cv2.circle(display_frame, (cx_hsv, cy_hsv), 10, (0, 255, 0), -1)
                    cv2.line(display_frame, (center_x, cy_hsv), (cx_hsv, cy_hsv), (0, 255, 0), 2) 
                    
                    # HSV yayını
                    error_hsv = float(cx_hsv - center_x)
                    msg_hsv = Float32()
                    msg_hsv.data = error_hsv
                    self.pub_hsv.publish(msg_hsv)
            
            # Aracın ve Kameranın tam merkez çizgisi (MAVİ)
            cv2.line(display_frame, (center_x, 0), (center_x, height), (255, 0, 0), 2)
            
            cv2.imshow(" Otsu", thresh_otsu)
            cv2.imshow(" HSV", mask_hsv)
            cv2.imshow("(Kirmizi: Otsu , Yesil: HSV)", display_frame)
            cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f"Görüntü işleme hatası: {e}")
            
    def destroy_node(self):
        self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    lane_tracker = LaneTracker()
    rclpy.spin(lane_tracker)
    lane_tracker.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
