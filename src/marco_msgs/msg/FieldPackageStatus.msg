uint8 STATE_DRAFT=0
uint8 STATE_VALID=1
uint8 STATE_ACTIVE=2
uint8 STATE_ARCHIVED=3
uint8 STATE_ERROR=4

std_msgs/Header header
uint8 state
string field_name
string package_hash
uint32 node_count
uint32 edge_count
string[] errors
string[] warnings
string message
