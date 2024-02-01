from datetime import date


class note:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, context):
        return {
            "type": "note",
        }
