# Holder Change ERP Integration

Webforms validates the holder-change payload before calling the ERP facade
`som.holder.change.www`. ERP owns persistence, business rules, M1 creation,
payment processing, signing, and asynchronous execution.

## Flow

1. Call `create_request(payload)`. Bank requests return `awaiting_signature`;
   card requests return `awaiting_payment`.
2. For cards, call `add_payment_card_data(request_id, cups, card_values)` with
   tokenized card data. The request moves to `awaiting_signature`.
3. Call `sign_request(request_id, cups)` and redirect the holder to the URL.
4. When the signature is complete, call `execute_request(request_id, cups)`.
   ERP queues execution and returns `queued`.

`create_request` rejects a second active request for the same CUPS with
`REQUEST_IN_PROGRESS`. Active requests are `received`, `awaiting_payment`,
`awaiting_signature`, and `queued`.

## States

`received` -> `awaiting_payment` or `awaiting_signature` -> `queued` ->
`completed`. Failures are persisted as `validation_error` or `execution_error`.

`execute_request` requires a completed signature. Repeated queue deliveries are
serialized on the request and a completed request returns its existing M1 and
result contract references.

## Security

All request-specific operations require both `request_id` and the matching
CUPS, including tokenized card submission. Card numbers must never be sent to
ERP; `card_values` contains only the provider token, masked number, expiry date,
and credential-on-file transaction ID.
