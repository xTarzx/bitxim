import socket
from network import send_to, Message, MSG_TYPE, recv_from

from typing import List
from game import Card, Deck, get_full_deck
from random import shuffle


HOST, PORT = "0.0.0.0", 42069

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

server_sock.bind((HOST, PORT))
server_sock.listen()

print("waiting for players")


def deal_cards(players: List[Deck]):
    cards = get_full_deck()
    shuffle(cards)

    t = 0
    l = len(players)
    while len(cards):
        players[t].add_card(cards.pop())
        t += 1
        t %= l


player_n = 4

joined = 0
conns = []
while joined < player_n:
    conn, addr = server_sock.accept()
    joined += 1
    print(f"player {joined} joined")
    conns.append(conn)
    send_to(conn, Message(MSG_TYPE.SYSTEM_WAIT))


player_decks: List[Deck] = [Deck() for _ in range(player_n)]
deal_cards(player_decks)


def relay_game_data(conns, table, turn, player_decks):
    for player_id, conn in enumerate(conns):
        send_to(conn, Message(MSG_TYPE.GAME_DATA, data={
            "decks": player_decks, "player_id": player_id, "turn": turn, "table": table}))


table: List[List[Card]] = []
turn = 0
started_turn = turn
last_player = -1

run = True
while run:
    if not player_decks[turn].has_cards():
        turn += 1
        turn %= player_n

        if turn == started_turn:
            table.clear()
            turn = last_player
            started_turn = turn

        continue

    players_with_cards = [1 for deck in player_decks if deck.has_cards()]
    if len(players_with_cards) == 1:
        run = False
        continue

    relay_game_data(conns, table, turn, player_decks)
    send_to(conns[turn], Message(MSG_TYPE.PLAY_MF))

    msg: Message = recv_from(conns[turn])
    action = msg.data.get("action_type")

    if action == "play":
        card_rank = msg.data.get("card_rank")
        card_quantity = msg.data.get("card_quantity")

        card_rank_begin = -1
        for idx, card in enumerate(player_decks[turn].cards):
            if card.rank == card_rank:
                card_rank_begin = idx
                break

        cards = []
        for _ in range(card_quantity):
            cards.append(player_decks[turn].cards.pop(card_rank_begin))

        table.append(cards)
        last_player = turn

        if card_rank == 13:
            table.clear()
            turn = last_player
            started_turn = turn
            continue
    turn += 1
    turn %= player_n

    if turn == started_turn:
        table.clear()
        turn = last_player
        started_turn = turn


for conn in conns:
    send_to(conn, Message(MSG_TYPE.SYSTEM_END))

server_sock.close()
