# Binds

All created binds and settings for a specific app and controller are stored as `YAML` files.
Ids of the elements should match the ones specified in the controller's schema.

## All available fields
- `name`: The name of the binds set. Cannot be empty. Must be unique among all binds sets.
- `app_name`: For which app are the binds intended. Cannot be empty.
- `controller_name`: For which controller are the binds intended. Cannot be empty.
- `description`: Additional information that the user may provide. Is optional.
- `button_binds`: List of bound buttons. Each of them consists of:
  - `button_id`: The id of the button. Should be in the range `[0, 127]`.
  - `action_id`: The id of an action to be executed when the button is pressed.
- `knob_binds`: List of bound knobs. Each of them consists of:
  - `knob_id`: The id of the knob. Should be in the range `[0, 127]`.
  - `action_id_increase`: The id of an action to be executed when the knob's value increases.
  - `action_id_decrease`: The id of an action to be executed when the knob's value decreases.

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
