import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import cv2
import numpy as np

class LaneTracker(Node):
    def __init__(self):
        super().__init__('lane_tracker_node')

        # --- DURUM VE QR DEĞİŞKENLERİ ---
        self.state = "QR_MODU"  # Kesinlikle QR modu ile başlar
        self.qr_detector = cv2.QRCodeDetector()
        self.QR_AREA_THRESHOLD = 25000.0  # Geçiş alanı eşiği

        # Otsu yayıncısı kaldırıldı, sadece HSV kaldı.
        # controller.py'nin bu topiği dinlediğinden emin olmalısın.
        self.pub_hsv = self.create_publisher(Float32, '/lane_error_hsv', 10)

        # Kamera bağlantısı (V4L2 arka ucu)
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # 0.1 saniyede bir kameradan görüntü çek
        self.timer = self.create_timer(0.1, self.timer_callback)

    def process_qr_position(self, frame):
        height, width = frame.shape[:2]
        cam_cX = int(width / 2)
        
        success, bbox = self.qr_detector.detect(frame)
        if success and bbox is not None:
            corners = bbox[0].astype(int)
            qr_cX = int(np.mean(corners[:, 0]))
            error_x = qr_cX - cam_cX
            qr_area = cv2.contourArea(corners)
            return error_x, qr_area, frame
        return None, None, frame

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warning("Kamerada sorun var")
            return

        try:
            # --- YENİ EKLENEN KISIM: ANA GÖRÜNTÜYE BLUR AT ---
            # GAUSSIAN BLUR
            frame = cv2.GaussianBlur(frame, (5, 5), 0)
            
            height, width, _ = frame.shape
            center_x = width // 2  # Genişliğin tam yarısı
            display_frame = frame.copy()

            # --- 1. ADIM: QR KONTROL MODU ---
            if self.state == "QR_MODU":
                error_x, qr_area, processed_frame = self.process_qr_position(frame)
                
                if error_x is not None:
                    # GÖLGE MOD: Şimdilik motora hata basmıyoruz, sadece terminale yazdırıyoruz
                    self.get_logger().info(f'Gölge Mod - QR Hata X: {error_x} | Alan: {qr_area}')
                    
                    # Eşik değerine ulaşıldıysa şerit moduna geç!
                    if qr_area > self.QR_AREA_THRESHOLD:
                        self.get_logger().info('--- HEDEFE ULAŞILDI! ŞERİT TAKİBİNE GEÇİLİYOR ---')
                        self.state = "SERIT_MODU"
                
                # QR modundayken ekranı göster ve şerit kodlarını çalıştırmadan çık
                cv2.imshow("Kamera Arayuzu", display_frame)
                cv2.waitKey(1)
                return

            # --- 2. ADIM: ŞERİT TAKİBİ MODU (SADECE HSV AKTİF, OTSU KALDIRILDI) ---
            elif self.state == "SERIT_MODU":
                # Otsu kodları tamamen temizlendi.

                # YÖNTEM: HSV + GÜRÜLTÜ FİLTRELEME
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                lower_color = np.array([0, 0, 0])
                upper_color = np.array([180, 255, 50])
                mask_hsv = cv2.inRange(hsv, lower_color, upper_color)

                kernel = np.ones((5,5), np.uint8)
                mask_hsv = cv2.erode(mask_hsv, kernel, iterations=1)
                mask_hsv = cv2.dilate(mask_hsv, kernel, iterations=1)

                contours, _ = cv2.findContours(mask_hsv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                
                if len(contours) > 0:
                    biggest_contour = max(contours, key=cv2.contourArea)
                    M_hsv = cv2.moments(biggest_contour)
                    
                    if M_hsv["m00"] > 0:
                        cx_hsv = int(M_hsv["m10"] / M_hsv["m00"])
                        cy_hsv = int(M_hsv["m01"] / M_hsv["m00"])
                        
                        # HSV merkezi ve sapma çizgisi (YEŞİL)
                        cv2.circle(display_frame, (cx_hsv, cy_hsv), 10, (0, 255, 0), -1)
                        cv2.line(display_frame, (center_x, cy_hsv), (cx_hsv, cy_hsv), (0, 255, 0), 2)
                        
                        error_hsv = float(cx_hsv - center_x)
                        msg_hsv = Float32()
                        msg_hsv.data = error_hsv
                        self.pub_hsv.publish(msg_hsv)

                # Aracın ve Kameranın tam merkez çizgisi (MAVİ)
                cv2.line(display_frame, (center_x, 0), (center_x, height), (255, 0, 0), 2)

                # Otsu penceresi kaldırıldı, sadece HSV maskesi ve ana kamera kaldi.
                cv2.imshow("HSV Maskesi", mask_hsv)
                cv2.imshow("Kamera Arayuzu", display_frame)
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
