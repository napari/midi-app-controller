# Controllers

## Schemas

Support for any model of a MIDI controller can be added by creating its schema, which is represented as a simple [YAML](https://yaml.org) file.

The YAML file should contain all fields from the Controller class. See [example](#example-of-a-valid-schema).

Built-in schemas are available in [config_files/controllers](https://github.com/midi-app-controller/midi-app-controller/tree/main/config_files/controllers) on GitHub.

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
default_channel: 1
preferred_midi_in: "Some midi input port"
preferred_midi_out: "Some midi output port"
buttons:
  - id: 1
    name: "Button 1"
  - id: 2
    name: "Button 2"
knobs:
  - id: 1
    name: "Knob 1"
```

## Finding ids of knobs and buttons

Install `python-rtmidi` using:

```sh
python -m pip install python-rtmidi
```

and then run the following script:

```python
import rtmidi

def get_type(command):
    if command in (0x80, 0x90):
        return "Button"
    elif command == 0xB0:
        return "Knob"
    else:
        return "Unknown"

def midi_input_callback(event, data):
    message, _ = event
    command = message[0] & 0xF0
    print(get_type(command), "id:", message[1])

def select_midi_port(available_ports):
    print("Available MIDI input ports:")
    for i, port_name in enumerate(available_ports):
        print(f"{i}. {port_name}")
    return int(input("Select number of MIDI input port: "))

def main():
    midi_in = rtmidi.MidiIn()
    port_index = select_midi_port(midi_in.get_ports())
    midi_in.open_port(port_index)
    print("Listening...")
    print("Interact with elements of the MIDI controller to show their ids here.")
    midi_in.set_callback(midi_input_callback)
    input("Press Enter to quit.\n")
    midi_in.close_port()

if __name__ == "__main__":
    main()
```
