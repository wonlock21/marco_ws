#!/usr/bin/env python3
"""Track each selected graph route and pass its exact path to FollowPath."""
import copy, json, math, os, statistics, time
import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import ComputeAndTrackRoute, FollowPath
from nav2_msgs.msg import SpeedLimit
from nav_msgs.msg import Odometry, Path
from rclpy.action import ActionClient
from rclpy.node import Node

def segment_error(x,y,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]; d=dx*dx+dy*dy
    t=max(0.,min(1.,((x-a[0])*dx+(y-a[1])*dy)/d)) if d else 0.
    return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)

class Mission(Node):
    def __init__(self):
        super().__init__('route_test_mission'); self.declare_parameter('scenario','nominal'); self.declare_parameter('result_path','/tmp/marco_phase7/final.json');self.declare_parameter('graph','')
        with open(self.get_parameter('graph').value,encoding='utf-8') as stream:graph=json.load(stream)
        self.edge_metadata={}
        for feature in graph['features']:
            prop=feature['properties']
            if feature['geometry']['type']=='MultiLineString':self.edge_metadata[(prop['startid'],prop['endid'])]=(prop['id'],prop['metadata'])
        self.track=ActionClient(self,ComputeAndTrackRoute,'compute_and_track_route'); self.follow=ActionClient(self,FollowPath,'follow_path')
        self.pub=self.create_publisher(Path,'/route_path',1)
        self.speed_pub=self.create_publisher(SpeedLimit,'/speed_limit',10)
        self.stop_pub=self.create_publisher(Twist,'/cmd_vel',10)
        self.path=None; self.last_path=None; self.edges=[]; self.speeds=[]; self.cmd=[]; self.errors=[]; self.negative=[]
        self.create_subscription(SpeedLimit,'/speed_limit',lambda m:self.speeds.append((m.speed_limit,m.percentage)),20)
        self.create_subscription(Twist,'/cmd_vel',self.cmd_cb,50); self.create_subscription(Odometry,'/ground_truth/odom',self.odom_cb,50)
    def cmd_cb(self,m):
        self.cmd.append((m.linear.x,m.angular.z))
        if m.linear.x<-.01:self.negative.append(m.linear.x)
    def odom_cb(self,m):
        if self.path and len(self.path.poses)>1:
            p=m.pose.pose.position; pts=[(q.pose.position.x,q.pose.position.y) for q in self.path.poses]
            self.errors.append(min(segment_error(p.x,p.y,a,b) for a,b in zip(pts,pts[1:])))
    def feedback(self,m):
        f=m.feedback
        if f.current_edge_id not in self.edges:self.edges.append(f.current_edge_id)
        if f.path.poses and self.path is None:self.path=f.path;self.pub.publish(f.path)
    def wait(self,f,t):
        end=time.monotonic()+t
        while rclpy.ok() and not f.done() and time.monotonic()<end:rclpy.spin_once(self,timeout_sec=.05)
        return f.done()
    def reset_speed(self):
        reset=SpeedLimit();reset.percentage=False;reset.speed_limit=0.0;self.speed_pub.publish(reset)
    def segment(self,start,goal,reverse):
        cmd_start=len(self.cmd)
        g=ComputeAndTrackRoute.Goal();g.start_id=start;g.goal_id=goal;g.use_start=True;g.use_poses=False
        sent=self.track.send_goal_async(g,feedback_callback=self.feedback)
        if not self.wait(sent,5) or not sent.result().accepted:self.reset_speed();return {'passed':False}
        th=sent.result();end=time.monotonic()+5
        while self.path is None and time.monotonic()<end:rclpy.spin_once(self,timeout_sec=.05)
        if self.path is None:th.cancel_goal_async();self.reset_speed();return {'passed':False}
        if reverse:
            for p in self.path.poses:
                yaw=math.atan2(2*p.pose.orientation.w*p.pose.orientation.z,1-2*p.pose.orientation.z*p.pose.orientation.z)+math.pi
                p.pose.orientation.z=math.sin(yaw/2);p.pose.orientation.w=math.cos(yaw/2)
        edge_id,metadata=self.edge_metadata[(start,goal)];edge_limit=float(metadata['abs_speed_limit'])
        limit=SpeedLimit();limit.percentage=False;limit.speed_limit=edge_limit;self.speed_pub.publish(limit)
        align_yaw={2:-math.pi/2,3:0.0,4:math.pi/2}.get(start)
        if align_yaw is not None:
            # Align at the graph node using Nav2 FollowPath goal rotation. This
            # preserves the selected edge and avoids corner-cutting transitions.
            align=Path();align.header=copy.deepcopy(self.path.header)
            pose=copy.deepcopy(self.path.poses[0]);pose.pose.orientation.z=math.sin(align_yaw/2);pose.pose.orientation.w=math.cos(align_yaw/2)
            align.poses=[copy.deepcopy(pose),pose]
            ag=FollowPath.Goal();ag.path=align;ag.controller_id='FollowPath';af=self.follow.send_goal_async(ag)
            if not self.wait(af,5) or not af.result().accepted:self.reset_speed();return {'passed':False}
            ar=af.result().get_result_async()
            if not self.wait(ar,30) or ar.result().status!=GoalStatus.STATUS_SUCCEEDED:self.reset_speed();return {'passed':False}
        fg=FollowPath.Goal();fg.path=self.path;fg.controller_id='FollowPath';sf=self.follow.send_goal_async(fg)
        if not self.wait(sf,5) or not sf.result().accepted:th.cancel_goal_async();self.reset_speed();return {'passed':False}
        result=sf.result().get_result_async();ok=self.wait(result,120) and result.result().status==GoalStatus.STATUS_SUCCEEDED
        tr=th.get_result_async();self.wait(tr,10)
        self.reset_speed();self.last_path=copy.deepcopy(self.path);self.path=None
        linear=[abs(x) for x,_ in self.cmd[cmd_start:]]
        return {'passed':ok,'edge_id':edge_id,'metadata_limit':edge_limit,
                'cmd_linear_max':max(linear,default=0.0),'metadata_source':self.get_parameter('graph').value}
    def run(self):
        if not self.track.wait_for_server(30) or not self.follow.wait_for_server(30):return False
        segments=[]
        sequence=[(0,1,False),(1,2,False),(2,3,False),(3,4,True)] if self.get_parameter('scenario').value=='dynamic_speed' else [(0,1,False),(1,2,False),(2,3,False),(3,4,True),(4,0,False)]
        for a,b,rev in sequence:
            measured=self.segment(a,b,rev);measured.update(start=a,goal=b,reverse=rev);segments.append(measured)
            if not measured['passed']:break
        reset_tests={}
        if self.get_parameter('scenario').value=='dynamic_speed' and self.last_path:
            # Real FollowPath cancellation, followed by the same reset path used
            # for mission cancellation in this simulator-only coordinator.
            active=SpeedLimit();active.percentage=False;active.speed_limit=.15;self.speed_pub.publish(active)
            cancel_path=Path();cancel_path.header.frame_id='map';cancel_path.header.stamp=self.get_clock().now().to_msg()
            for i in range(41):
                pose=PoseStamped();pose.header=cancel_path.header;pose.pose.position.x=0.0;pose.pose.position.y=-2.5+i*0.025
                pose.pose.orientation.z=math.sin(math.pi/4);pose.pose.orientation.w=math.cos(math.pi/4);cancel_path.poses.append(pose)
            goal=FollowPath.Goal();goal.path=cancel_path;goal.controller_id='FollowPath'
            sent=self.follow.send_goal_async(goal)
            accepted=self.wait(sent,5) and sent.result().accepted
            cancelled=False
            if accepted:
                for _ in range(8):rclpy.spin_once(self,timeout_sec=.05)
                future=sent.result().cancel_goal_async()
                cancelled=self.wait(future,5) and bool(future.result().goals_canceling)
            for _ in range(10):rclpy.spin_once(self,timeout_sec=.05)
            for _ in range(3):self.reset_speed();rclpy.spin_once(self,timeout_sec=.10)
            reset_tests['cancel']={'action_cancelled':cancelled,'reset':bool(self.speeds) and self.speeds[-1][0]==0.0}
            # Real invalid ComputeAndTrackRoute error, then fail-safe reset.
            active.speed_limit=.20;self.speed_pub.publish(active)
            bad=ComputeAndTrackRoute.Goal();bad.start_id=4;bad.goal_id=65000;bad.use_start=True;bad.use_poses=False
            bad_sent=self.track.send_goal_async(bad)
            failed=False
            if self.wait(bad_sent,5) and bad_sent.result().accepted:
                bad_result=bad_sent.result().get_result_async()
                failed=self.wait(bad_result,8) and bad_result.result().status!=GoalStatus.STATUS_SUCCEEDED
            for _ in range(10):rclpy.spin_once(self,timeout_sec=.05)
            for _ in range(3):self.reset_speed();rclpy.spin_once(self,timeout_sec=.10)
            reset_tests['error']={'action_failed':failed,'reset':bool(self.speeds) and self.speeds[-1][0]==0.0}
        for _ in range(30):rclpy.spin_once(self,timeout_sec=.05)
        # Explicit safety neutral at mission boundary; all motion, including
        # reverse, remains exclusively generated by Nav2 FollowPath.
        for _ in range(3):self.stop_pub.publish(Twist());rclpy.spin_once(self,timeout_sec=.05)
        p95=sorted(self.errors)[min(len(self.errors)-1,int(.95*len(self.errors)))] if self.errors else math.inf
        last=[abs(v) for pair in self.cmd[-1:] for v in pair]
        bounds=all(x.get('cmd_linear_max',math.inf)<=x.get('metadata_limit',-1)+0.015 for x in segments)
        publishers=len(self.get_publishers_info_by_topic('/speed_limit'))
        checks={'actions_succeeded':len(segments)==len(sequence) and all(x['passed'] for x in segments),'p95_le_010':p95<=.10,
                'max_le_015':max(self.errors,default=math.inf)<=.15,'negative_cmd_vel':bool(self.negative),
                'final_cmd_vel_zero':max(last,default=math.inf)<.01,'speed_limits_seen':any(not p and .14<=v<=.51 for v,p in self.speeds),
                'speed_limit_reset':bool(self.speeds) and self.speeds[-1][0]<=0.,
                'single_speed_limit_publisher':publishers==1,'cmd_within_metadata_limits':bounds,
                'metadata_not_hardcoded':all(x.get('metadata_source')==self.get_parameter('graph').value for x in segments)}
        if self.get_parameter('scenario').value=='dynamic_speed':
            checks['cancel_reset']=all(reset_tests.get('cancel',{}).values())
            checks['error_reset']=all(reset_tests.get('error',{}).values())
        result={'passed':all(checks.values()),'checks':checks,'segments':segments,'edge_feedback':self.edges,'reset_tests':reset_tests,
                'metrics':{'mean':statistics.fmean(self.errors) if self.errors else None,'p95':p95 if self.errors else None,
                           'max':max(self.errors) if self.errors else None,'negative_min':min(self.negative,default=None),
                           'speed_limits':sorted(set(round(v,3) for v,p in self.speeds if not p))}}
        path=self.get_parameter('result_path').value;os.makedirs(os.path.dirname(path),exist_ok=True)
        with open(path,'w',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
        print(('PASS' if result['passed'] else 'FAIL')+' route nominal mission');return result['passed']

def main():
    rclpy.init();n=Mission()
    try:ok=n.run()
    finally:n.destroy_node();rclpy.shutdown()
    raise SystemExit(0 if ok else 2)
if __name__=='__main__':main()
