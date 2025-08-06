import random
from typing import Dict, Optional
from .game import ChittiGame          

class GameManager:
    def __init__(self):
        self.games: Dict[int, ChittiGame] = {}        # chat_id -> game
        self.player_chat: Dict[int, int] = {}         # user_id -> chat_id

    def create_game(self, host_id: int, chat_id: int) -> ChittiGame:
        # Check if host is already in another active game
        if host_id in self.player_chat:
            existing_chat = self.player_chat[host_id]
            existing_game = self.games.get(existing_chat)
            if existing_game and existing_chat != chat_id:
                return None  # User already in another group's game

        game = ChittiGame(host_id, chat_id)
        self.games[chat_id] = game
        self.player_chat[host_id] = chat_id
        return game

    def get_game(self, chat_id: int) -> Optional[ChittiGame]:
        return self.games.get(chat_id)

    def get_game_by_player(self, user_id: int) -> Optional[ChittiGame]:
        chat_id = self.player_chat.get(user_id)
        return self.games.get(chat_id) if chat_id else None

    def get_player_active_chat(self, user_id: int) -> Optional[int]:
        """Get the chat_id where user is currently playing"""
        return self.player_chat.get(user_id)

    def add_player(self, chat_id: int, user_id: int, username: str) -> tuple[bool, str]:
        """
        Add player to game. Returns (success, message)
        """
        game = self.games.get(chat_id)
        if not game:
            return False, "No active game found in this group."

        # Check if player is already in another group's game
        if user_id in self.player_chat:
            existing_chat = self.player_chat[user_id]
            if existing_chat != chat_id:
                existing_game = self.games.get(existing_chat)
                if existing_game:
                    return False, "You're already playing in another group! Finish that game first."

        success = game.add_player(user_id, username)
        if success:
            self.player_chat[user_id] = chat_id
            return True, "Successfully joined!"
        else:
            return False, "You're already in this game."

    def remove_player(self, chat_id: int, user_id: int):
        game = self.games.get(chat_id)
        if game:
            game.players = [p for p in game.players if p['id'] != user_id]
        self.player_chat.pop(user_id, None)

    def end_game(self, chat_id: int):
        game = self.games.pop(chat_id, None)
        if game:
            for p in game.players:
                self.player_chat.pop(p['id'], None)

    def cleanup_inactive_buttons(self, client):
        """Clean up buttons from ended games"""
        # This would be called periodically or when games end
        pass

# single instance used everywhere
game_manager = GameManager()