import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

class VirtualController(Node):
    def __init__(self):
        super().__init__('virtual_controller_node')
        
        self.subscription = self.create_subscription(
            Float32, '/lane_error_hsv', self.error_callback, 10)
            
        self.pub_left_pwm = self.create_publisher(Float32, '/pwm_left', 10)
        self.pub_right_pwm = self.create_publisher(Float32, '/pwm_right', 10)
            
        # (P ve D)
        self.base_speed = 100
        self.Kp = 0.10
        self.Kd = 0.05  
        
        # 2. Geçmiş veriler
        self.last_error = 0.0
        self.last_time = self.get_clock().now().nanoseconds / 1e9 
   
    def error_callback(self, msg):
        error = msg.data
        
        # dt
        current_time = self.get_clock().now().nanoseconds / 1e9
        dt = current_time - self.last_time
        
    
        if dt <= 0.0:
            dt = 0.001
            
        # 4. Türev 
        derivative = (error - self.last_error) / dt
        
        # 5. PD Kontrol 
        control_signal = (self.Kp * error) + (self.Kd * derivative)
        
        # 6. Geçmişi güncelle 
        self.last_error = error
        self.last_time = current_time
        
       
        left_pwm = max(0.0, min(150.0, self.base_speed + control_signal))
        right_pwm = max(0.0, min(150.0, self.base_speed - control_signal))
        
        # Kanallara ver
        msg_left, msg_right = Float32(), Float32()
        msg_left.data, msg_right.data = float(left_pwm), float(right_pwm)
        
        self.pub_left_pwm.publish(msg_left)
        self.pub_right_pwm.publish(msg_right)
        
       
        self.get_logger().info(
            f"Hata: {error:+.1f} | Eğim(D): {derivative:+.1f} | SOL: {left_pwm:.1f}/255 | SAĞ: {right_pwm:.1f}/255"
        )

def main(args=None):
    rclpy.init(args=args)
    controller = VirtualController()
    rclpy.spin(controller)
    controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
