std_msgs/Header header

uint8 STATE_IDLE=0
uint8 STATE_STARTING=1
uint8 STATE_NAVIGATING_A=2
uint8 STATE_LANE_A=3
uint8 STATE_TURNING_A=4
uint8 STATE_WAITING_LOAD=5
uint8 STATE_NAVIGATING_B=6
uint8 STATE_LANE_B=7
uint8 STATE_TURNING_B=8
uint8 STATE_COMPLETE=9
uint8 STATE_ERROR=10
uint8 STATE_CANCELED=11

uint8 state
string message
geometry_msgs/Pose2D point_a
geometry_msgs/Pose2D point_b
string active_target
int32 navigation_process_id
int32 lane_process_id
