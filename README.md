# tlaplus-cli has moved to tlaup

This project is now **tlaup**.

* Repository: https://github.com/nikolskiy/tlaup
* PyPI: https://pypi.org/project/tlaup/

`tlaplus-cli` is no longer maintained, and this repository is archived. The last release, 0.8.3, contains no code of its own: it installs `tlaup` and keeps the old `tla` command working by printing a notice and running the same command through `tlaup`.

## Switching

```bash
uv tool uninstall tlaplus-cli
uv tool install tlaup
```

Then use `tlaup` wherever you used `tla`, for example `tlaup tools install` and `tlaup tlc MySpec`. Installed toolsets, custom modules and the config file stay where they are, so nothing needs to be reinstalled.
