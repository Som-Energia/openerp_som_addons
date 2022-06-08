# som_modul_fulla
OpenERP module that loads all installed modules in Som Energia

## How we build __terp__.py file?
We grep the init of OpenERP to get the list of modules:
```bash
awk '/load/ {print $4}' output_init.log
```

## How to run all tests
You need to uses https://github.com/gisce/destral/
```bash
destral -m som_modul_fulla -a
```

## How to get an OpenERP instance with all Som Energia modules instalded
```bash
destral -m som_modul_fulla
openerp-server.py
```
