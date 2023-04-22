import curses
import os
from typing import TYPE_CHECKING, List, Dict, Any
from client import Client, State, ActionType
from game import Deck, Card

if TYPE_CHECKING:
    from _curses import _CursesWindow
    Window = _CursesWindow
else:
    Window = Any


def draw_game(stdscr: Window, data: Dict[str, Any]):
    player_id: int = data.get('player_id')
    player_decks: List[Deck] = data.get('decks')
    table: List[List[Card]] = data.get("table")
    turn: int = data.get("turn")

    client_deck = player_decks[player_id]

    stdscr.erase()

    stdscr.addstr("table: ")

    for idx, card_group in enumerate(table):
        stdscr.addstr(f"{[card.value for card in card_group]}")
        if idx+1 < len(table):
            stdscr.addstr(" -> ")

    stdscr.addstr("\n")

    for idx, deck in enumerate(player_decks):
        if idx != player_id:
            turn_mark = "> " if turn == idx else "  "
            card_count = len(deck.cards)
            card_text = "cards" if card_count != 1 else "card"
            stdscr.addstr(
                f"{turn_mark}player {idx+1}: {card_count} {card_text}\n")

    turn_mark = "> " if turn == player_id else "  "
    stdscr.addstr(f"{turn_mark}player {player_id+1}:\n")
    for card in client_deck.cards:
        stdscr.addstr(f"{card.value} ")

    stdscr.refresh()


def main(stdscr: Window):
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    client = Client()

    player_decks: List[Deck] = []
    table: List[List[Card]] = []

    player_id = -1
    should_play = False

    selected_action = 0
    action_text = ["play", "pass"]

    selecting_card = False

    range_selection = False
    range_start = -1

    card_select_cursor = 0

    stdscr.clear()
    stdscr.refresh()
    run = True
    while run:
        while len(client.state):
            state = client.state.pop()

            if state == State.WAITING:
                stdscr.clear()
                stdscr.addstr("waiting for players")
                stdscr.refresh()

            elif state == State.END:
                run = False

            elif state == State.UPDATE_GAME:
                player_id: int = client.data.get('player_id')
                player_decks = client.data.get("decks")
                table = client.data.get("table")
                # turn: int = client.data.get("turn")

            elif state == State.PLAY_MF:
                should_play = True

        if len(client.data):
            draw_game(stdscr, client.data)

        if selecting_card and not range_selection:
            client_deck = player_decks[player_id]

            tens_before = len(
                [1 for card in client_deck.cards[:card_select_cursor] if card.rank == 10])

            stdscr.addstr("\n")
            cy, cx = stdscr.getyx()

            stdscr.move(cy, cx+(card_select_cursor*2)+tens_before)
            stdscr.addstr(f"^\n")

            key = stdscr.getch()

            isenter = key == curses.KEY_ENTER or key == 13 or key == 10

            if key == curses.KEY_RIGHT:
                card_select_cursor += 1
                card_select_cursor %= len(client_deck.cards)
            elif key == curses.KEY_LEFT:
                card_select_cursor -= 1
                card_select_cursor %= len(client_deck.cards)

            elif key == curses.KEY_BACKSPACE:
                selecting_card = False
                should_play = True
                card_select_cursor = 0

                cy, cx = stdscr.getyx()
                stdscr.move(cy-1, 0)
                stdscr.clrtoeol()
                cy, cx = stdscr.getyx()
                stdscr.move(cy-1, 0)

            elif isenter:
                # TODO: only allow player to select card with higher rank than table, and only if player has enough cards, except J

                can_play = True

                if len(table) > 0:
                    table_card_group = table[-1]

                    curr_card_group: List[Card] = []
                    for n in range(card_select_cursor, len(client_deck.cards)):
                        card = client_deck.cards[n]
                        if len(curr_card_group):
                            if card.rank != curr_card_group[0].rank:
                                break
                        curr_card_group.append(card)
                    if curr_card_group[0].rank != 13:
                        if curr_card_group[0].rank <= table_card_group[0].rank:
                            can_play = False

                        if len(curr_card_group) < len(table_card_group):
                            can_play = False

                if can_play:
                    range_selection = True
                    range_start = card_select_cursor

        elif selecting_card and range_selection:
            client_deck = player_decks[player_id]

            tens_before = len(
                [1 for card in client_deck.cards[:range_start] if card.rank == 10])

            stdscr.addstr("\n")
            cy, cx = stdscr.getyx()

            stdscr.move(cy, cx+(range_start*2)+tens_before)
            stdscr.addstr(f"^", curses.color_pair(1))

            if len(table) > 0:
                card = client_deck.cards[range_start]
                if card.rank != 13:
                    table_card_group = table[-1]
                    card_select_cursor = range_start+len(table_card_group)-1

            for x in range(card_select_cursor-range_start):
                if client_deck.cards[range_start+x].rank == 10:
                    stdscr.addstr(" ")
                stdscr.addstr(" ^", curses.color_pair(1))

            stdscr.addstr("\n")

            key = stdscr.getch()

            isenter = key == curses.KEY_ENTER or key == 13 or key == 10

            if key == curses.KEY_RIGHT:
                if card_select_cursor < len(client_deck)-1:
                    curr_card = client_deck.cards[card_select_cursor]
                    next_card = client_deck.cards[card_select_cursor+1]

                    if curr_card.rank == next_card.rank:
                        card_select_cursor += 1

                if len(table):
                    table_card_group = table[-1]

                    if 1+card_select_cursor-range_start > len(table_card_group):
                        card_select_cursor = len(table_card_group)

            elif key == curses.KEY_LEFT:
                if card_select_cursor > range_start:
                    card_select_cursor -= 1

            elif key == curses.KEY_BACKSPACE:
                range_selection = False
                card_select_cursor = range_start
                range_start = -1

            elif isenter:
                card_rank = client_deck.cards[range_start].rank
                card_quantity = 1+card_select_cursor-range_start

                client.do_action(ActionType.PLAY, {
                                 "card_rank": card_rank, "card_quantity": card_quantity})

                selecting_card = False
                should_play = False
                range_selection = False
                range_start = -1
                selected_action = 0
                card_select_cursor = 0

        if should_play:
            cy, cx = stdscr.getyx()
            stdscr.move(cy+2, 0)

            for c in range(2):
                selected_text = "> " if c == selected_action else "  "
                stdscr.addstr(f"{selected_text}{action_text[c]}\n")

            stdscr.addstr("\n")

            key = stdscr.getch()

            if key == curses.KEY_UP:
                selected_action -= 1
                selected_action %= len(action_text)
            if key == curses.KEY_DOWN:
                selected_action += 1
                selected_action %= len(action_text)

            isenter = key == curses.KEY_ENTER or key == 13 or key == 10

            if isenter:
                should_play = False
                action_type = ActionType.PASS if selected_action else ActionType.PLAY

                if action_type == ActionType.PASS:
                    client.do_action(action_type)
                    selected_action = 0
                else:
                    selected_action = 0
                    selecting_card = True

            stdscr.refresh()

        # is_escape = key == 27
        # if is_escape:
        #     break


if __name__ == "__main__":
    os.environ.setdefault("ESCDELAY", "25")
    curses.wrapper(main)
