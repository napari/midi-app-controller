# Binds

All created binds and settings for a specific app and controller are stored as `YAML` files. They are usually edited from within the graphical user interface that disallows creating illegal configurations.

All ids of the elements should match the ones specified in the controller's schema.

Built-in schemas are available in [config_files/binds](https://github.com/midi-app-controller/midi-app-controller/tree/main/config_files/binds) on GitHub.

::: midi_app_controller.models.binds.Binds
    options:
      show_root_heading: true
      show_bases: false
      members: [""]

::: midi_app_controller.models.binds.ButtonBind
    options:
      show_root_heading: true
      show_bases: false
      members: [""]

::: midi_app_controller.models.binds.KnobBind
    options:
      show_root_heading: true
      show_bases: false
      members: [""]

## Example

```yaml
name: "MyBinds"
app_name: "MyApp"
controller_name: "MyController"
description: "Optional description"
button_binds:
  - button_id: 1
    action_id: "action_1"
  - button_id: 2
    action_id: "action_2"
knob_binds:
  - knob_id: 3
    action_id_increase: "action_3"
    action_id_decrease: "action_4"
```
