# Examples

Some examples of configurations built using ARouteServer can be found within this directory.

## `default` - Default settings

Configurations built using the default `general.yml` and `clients.yml` files distributed with the project.

## `rich` - Feature-rich configuration

Configurations that feature advanced NEXT_HOP filtering, invalid/private/*transit-free* ASNs filtering, RPKI validation, propagation control BGP communities and more.

## `bird_hooks` - Configuration customization

A scenario where *hooks* have been used to inject custom snippet of configuration into the main configuration built by ARouteServer.

## `clients-from-euroix` - Euro-IX JSON file integration

Some lists of clients built starting from Euro-IX JSON files exported by some IXs.

## `auto-config` - general.yml files generated using the `configure` command

`general.yml` configurations files generated with the `configure` command.

## `bird2_rpki_rtr` - BIRD v2 RTR protocol configuration

An example on how to use BIRD v2 built-in RTR protocol support.
