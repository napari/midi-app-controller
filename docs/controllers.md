# Controllers

## Schemas

Support for any model of a MIDI controller can be added by creating its schema, which is represented as a simple [YAML](https://yaml.org) file.

The YAML file should contain all fields from the Controller class. See [example](#example-of-a-valid-schema).

Built-in schemas are available in [config_files/controllers](https://github.com/midi-app-controller/midi-app-controller/tree/main/config_files/controllers) at GitHub.

::: midi_app_controller.models.controller.Controller
    options:
      show_root_heading: true
      show_bases: false
      members: [""]

::: midi_app_controller.models.controller.ControllerElement
    options:
      show_root_heading: true
      show_bases: false
      members: [""]
      
## Example of a valid schema

```yaml
name: "MyController"
button_value_off: 0
button_value_on: 127
knob_value_min: 0
knob_value_max: 127
buttons:
  - id: 1
    name: "Button 1"
  - id: 2
    name: "Button 2"
knobs:
  - id: 1
    name: "Knob 1"
```
