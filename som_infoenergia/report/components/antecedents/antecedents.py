class antecedents:
    def get_data(self, cursor, uid, object, extra_text, context):
        return {
            "nom_titular": object.partner_id.name,
            "direccio": object.polissa_id.cups_direccio
            if object.polissa_id
            else "ERROR no polissa",
            "cups": object.polissa_id.cups.name if object.polissa_id else "ERROR no polissa",
            "consum_anual": extra_text.get("consum_anual", "ERROR EXTRA TEXT: sense consum anual"),
        }
