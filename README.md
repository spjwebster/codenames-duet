# 2-player key card generator for Codenames / Codenames Duet

Generates dual-sided key cards for playing Codenames Duet rules either with the original Codenames or with Codenames Duet.

Features:

* Generates individual PNGs or combined PDFs
* Built-in full colour and low ink templates
* Extensible and configurable templates for your own designs
* Repeatable generation using seeded RNG

However, perhaps the most important feature of this tool is that, unlike other key card generators, the generation algorithm used here strictly observes the key card rules given in the official Codenames Duet rules.

# Installation

* Clone / download the repo
* (Optional) Create a pipenv and virtualenv
* Install dependencies: `pip install -r requirements.txt`
* Run `python generate.py` for help on available commands and options

Example to generate full-colour and low-ink PDFs with 100 key cards:

```zsh
python generate.py pdf full-colour low-ink -c 100
```

# TODO

- [x] Remove hard-coded parameterisation of PDF layouts
- [x] Relatedly: Support for non-68mm key cards
- [ ] Support fit-to-height, fit-within and exact-fit card sizing
- [x] Add support for crop marks
- [x] Add support for solid colour bleed regions
- [ ] Better logical separation between layout and template (e.g. bleed zone & crop mark colours)
- [ ] Add support for bleed regions within card templates
- [ ] Add support for loading templates/layouts by relative/absolute file path
- [ ] Create proper test suite for algorithm under CI