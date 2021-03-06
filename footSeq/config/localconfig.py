# AUTOGENERATED! DO NOT EDIT! File to edit: 000_config.ipynb (unless otherwise specified).

__all__ = ['CONFIG', 'DB_HOSTS']

# Cell
import toml
import logging

# Read local `config.toml` file.
CONFIG = toml.load("/secrets/config.toml")

## defined database hosts
DB_HOSTS = set([db for db in CONFIG["databases"]])

## config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')