# som_gurb

## Diagrama d'estats d'una agrupació (GURB)

```mermaid
graph TD
    act_draft["draft"]
    act_first_opening["first_opening"]
    act_complete["complete"]
    act_incomplete["incomplete"]
    act_registered["registered"]
    act_in_process["in_process"]
    act_active["active"]
    act_active_inc["active_inc"]
    act_active_crit_inc["active_crit_inc"]
    act_reopened["reopened"]

    act_draft -->|button_open| act_first_opening
    act_first_opening -->|button_close_first_opening validate_first_opening_complete| act_complete
    act_first_opening -->|button_close_first_opening validate_first_opening_incomplete| act_incomplete
    act_complete -->|button_register| act_registered
    act_registered -->|button_process| act_in_process
    act_in_process -->|button_activate| act_active
    act_active -->|validate_active_incomplete| act_active_inc
    act_active_inc -->|validate_active_critic_incomplete| act_active_crit_inc
    act_active_inc -->|button_reopen_active_incomplete| act_reopened
    act_active_crit_inc -->|button_reopen_active_critical_incomplete| act_reopened
    act_reopened -->|button_close_reopening validate_reopening_complete| act_incomplete
    act_reopened -->|button_close_reopening validate_reopening_incomplete| act_complete
    act_incomplete -->|validate_incomplete_complete| act_complete
    act_incomplete -->|button_first_reopening| act_first_opening

```
## Diagrama d'estats d'un contracte (CUPS) dins una agrupació (GURB)

```mermaid
graph TD
    act_draft_cups["draft"]
    act_comming_registration["comming_registration"]
    act_comming_modification["comming_modification"]
    act_comming_cancellation["comming_cancellation"]
    act_atr_pending["atr_pending"]
    act_active_cups["active"]
    act_cancel["cancel"]

    act_draft_cups -->|button_create_cups| act_comming_registration
    act_draft_cups -->|button_undo_cups| act_cancel
    act_comming_registration -->|button_activate_cups| act_active_cups
    act_active_cups -->|button_pending_modification| act_comming_modification
    act_comming_modification -->|button_activate_modification| act_active_cups
    act_active_cups -->|button_coming_cancellation| act_comming_cancellation
    act_comming_cancellation -->|button_cancel_cups| act_cancel
    act_comming_cancellation -->|button_discard_comming_cancellation_cups| act_active_cups
    act_cancel -->|button_reactivate_cups| act_comming_registration
    act_active_cups -->|button_atr_pending| act_atr_pending
    act_atr_pending -->|button_reject_atr| act_active_cups
    act_atr_pending -->|button_confirm_atr| act_comming_cancellation
