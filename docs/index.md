
# Getting started

MIDI App Controller is a package designed to integrate MIDI controllers with Python Qt apps using app-model.

## Installation

TODO: Installation instructions after we publish our package

### Development version

```
git clone https://github.com/midi-app-controller/midi-app-controller/
cd midi-app-controller
python3 -m pip install -e .
napari
```

## Setup

TODO: Pictures

If your MIDI controller is supported out of the box, you can simply select the appropriate model. If not, you will need to tell MIDI App Controller how to interact with this model of controller by creating a [controller schema](controllers.md).

You can configure bindings by choosing which physical buttons and knobs on your controller correspond to which commands in the application. Think of it like configuring keyboard shortcuts.

All configurations are simple YAML files which you can copy, share, or edit manually. You can click "Reveal in explorer" to see the exact location of the currently chosen config file. You shouldn't edit built-in presets stored in the package directory; when you edit a built-in preset in the graphical user interface, a copy will automatically be created.

## Start

After a controller and bindings are selected, you can click "Start handling". This will start a thread that listens to all input from the controller and invokes appropriate commands.

You are now ready to enjoy MIDI App Controller.

