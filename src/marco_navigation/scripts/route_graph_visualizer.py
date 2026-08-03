#!/usr/bin/env python3
import json
import math
import rclpy
from geometry_msgs.msg import Point
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile
from visualization_msgs.msg import Marker, MarkerArray


class Visualizer(Node):
    def __init__(self):
        super().__init__('route_graph_visualizer')
        self.declare_parameter('graph', '')
        with open(self.get_parameter('graph').value, encoding='utf-8') as stream: self.graph = json.load(stream)
        qos = QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        self.pub = self.create_publisher(MarkerArray, '/route_graph/markers', qos)
        self.timer = self.create_timer(1.0, self.publish)

    def marker(self, ident, kind, scale, color):
        m = Marker(); m.header.frame_id = 'map'; m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'route_graph'; m.id = ident; m.type = kind; m.action = Marker.ADD
        m.scale.x, m.scale.y, m.scale.z = scale
        m.color.r, m.color.g, m.color.b, m.color.a = color
        m.pose.orientation.w = 1.0
        return m

    def publish(self):
        out = MarkerArray()
        for f in self.graph['features']:
            p, g = f['properties'], f['geometry']; ident = p['id']
            if g['type'] == 'Point':
                x, y = g['coordinates'][:2]
                dot = self.marker(ident, Marker.SPHERE, (.16,.16,.16), (0.2,0.8,1.0,1.0))
                dot.pose.position.x, dot.pose.position.y = x, y; out.markers.append(dot)
                label = self.marker(1000+ident, Marker.TEXT_VIEW_FACING, (0.,0.,.18), (1.,1.,1.,1.))
                label.pose.position.x, label.pose.position.y, label.pose.position.z = x, y, .25
                label.text = '%d %s' % (ident, p.get('metadata', {}).get('name', '')); out.markers.append(label)
            else:
                meta = p['metadata']; cls = meta.get('class')
                color = {'fast':(0.,1.,0.,1.), 'slow':(1.,.65,0.,1.), 'reverse':(.7,0.,1.,1.)}.get(cls, (0.2,.6,1.,1.))
                if meta.get('disableable'): color = (1.,0.,0.,1.)
                line = self.marker(2000+ident, Marker.LINE_STRIP, (.055,0.,0.), color)
                coords = [q for segment in g['coordinates'] for q in segment]
                line.points = [Point(x=float(q[0]), y=float(q[1]), z=.05) for q in coords]; out.markers.append(line)
                for i, (a,b) in enumerate(zip(coords, coords[1:])):
                    arrow = self.marker(3000+ident*10+i, Marker.ARROW, (.16,.28,.22), color)
                    arrow.pose.position.x=(a[0]+b[0])/2; arrow.pose.position.y=(a[1]+b[1])/2; arrow.pose.position.z=.07
                    arrow.pose.orientation.z=math.sin(math.atan2(b[1]-a[1],b[0]-a[0])/2)
                    arrow.pose.orientation.w=math.cos(math.atan2(b[1]-a[1],b[0]-a[0])/2); out.markers.append(arrow)
        self.pub.publish(out)


def main():
    rclpy.init(); node=Visualizer()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.shutdown()


if __name__ == '__main__': main()
