# Binja Win Docs

_Binary Ninja plugin to display the documentation of a Windows function in a sidebar widget._

![Screenshot from 2023-01-01 12-40-15](https://user-images.githubusercontent.com/8758978/210169502-ceafcb37-53b0-403b-88e7-d018e3932acd.png)

### Description

This plugin adds a sidebar widget to Binary Ninja. If the cursor is set to a `call` instruction the plugin detects the function's name a requests MSDN documentation.

The requested documentation is then displayed in the sidebar widget.

Each documented function is also saved to a cache file named `cache.json` in the current plugin directory, meaning the plugin doesn't requests the doc for the same function everytime.

### Demo

![Desktop 02-01-2023 08-05-21](https://user-images.githubusercontent.com/8758978/210202853-841b973f-8add-4e35-bcf0-dde51ac5aa87.gif)

### Installation Instructions

#### Darwin

Clone this repository into `~/Library/Application Support/Binary Ninja/plugins/`

#### Windows

Clone this repository into `%APPDATA%/Binary Ninja/plugins/`

#### Linux

Clone this repository into `~/.binaryninja/plugins/`


### TODO

- [ ] Improve scrapper
- [ ] Gif demo
- [ ] It might me possible to use binja's context to get the function's name instead of calling BNILs functions


### Credits

- [Eric Hennenfent](https://github.com/ehennenfent) for [binja_explain_instruction](https://github.com/ehennenfent/binja_explain_instruction) which I used as templated for this plugin.
- [Hacking Things](https://github.com/HackingThings) for the [URL I needed to make this work](https://github.com/HackingThings/binja_MSDN_Helper/blob/main/__init__.py#L17).
- kareemovic1000 from the Noun Project for the icon.
