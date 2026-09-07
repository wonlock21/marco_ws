#ifndef MARCO_NAVIGATION__OBSTACLE_AWARE_PROGRESS_CHECKER_HPP_
#define MARCO_NAVIGATION__OBSTACLE_AWARE_PROGRESS_CHECKER_HPP_

#include <atomic>
#include <memory>
#include <string>

#include "geometry_msgs/msg/pose2_d.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "nav2_core/progress_checker.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"
#include "std_msgs/msg/bool.hpp"

namespace marco_navigation
{

class ObstacleAwareProgressChecker : public nav2_core::ProgressChecker
{
public:
  void initialize(
    const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
    const std::string & plugin_name) override;

  bool check(geometry_msgs::msg::PoseStamped & current_pose) override;
  void reset() override;

private:
  void resetBaseline(
    const geometry_msgs::msg::PoseStamped & pose,
    const rclcpp::Time & stamp);

  rclcpp::Clock::SharedPtr clock_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr obstacle_sub_;
  std::atomic_bool obstacle_active_{false};
  double movement_radius_{0.15};
  rclcpp::Duration movement_time_allowance_{0, 0};
  geometry_msgs::msg::Pose2D baseline_pose_;
  rclcpp::Time baseline_time_{0, 0, RCL_ROS_TIME};
  bool baseline_set_{false};
};

}  // namespace marco_navigation

#endif  // MARCO_NAVIGATION__OBSTACLE_AWARE_PROGRESS_CHECKER_HPP_
