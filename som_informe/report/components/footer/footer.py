from datetime import date


class footer:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, context):
        pol_data = wiz.polissa
        has_atr = context.get("has_atr", False)
        return {
            "show_atr_disclaimer": has_atr,
            "type": "footer",
            "create_date": date.today().strftime("%d/%m/%Y"),
        }
