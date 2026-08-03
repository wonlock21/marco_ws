#!/usr/bin/env python3
"""One-shot Phase 7 scorer and active-edge obstacle evidence."""
import json, math, os, statistics, time

import rclpy
from action_msgs.msg import GoalStatus, GoalStatusArray
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import ComputeRoute, NavigateToPose
from nav2_msgs.msg import SpeedLimit
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import DeleteEntity, SpawnEntity

FOOTPRINT = [(0.50, 0.35), (0.50, -0.35), (-1.18, -0.35), (-1.18, 0.35)]
SELECTED = [((1., 0.), (2., -2.5))]
OTHER = [((1., 0.), (1., -3.6)), ((1., -3.6), (2., -3.6)), ((2., -3.6), (2., -2.5))]
OBSTACLE = (1.50, -1.25, .60, .25)  # center x/y and half extents

def segdist(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]; d = dx*dx+dy*dy
    t = max(0., min(1., ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/d)) if d else 0.
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)

def percentile(v, q):
    if not v: return None
    s=sorted(v); x=(len(s)-1)*q; lo=int(x); hi=min(lo+1,len(s)-1)
    return s[lo]+(s[hi]-s[lo])*(x-lo)

def yaw(q): return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))

class Final(Node):
    def __init__(self):
        super().__init__('phase7_final_acceptance')
        self.declare_parameter('result_dir','/tmp/marco_phase7')
        self.declare_parameter('route_bt','')
        self.distance=ActionClient(self,ComputeRoute,'/distance/compute_route')
        self.fast=ActionClient(self,ComputeRoute,'/time/compute_route')
        self.main=ActionClient(self,ComputeRoute,'/compute_route')
        self.nav=ActionClient(self,NavigateToPose,'/navigate_to_pose')
        self.spawn=self.create_client(SpawnEntity,'/world/marco_test/create')
        self.remove=self.create_client(DeleteEntity,'/world/marco_test/remove')
        self.speed_pub=self.create_publisher(SpeedLimit,'/speed_limit',10)
        self.stop_pub=self.create_publisher(Twist,'/cmd_vel',10)
        self.truth=None; self.map=None; self.cmd=Twist(); self.samples=[]; self.clear=[]
        self.collisions=0; self.wrong=0; self.shortcuts=0; self.wait=0; self.spin=0; self.backup=0
        self.speed=[]; self.route_during=[]; self.obstacle_active=False
        transient=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)
        self.create_subscription(OccupancyGrid,'/map',lambda m:setattr(self,'map',m),transient)
        self.create_subscription(Odometry,'/ground_truth/odom',self.truth_cb,50)
        self.create_subscription(Twist,'/cmd_vel',lambda m:setattr(self,'cmd',m),50)
        self.create_subscription(SpeedLimit,'/speed_limit',lambda m:self.speed.append((m.speed_limit,m.percentage)),20)
        self.create_subscription(GoalStatusArray,'/wait/_action/status',lambda m:self.count(m,'wait'),10)
        self.create_subscription(GoalStatusArray,'/spin/_action/status',lambda m:self.count(m,'spin'),10)
        self.create_subscription(GoalStatusArray,'/backup/_action/status',lambda m:self.count(m,'backup'),10)
    def count(self,msg,name):
        if any(x.status in (GoalStatus.STATUS_ACCEPTED,GoalStatus.STATUS_EXECUTING) for x in msg.status_list):
            setattr(self,name,getattr(self,name)+1)
    def spin_until(self,pred,timeout):
        end=time.monotonic()+timeout
        while rclpy.ok() and time.monotonic()<end:
            rclpy.spin_once(self,timeout_sec=.05)
            if pred(): return True
        return False
    def compute(self,client,start,goal):
        g=ComputeRoute.Goal();g.start_id=start;g.goal_id=goal;g.use_start=True;g.use_poses=False
        sent=client.send_goal_async(g)
        if not self.spin_until(sent.done,5) or not sent.result().accepted:return {'status':'REJECTED','edges':[]}
        done=sent.result().get_result_async()
        if not self.spin_until(done.done,8):return {'status':'TIMEOUT','edges':[]}
        w=done.result();return {'status':w.status,'edges':[e.edgeid for e in w.result.route.edges],
                                'cost':float(w.result.route.route_cost),'poses':len(w.result.path.poses)}
    def truth_cb(self,msg):
        self.truth=msg
        if not self.map:return
        p=msg.pose.pose; point=(p.position.x,p.position.y); angle=yaw(p.orientation);c,s=math.cos(angle),math.sin(angle)
        poly=[(point[0]+c*x-s*y,point[1]+s*x+c*y) for x,y in FOOTPRINT]
        cte=min(segdist(point,a,b) for a,b in SELECTED); self.samples.append(cte)
        if min(segdist(point,a,b) for a,b in OTHER)+.02 < cte:self.wrong+=1
        if cte>.10:self.shortcuts+=1
        info=self.map.info; ox,oy=info.origin.position.x,info.origin.position.y
        for gy in range(math.floor((min(y for _,y in poly)-oy)/info.resolution)-1,math.ceil((max(y for _,y in poly)-oy)/info.resolution)+2):
            for gx in range(math.floor((min(x for x,_ in poly)-ox)/info.resolution)-1,math.ceil((max(x for x,_ in poly)-ox)/info.resolution)+2):
                if not (0<=gx<info.width and 0<=gy<info.height):continue
                if self.map.data[gy*info.width+gx]>=65:
                    q=(ox+(gx+.5)*info.resolution,oy+(gy+.5)*info.resolution)
                    self.clear.append(min(segdist(q,poly[i],poly[(i+1)%4]) for i in range(4)))
        if self.obstacle_active:
            # Separating-axis test and edge clearance for the temporary box.
            cx,cy,hx,hy=OBSTACLE
            rect=[(cx-hx,cy-hy),(cx+hx,cy-hy),(cx+hx,cy+hy),(cx-hx,cy+hy)]
            axes=[]
            for shape in (poly,rect):
                for i in range(len(shape)):
                    dx=shape[(i+1)%len(shape)][0]-shape[i][0];dy=shape[(i+1)%len(shape)][1]-shape[i][1]
                    axes.append((-dy,dx))
            overlap=all(not (max(x*a+y*b for x,y in poly)<min(x*a+y*b for x,y in rect) or
                                max(x*a+y*b for x,y in rect)<min(x*a+y*b for x,y in poly)) for a,b in axes)
            if overlap:self.collisions+=1;self.clear.append(0.)
            else:self.clear.append(min(segdist(q,poly[i],poly[(i+1)%4]) for q in rect for i in range(4)))
    def set_speed(self,value):
        m=SpeedLimit();m.percentage=False;m.speed_limit=value;self.speed_pub.publish(m)
    def run(self):
        ready=all(c.wait_for_server(35) for c in (self.distance,self.fast,self.main,self.nav))
        scorer={'ready':ready}
        if ready:
            scorer['distance']=self.compute(self.distance,1,3)
            scorer['time']=self.compute(self.fast,1,3)
        scorer['passed']=ready and scorer['distance']['edges']==[105] and scorer['time']['edges']==[106,107]
        with open(os.path.join(self.get_parameter('result_dir').value,'scorer_live.json'),'w') as f:json.dump(scorer,f,indent=2)
        # Reach node 1 without an obstacle; the measured scenario itself is the
        # single short edge 105 and starts only after these samples are cleared.
        preposition=False
        if ready:
            pg=NavigateToPose.Goal();pg.pose.header.frame_id='map';pg.pose.pose.position.x=1.;pg.pose.pose.orientation.w=1.
            pg.behavior_tree=self.get_parameter('route_bt').value
            ps=self.nav.send_goal_async(pg)
            if self.spin_until(ps.done,8) and ps.result().accepted:
                pr=ps.result().get_result_async();preposition=self.spin_until(pr.done,45) and pr.result().status==GoalStatus.STATUS_SUCCEEDED
        self.samples=[];self.clear=[];self.collisions=0;self.wrong=0;self.shortcuts=0
        before=self.compute(self.main,1,3) if ready else {'edges':[]}
        service=self.spawn.wait_for_service(15) and self.remove.wait_for_service(3)
        sdf=("<sdf version='1.7'><model name='phase7_edge_obstacle'><static>true</static><link name='link'>"
             "<collision name='collision'><geometry><box><size>1.20 0.50 1.00</size></box></geometry></collision>"
             "<visual name='visual'><geometry><box><size>1.20 0.50 1.00</size></box></geometry>"
             "<material><ambient>1 0.1 0.1 1</ambient><diffuse>1 0.1 0.1 1</diffuse></material></visual></link></model></sdf>")
        spawned=False;removed=False;action_status=None;stopped=False
        if service:
            req=SpawnEntity.Request();req.entity_factory.name='phase7_edge_obstacle';req.entity_factory.sdf=sdf
            req.entity_factory.pose.position.x=OBSTACLE[0];req.entity_factory.pose.position.y=OBSTACLE[1];req.entity_factory.pose.position.z=.5;req.entity_factory.pose.orientation.w=1.
            f=self.spawn.call_async(req);spawned=self.spin_until(f.done,10) and f.result().success;self.obstacle_active=spawned
        if spawned:
            self.set_speed(.15)
            goal=NavigateToPose.Goal();goal.pose.header.frame_id='map';goal.pose.pose.position.x=2.;goal.pose.pose.position.y=-2.5;goal.pose.pose.orientation.w=1.
            goal.behavior_tree=self.get_parameter('route_bt').value
            sent=self.nav.send_goal_async(goal);accepted=self.spin_until(sent.done,8) and sent.result().accepted
            handle=sent.result() if accepted else None
            moving=self.spin_until(lambda:abs(self.cmd.linear.x)>.02,15) if handle else False
            stopped=self.spin_until(lambda:self.wait>0 and abs(self.cmd.linear.x)<.005 and abs(self.cmd.angular.z)<.005,35) if moving else False
            for _ in range(3):self.route_during.append(self.compute(self.main,1,3));self.spin_until(lambda:False,.3)
            held=self.spin_until(lambda:False,3.0) is False
            delete=DeleteEntity.Request();delete.entity.name='phase7_edge_obstacle';delete.entity.type=Entity.MODEL
            f=self.remove.call_async(delete);removed=self.spin_until(f.done,10) and f.result().success;self.obstacle_active=not removed
            result=handle.get_result_async() if handle else None
            if result and self.spin_until(result.done,100):action_status=result.result().status
        self.set_speed(0.);self.spin_until(lambda:False,.3)
        for _ in range(5):self.stop_pub.publish(Twist());rclpy.spin_once(self,timeout_sec=.05)
        final_zero=abs(self.cmd.linear.x)<.005 and abs(self.cmd.angular.z)<.005
        route_same=before.get('edges')==[105] and all(x.get('edges')==[105] for x in self.route_during)
        obstacle={'preposition_succeeded':preposition,'spawned':spawned,'removed':removed,'route_before':before,'route_during':self.route_during,
                  'same_route':route_same,'wait_samples':self.wait,'spin_samples':self.spin,'backup_samples':self.backup,
                  'stopped':stopped,'action_status':action_status,'succeeded':action_status==GoalStatus.STATUS_SUCCEEDED,
                  'final_cmd_vel_zero':final_zero,'speed_limit_reset':bool(self.speed) and self.speed[-1][0]==0.,
                  'dynamic_edges_used':False,'alternative_route_used':False}
        obstacle['metrics']={'footprint_collisions':self.collisions,'minimum_clearance_m':min(self.clear) if self.clear else None,
          'wrong_edge_samples':self.wrong,'graph_shortcut_samples':self.shortcuts,'cross_track_mean_m':statistics.fmean(self.samples) if self.samples else None,
          'cross_track_p95_m':percentile(self.samples,.95),'cross_track_max_m':max(self.samples) if self.samples else None,'samples':len(self.samples)}
        obstacle['passed']=(preposition and spawned and removed and route_same and self.wait>0 and self.spin==0 and self.backup==0 and stopped and obstacle['succeeded']
          and final_zero and obstacle['speed_limit_reset'] and self.collisions==0 and self.wrong==0 and self.shortcuts==0
          and bool(self.samples) and percentile(self.samples,.95)<=.10 and max(self.samples)<=.15)
        with open(os.path.join(self.get_parameter('result_dir').value,'obstacle_route.json'),'w') as f:json.dump(obstacle,f,indent=2)
        summary={'passed':scorer['passed'] and obstacle['passed'],'scorer':scorer,'obstacle':obstacle}
        with open(os.path.join(self.get_parameter('result_dir').value,'final.json'),'w') as f:json.dump(summary,f,indent=2)
        return summary['passed']

def main():
    rclpy.init();n=Final()
    try:ok=n.run()
    finally:n.destroy_node();rclpy.shutdown()
    raise SystemExit(0 if ok else 2)
if __name__=='__main__':main()
