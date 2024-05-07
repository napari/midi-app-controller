# Controllers

## Schemas

Support for any model of a MIDI controller can be added by creating its schema, which is represented as a simple `YAML` file.

### All available fields

- `name`: The name of the controller. Cannot be empty. Must be unique among all schemas.
- `button_value_off`: The number sent by the controller when a button is in `off` state. Should be in the range `[0, 127]`.
- `button_value_on`: The number sent by the controller when a button is in `on` state. Should be in the range `[0, 127]`.
- `knob_value_min`: The minimum value sent by the controller when a knob is rotated. Should be in the range `[0, 127]`.
- `knob_value_max`: The maximum value sent by the controller when a knob is rotated. Should be in the range `[0, 127]`.
- `default_channel`: The channel on which all the messages to the controller will be sent. Keep in mind, that the actual number sent in
  the MIDI message is decreased by 1, so it fits in a single hex digit. Should be in the range `[1, 16]`.
- `buttons`: List of available buttons on the controller. Each of them consists of:
  - `id`: The ID of the button that the controller sends with every event. Should be in the range `[0, 127]`.
  - `name`: A user-defined name for the button that helps to differentiate elements. Cannot be empty. No two elements can have the same name.
- `knobs`: List of available knobs on the controller.  Each of them consists of:
  - `id`: The ID of the knob that the controller sends with every event. Should be in the range `[0, 127]`.
  - `name`: A user-defined name for the knob that helps to differentiate elements. Cannot be empty. No two elements can have the same name.

### Example of a valid schema
```yaml
name: "MyController"
button_value_off: 0
button_value_on: 127
knob_value_min: 0
knob_value_max: 127
default_channel: 1
buttons:
  - id: 1
    name: "Button 1"
  - id: 2
    name: "Button 2"
knobs:
  - id: 1
    name: "Knob 1"
```
