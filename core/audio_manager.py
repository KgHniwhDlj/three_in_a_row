import pygame
from core.setting_deploy import get_resource_path


class AudioManager:
    _instance = None

    @classmethod
    def instance(cls):
        if not cls._instance:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # музыка
        pygame.mixer.music.load(get_resource_path("assets/music/lobby.wav"))
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)  # зацикливание

        self.music_on = True
        self.sound_on = True
        # sfx
        self._effects = {
            name: pygame.mixer.Sound(get_resource_path(f"assets/sfx/{name}.wav"))
            for name in ["click", "swap", "rocket", "falling", "boom", "add_bonus", "nice_swap", "removed"]
        }

    def toggle_music(self, on: bool):
        self.music_on = on
        if on:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

    def switch_to_lobby(self):
        pygame.mixer.music.load(get_resource_path("assets/music/lobby.wav"))
        if self.music_on:
            pygame.mixer.music.play(-1)

    def switch_to_game(self):
        pygame.mixer.music.load(get_resource_path("assets/music/in_game.wav"))
        if self.music_on:
            pygame.mixer.music.play(-1)

    def toggle_sound(self, on: bool):
        self.sound_on = on

    def play_sound(self, name: str, volume: float = 0.8):
        if self.sound_on and name in self._effects:
            snd = self._effects[name]
            snd.set_volume(volume)
            snd.play()
