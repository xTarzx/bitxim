from __future__ import annotations
from typing import List


class Card:
    def __init__(self, rank, value):
        self.rank = rank
        self.value = value

    def __lt__(self, other: Card):
        return self.rank < other.rank

    def __repr__(self) -> str:
        return f"Card(rank={self.rank}, value={self.value})"


class Deck:
    def __init__(self):
        self.cards: List[Card] = []

    def add_card(self, card: Card):
        self.cards.append(card)
        self.cards.sort()

    def __str__(self) -> str:
        return f"{self.cards}"

    def __len__(self):
        return len(self.cards)

    def has_cards(self) -> bool:
        return len(self) > 0


def get_full_deck() -> List[Card]:
    cards = []

    for n in range(1, 11):
        cards.extend([Card(rank=n, value=n) for _ in range(4)])

    for _ in range(4):
        cards.append(Card(11, "Q"))
    for _ in range(4):
        cards.append(Card(12, "K"))
    for _ in range(4):
        cards.append(Card(13, "J"))

    return cards
