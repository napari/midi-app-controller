
# Config files

Config files are YAML files with appropriate structure. See [controllers](controllers.md) and [binds](binds.md) for required fields. There shouldn't be a need to edit binds files because editing them is available from the user interface.

Built-in config files are stored alongside MIDI App Controller's source code, and can't be modified. When you try to edit a built-in config file in the user interface, a copy of the file will be created in the user config directory. If you manually create new files, they should also be put there.

For example, if you want to add support for a new type of hardware controller, you should create a YAML file in this folder:

| Platform | Path                                                                                 |
| -------- | ------------------------------------------------------------------------------------ |
| Windows  | C:\Users\&lt;user>\AppData\Local\MIDI App Controller\MIDI App Controller\controllers |
| macOS    | ~/Library/Preferences/MIDI App Controller/controllers                                |
| Linux    | ~/.config/MIDI App Controller/controllers                                            |
