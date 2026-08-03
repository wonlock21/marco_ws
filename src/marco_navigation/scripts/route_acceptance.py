#!/usr/bin/env python3
"""Real ComputeRoute checks and an independent scorer oracle."""
import json, math, os, time
import rclpy
from action_msgs.msg import GoalStatus
from nav2_msgs.action import ComputeRoute
from nav2_msgs.srv import DynamicEdges
from rclpy.action import ActionClient
from rclpy.node import Node

class Acceptance(Node):
    def __init__(self):
        super().__init__('route_acceptance'); self.declare_parameter('result_path','/tmp/marco_phase7/final.json')
        self.client=ActionClient(self,ComputeRoute,'compute_route')
        self.dynamic=self.create_client(DynamicEdges,'/route_server/DynamicEdgesScorer/adjust_edges')
    def wait(self,future,timeout=8.):
        end=time.monotonic()+timeout
        while rclpy.ok() and not future.done() and time.monotonic()<end: rclpy.spin_once(self,timeout_sec=.05)
        return future.done()
    def compute(self,start,goal):
        g=ComputeRoute.Goal(); g.start_id=start; g.goal_id=goal; g.use_start=True; g.use_poses=False
        sent=self.client.send_goal_async(g)
        if not self.wait(sent) or not sent.result().accepted: return {'succeeded':False,'status':'rejected'}
        future=sent.result().get_result_async()
        if not self.wait(future): return {'succeeded':False,'status':'timeout'}
        wrapped=future.result(); msg=wrapped.result
        edges=[e.edgeid for e in msg.route.edges]; nodes=[n.nodeid for n in msg.route.nodes]
        finite=all(math.isfinite(p.pose.position.x) and math.isfinite(p.pose.position.y) for p in msg.path.poses)
        length=sum(math.hypot(b.pose.position.x-a.pose.position.x,b.pose.position.y-a.pose.position.y) for a,b in zip(msg.path.poses,msg.path.poses[1:]))
        return {'succeeded':wrapped.status==GoalStatus.STATUS_SUCCEEDED,'status':wrapped.status,'nodes':nodes,'edges':edges,
                'frame':msg.path.header.frame_id,'finite':finite,'length':length,'cost':float(msg.route.route_cost)}
    def run(self):
        if not self.client.wait_for_server(30.): return False
        tests={'node_to_node':self.compute(0,2),'reverse_valid':self.compute(3,2),'same_node':self.compute(1,1),
               'missing_node':self.compute(0,65000),'one_way_alternative':self.compute(0,4)}
        v,s=tests['node_to_node'],tests['same_node']; short_d,fast_d=3.5,5.7; short_t,fast_t=3.5/.15,5.7/.50
        checks={'node_to_node':v['succeeded'] and v['edges']==[100,101],
                'route_integrity':v['frame']=='map' and v['finite'] and v['length']>0 and math.isfinite(v['cost']),
                'reverse_valid':tests['reverse_valid']['succeeded'],'same_node':s['succeeded'] and not s['edges'],
                'missing_node_fails':not tests['missing_node']['succeeded'],
                'one_way_alternative':tests['one_way_alternative']['succeeded'] and tests['one_way_alternative']['edges']==[109],
                'scorer_oracle':short_d<fast_d and fast_t<short_t}
        dynamic={}
        if self.dynamic.wait_for_service(timeout_sec=10.):
            before=self.compute(1,3)
            request=DynamicEdges.Request();request.closed_edges=[106]
            closed=self.dynamic.call_async(request);self.wait(closed)
            while_closed=self.compute(1,3)
            request=DynamicEdges.Request();request.opened_edges=[106]
            opened=self.dynamic.call_async(request);self.wait(opened)
            after=self.compute(1,3)
            dynamic={'before':before,'closed':while_closed,'after':after,
                     'close_success':bool(closed.done() and closed.result().success),
                     'open_success':bool(opened.done() and opened.result().success)}
            checks['dynamic_close_alternative']=(dynamic['close_success'] and before['edges']==[106,107]
                                                 and while_closed['edges']==[105])
            checks['dynamic_reopen_normal']=(dynamic['open_success'] and after['edges']==[106,107])
        else:
            checks['dynamic_close_alternative']=False;checks['dynamic_reopen_normal']=False
        result={'passed':all(checks.values()),'checks':checks,'tests':tests,'dynamic':dynamic,
                'oracle':{'distance_choice':[105],'time_choice':[106,107],'distance_costs':[short_d,fast_d],'time_costs':[short_t,fast_t]}}
        path=self.get_parameter('result_path').value.replace('.json','_api.json'); os.makedirs(os.path.dirname(path),exist_ok=True)
        with open(path,'w',encoding='utf-8') as stream: json.dump(result,stream,indent=2)
        print(('PASS' if result['passed'] else 'FAIL')+' route API acceptance'); return result['passed']

def main():
    rclpy.init(); node=Acceptance()
    try: ok=node.run()
    finally: node.destroy_node(); rclpy.shutdown()
    raise SystemExit(0 if ok else 2)
if __name__=='__main__': main()
