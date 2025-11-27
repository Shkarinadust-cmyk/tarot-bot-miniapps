import random

class TarotLogic:
    def __init__(self):
        self.cards = [
            "Шут", "Маг", "Верховная Жрица", "Императрица", "Император"
        ]

    async def generate_tarot_response(self, question):
        card = random.choice(self.cards)
        return f"Выпала карта {card}. Это знак!"

tarot_logic = TarotLogic()
