# CleanScout TEB Dependency Lock

`C-4.1.3` vendors the ROS Noetic TEB build dependencies in this workspace so
the navigation baseline does not depend on unpinned system packages.

| Workspace path | Package/version | Upstream revision |
| --- | --- | --- |
| `teb_local_planner-noetic-devel` | `teb_local_planner 0.9.1` | `rst-tu-dortmund/teb_local_planner@8f429538601d7c4102aa345e8b5ba8dfae989c00` |
| `costmap_converter-master` | `costmap_converter 0.0.13` | `rst-tu-dortmund/costmap_converter@d1d57b6e6be35a0a9e802de8325d14c399cca9ed` |
| `move_base_flex` | MBF packages `0.4.0` | `naturerobots/move_base_flex@43063b9577ea11a122f65b6067ac9c76dfee92f0` |

The directories contain unmodified upstream source at the revisions above.
Project-specific TEB tuning remains under:

```text
clbrobot_project/clbrobot/param/navigation/
```
