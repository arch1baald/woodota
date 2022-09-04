import abc

from dota import MatchPlayer
from utils import TimeSeries, TimeTable


class BaseSigal(abc.ABC):

    def __init__(self, player: MatchPlayer):
        self.player = player

    def __str__(self) -> str:
        return f'{self.__class__.__name__} for {self.player}'

    def __repr__(self) -> str:
        return self.__str__()

    # @abc.abstractmethod()
    def detect(self):
        pass

    @property
    def hp(self) -> TimeSeries:
        return self.player.hp

    @property
    def max_hp(self) -> TimeSeries:
        return self.player.max_hp

    @property
    def dhp(self) -> TimeSeries:
        return self.player.dhp

    @property
    def sdhp(self) -> TimeSeries:
        return self.player.sdhp


class SignalHP(BaseSigal):
    HP_RATE_THRESHOLD = -20
    MAX_HP_THRESHOLD = 0.3

    def __init__(self, player: MatchPlayer):
        super().__init__(player)

    def get_negative_hp_trend(self) -> TimeSeries:
        binary_mask = self.sdhp < SignalHP.HP_RATE_THRESHOLD
        return TimeSeries(binary_mask)

    def get_low_hp(self) -> TimeSeries:
        series = self.hp / self.max_hp
        binary_mask = series < SignalHP.MAX_HP_THRESHOLD
        return binary_mask

    def detect(self) -> TimeSeries:
        pass
