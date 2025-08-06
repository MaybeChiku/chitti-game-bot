import random
import time
import hashlib
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import CARD_ITEMS


class ChittiGame:
    def __init__(self, host_id: int, chat_id: int):
        self.host = host_id
        self.chat_id = chat_id
        self.players = []
        self.started = False
        self.deck = []
        self.player_hands = {}
        self.locked_players = set()
        self.passed_players = set()
        self.turn_order = []
        self.current_player_index = 0
        self.active_button_messages = []
        
        # Generate unique hash for this game
        self.game_hash = self._generate_game_hash()

    def _generate_game_hash(self) -> str:
        """Generate a unique hash for this game session"""
        timestamp = str(time.time())
        chat_data = f"{self.chat_id}_{self.host}_{timestamp}_{random.randint(1000, 9999)}"
        return hashlib.md5(chat_data.encode()).hexdigest()[:8]

    def add_player(self, user_id: int, username: str) -> bool:
        if any(p['id'] == user_id for p in self.players):
            return False
        self.players.append({'id': user_id, 'name': username})
        return True

    def start_game(self):
        self.started = True
        self.locked_players.clear()
        self.passed_players.clear()
        self._create_deck()
        self._deal_cards()
        self._set_turn_order()
        self.active_button_messages.clear()

    def add_button_message(self, message_id, chat_id):
        self.active_button_messages.append((message_id, chat_id))

    def clear_button_messages(self):
        self.active_button_messages.clear()

    def _create_deck(self):
        N = len(self.players)
        self.deck = []
        for item in CARD_ITEMS[:N]:
            self.deck.extend([item] * N)
        random.shuffle(self.deck)

    def _deal_cards(self):
        N = len(self.players)
        for player in self.players:
            self.player_hands[player['id']] = self.deck[:N]
            self.deck = self.deck[N:]

    def _set_turn_order(self):
        self.turn_order = [p['id'] for p in self.players]
        random.shuffle(self.turn_order)
        self.current_player_index = 0

    def _get_next_active_player_id(self, current_id: int) -> int:
        if current_id not in self.turn_order:
            return current_id
        N = len(self.turn_order)
        start_index = self.turn_order.index(current_id)
        for i in range(1, N):
            next_id = self.turn_order[(start_index + i) % N]
            if next_id not in self.locked_players:
                return next_id
        return current_id

    def get_current_player(self):
        if not self.turn_order:
            return None
        for _ in range(len(self.turn_order)):
            player_id = self.turn_order[self.current_player_index]
            if player_id not in self.locked_players:
                return next((p for p in self.players if p['id'] == player_id), None)
            self.current_player_index = (self.current_player_index + 1) % len(self.turn_order)
        return None

    def get_next_player_info(self):
        current = self.get_current_player()
        if not current:
            return None
        next_id = self._get_next_active_player_id(current['id'])
        return next((p for p in self.players if p['id'] == next_id), None)

    def pass_card(self, player_id: int, card_index: int) -> tuple:
        current = self.get_current_player()
        if not current or player_id != current['id']:
            raise ValueError("Not your turn!")
        if player_id in self.locked_players:
            raise ValueError("You've already won!")

        try:
            card_type = CARD_ITEMS[card_index]
        except IndexError:
            raise ValueError("Invalid card")

        hand = self.player_hands[player_id]
        if card_type not in hand:
            raise ValueError("You don't have this card")

        hand.remove(card_type)

        next_id = self._get_next_active_player_id(player_id)
        if next_id in self.locked_players:
            raise ValueError("Next player already won!")

        self.player_hands[next_id].append(card_type)
        self.passed_players.add(player_id)

        self._advance_turn()

        return card_type, next_id

    def get_random_card(self, player_id: int) -> tuple:
        hand = self.player_hands.get(player_id, [])
        if not hand:
            return None, None

        card = random.choice(hand)
        hand.remove(card)

        next_id = self._get_next_active_player_id(player_id)
        if next_id in self.locked_players:
            return None, None

        self.player_hands[next_id].append(card)
        self.passed_players.add(player_id)

        self._advance_turn()

        return card, next_id

    def _advance_turn(self):
        if len(self.locked_players) >= len(self.players) - 1:
            return
        self.current_player_index = (self.current_player_index + 1) % len(self.turn_order)
        while self.turn_order[self.current_player_index] in self.locked_players:
            self.current_player_index = (self.current_player_index + 1) % len(self.turn_order)

    def check_win(self, player_id: int) -> bool:
        """Check if player has matching cards and auto-lock them"""
        if player_id in self.locked_players:
            return True

        hand = self.player_hands.get(player_id, [])
        if not hand:
            return False

        # Check if all cards are the same
        if all(card == hand[0] for card in hand):
            self.locked_players.add(player_id)
            # Don't advance turn here - handle it in the main game logic
            return True
        return False

    def get_card_buttons(self, player_id: int):
        if player_id in self.locked_players:
            return None

        hand = self.player_hands.get(player_id, [])
        if not hand:
            return None

        unique_cards = sorted(set(hand), key=lambda x: CARD_ITEMS.index(x))
        buttons = []
        row = []

        for i, card in enumerate(unique_cards):
            count = hand.count(card)
            row.append(InlineKeyboardButton(
                text=f"{card} ×{count}",
                callback_data=f"pass_{CARD_ITEMS.index(card)}_{self.game_hash}"
            ))

            if len(row) == 2 or i == len(unique_cards) - 1:
                buttons.append(row)
                row = []

        return InlineKeyboardMarkup(buttons) if buttons else None

    def is_valid_hash(self, provided_hash: str) -> bool:
        """Check if the provided hash matches this game's hash"""
        return provided_hash == self.game_hash

    def distribute_remaining_cards(self, locked_player_id: int):
        """When a player gets locked, distribute their remaining cards to next active players in turn order"""
        remaining_cards = self.player_hands.get(locked_player_id, [])
        if not remaining_cards:
            return []
        
        # Get all active players (not locked)
        active_players = [p['id'] for p in self.players if p['id'] not in self.locked_players]
        
        if not active_players:
            return []  # No active players left
        
        # Find starting position of the locked player in turn order
        try:
            locked_index = self.turn_order.index(locked_player_id)
        except ValueError:
            locked_index = 0
        
        distributed_cards = []
        active_index = 0
        
        # Distribute each card to next active players in sequence
        for card in remaining_cards:
            # Find next active player starting from locked player's position
            found_player = False
            for i in range(len(self.turn_order)):
                check_index = (locked_index + 1 + i) % len(self.turn_order)
                potential_player = self.turn_order[check_index]
                
                if potential_player not in self.locked_players:
                    self.player_hands[potential_player].append(card)
                    distributed_cards.append((card, potential_player))
                    found_player = True
                    break
            
            # If no player found in turn order, use first active player
            if not found_player and active_players:
                receiver_id = active_players[0]
                self.player_hands[receiver_id].append(card)
                distributed_cards.append((card, receiver_id))
        
        # Clear the locked player's hand
        self.player_hands[locked_player_id] = []
        
        return distributed_cards