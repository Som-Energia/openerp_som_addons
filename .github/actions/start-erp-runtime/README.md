# Start ERP runtime action

This action starts an exportable ERP runtime after bootstrap.

## Contract

- It first builds the ERP data model by running:
  - `destral -t OOBaseTests.test_translate_modules -d <database>`
- Then it starts OpenERP in background with XML-RPC exposed.
- Default external port is `8069` (configurable through `xmlrpc-port`).
- It waits until the TCP port is reachable and publishes readiness artifacts.

## Inputs

- `database` (required): database name used for model build and runtime startup.
- `xmlrpc-port` (optional, default `8069`): port exposed by ERP XML-RPC server.
- `bind-address` (optional, default `0.0.0.0`): listening interface.
- `health-timeout` (optional, default `180`): max wait seconds until ready.

## Exported environment variables

- `ERP_READY_FILE`: path to readiness flag file.
- `ERP_PID_FILE`: path containing ERP process PID.
- `ERP_LOG_FILE`: path to OpenERP server logs.
- `ERP_XMLRPC_PORT`: effective exposed XML-RPC port.
