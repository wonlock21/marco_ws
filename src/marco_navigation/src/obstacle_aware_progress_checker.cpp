#include "marco_navigation/obstacle_aware_progress_checker.hpp"

#include <cmath>
#include <stdexcept>

#include "pluginlib/class_list_macros.hpp"

namespace marco_navigation
{

void ObstacleAwareProgressChecker::initialize(
  const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
  const std::string & plugin_name)
{
  const auto node = parent.lock();
  if (!node) {
    throw std::runtime_error("ObstacleAwareProgressChecker parent node expired");
  }

  const auto radius_parameter = plugin_name + ".required_movement_radius";
  const auto allowance_parameter = plugin_name + ".movement_time_allowance";
  const auto topic_parameter = plugin_name + ".obstacle_topic";
  if (!node->has_parameter(radius_parameter)) {
    node->declare_parameter(radius_parameter, 0.15);
  }
  if (!node->has_parameter(allowance_parameter)) {
    node->declare_parameter(allowance_parameter, 60.0);
  }
  if (!node->has_parameter(topic_parameter)) {
    node->declare_parameter(topic_parameter, "/safety/obstacle_detected");
  }

  movement_radius_ = node->get_parameter(radius_parameter).as_double();
  const double allowance = node->get_parameter(allowance_parameter).as_double();
  const std::string obstacle_topic = node->get_parameter(topic_parameter).as_string();
  if (!std::isfinite(movement_radius_) || movement_radius_ <= 0.0) {
    throw std::invalid_argument(radius_parameter + " must be finite and positive");
  }
  if (!std::isfinite(allowance) || allowance <= 0.0) {
    throw std::invalid_argument(allowance_parameter + " must be finite and positive");
  }
  if (obstacle_topic.empty()) {
    throw std::invalid_argument(topic_parameter + " cannot be empty");
  }

  clock_ = node->get_clock();
  movement_time_allowance_ = rclcpp::Duration::from_seconds(allowance);
  obstacle_sub_ = node->create_subscription<std_msgs::msg::Bool>(
    obstacle_topic,
    rclcpp::QoS(10),
    [this](const std_msgs::msg::Bool::SharedPtr message) {
      obstacle_active_.store(message->data);
    });

  RCLCPP_INFO(
    node->get_logger(),
    "%s: no-progress %.1f s, radius %.3f m; obstacle topic %s pauses timer",
    plugin_name.c_str(), allowance, movement_radius_, obstacle_topic.c_str());
}

bool ObstacleAwareProgressChecker::check(
  geometry_msgs::msg::PoseStamped & current_pose)
{
  const auto now = clock_->now();
  if (!baseline_set_ || obstacle_active_.load()) {
    // Refresh on every controller cycle while stopped by safety. Therefore
    // obstacle dwell time can never consume the real no-progress allowance.
    resetBaseline(current_pose, now);
    return true;
  }

  const double dx = current_pose.pose.position.x - baseline_pose_.x;
  const double dy = current_pose.pose.position.y - baseline_pose_.y;
  if (std::hypot(dx, dy) >= movement_radius_) {
    resetBaseline(current_pose, now);
    return true;
  }
  return now - baseline_time_ <= movement_time_allowance_;
}

void ObstacleAwareProgressChecker::reset()
{
  baseline_set_ = false;
}

void ObstacleAwareProgressChecker::resetBaseline(
  const geometry_msgs::msg::PoseStamped & pose,
  const rclcpp::Time & stamp)
{
  baseline_pose_.x = pose.pose.position.x;
  baseline_pose_.y = pose.pose.position.y;
  baseline_pose_.theta = 0.0;
  baseline_time_ = stamp;
  baseline_set_ = true;
}

}  // namespace marco_navigation

PLUGINLIB_EXPORT_CLASS(
  marco_navigation::ObstacleAwareProgressChecker,
  nav2_core::ProgressChecker)
