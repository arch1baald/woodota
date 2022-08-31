import json
from enum import Enum
from pathlib import PosixPath
from functools import lru_cache
from typing import Type, List, Dict, Tuple

import pandas as pd
import numpy as np


class UnitToName(str, Enum):
    """
    Converts interval unit field to combatlog name with respect to OpenDota rules
    https://raw.githubusercontent.com/odota/dotaconstants/master/build/hero_names.json
    https://raw.githubusercontent.com/SteamDatabase/GameTracking-Dota2/master/game/dota/bin/linuxsteamrt64/libserver_strings.txt
    """
    CDOTA_Unit_Hero_Abaddon = 'npc_dota_hero_abaddon'
    CDOTA_Unit_Hero_AbyssalUnderlord = 'npc_dota_hero_abyssal_underlord'
    CDOTA_Unit_Hero_Alchemist = 'npc_dota_hero_alchemist'
    CDOTA_Unit_Hero_AncientApparition = 'npc_dota_hero_ancient_apparition'
    CDOTA_Unit_Hero_AntiMage = 'npc_dota_hero_antimage'
    CDOTA_Unit_Hero_ArcWarden = 'npc_dota_hero_arc_warden'
    CDOTA_Unit_Hero_Axe = 'npc_dota_hero_axe'
    CDOTA_Unit_Hero_Bane = 'npc_dota_hero_bane'
    CDOTA_Unit_Hero_Batrider = 'npc_dota_hero_batrider'
    CDOTA_Unit_Hero_Beastmaster = 'npc_dota_hero_beastmaster'
    CDOTA_Unit_Hero_Bloodseeker = 'npc_dota_hero_bloodseeker'
    CDOTA_Unit_Hero_BountyHunter = 'npc_dota_hero_bounty_hunter'
    CDOTA_Unit_Hero_Brewmaster = 'npc_dota_hero_brewmaster'
    CDOTA_Unit_Hero_Bristleback = 'npc_dota_hero_bristleback'
    CDOTA_Unit_Hero_Broodmother = 'npc_dota_hero_broodmother'
    CDOTA_Unit_Hero_Centaur = 'npc_dota_hero_centaur'
    CDOTA_Unit_Hero_ChaosKnight = 'npc_dota_hero_chaos_knight'
    CDOTA_Unit_Hero_Chen = 'npc_dota_hero_chen'
    CDOTA_Unit_Hero_Clinkz = 'npc_dota_hero_clinkz'
    CDOTA_Unit_Hero_CrystalMaiden = 'npc_dota_hero_crystal_maiden'
    CDOTA_Unit_Hero_DarkSeer = 'npc_dota_hero_dark_seer'
    CDOTA_Unit_Hero_DarkWillow = 'npc_dota_hero_dark_willow'
    CDOTA_Unit_Hero_Dawnbreaker = 'npc_dota_hero_dawnbreaker'
    CDOTA_Unit_Hero_Dazzle = 'npc_dota_hero_dazzle'
    CDOTA_Unit_Hero_DeathProphet = 'npc_dota_hero_death_prophet'
    CDOTA_Unit_Hero_Disruptor = 'npc_dota_hero_disruptor'
    CDOTA_Unit_Hero_DoomBringer = 'npc_dota_hero_doom_bringer'
    CDOTA_Unit_Hero_DragonKnight = 'npc_dota_hero_dragon_knight'
    CDOTA_Unit_Hero_DrowRanger = 'npc_dota_hero_drow_ranger'
    CDOTA_Unit_Hero_EarthSpirit = 'npc_dota_hero_earth_spirit'
    CDOTA_Unit_Hero_Earthshaker = 'npc_dota_hero_earthshaker'
    CDOTA_Unit_Hero_Elder_Titan = 'npc_dota_hero_elder_titan'
    CDOTA_Unit_Hero_EmberSpirit = 'npc_dota_hero_ember_spirit'
    CDOTA_Unit_Hero_Enchantress = 'npc_dota_hero_enchantress'
    CDOTA_Unit_Hero_Enigma = 'npc_dota_hero_enigma'
    CDOTA_Unit_Hero_FacelessVoid = 'npc_dota_hero_faceless_void'
    CDOTA_Unit_Hero_Furion = 'npc_dota_hero_furion'
    CDOTA_Unit_Hero_Grimstroke = 'npc_dota_hero_grimstroke'
    CDOTA_Unit_Hero_Gyrocopter = 'npc_dota_hero_gyrocopter'
    CDOTA_Unit_Hero_Hoodwink = 'npc_dota_hero_hoodwink'
    CDOTA_Unit_Hero_Huskar = 'npc_dota_hero_huskar'
    CDOTA_Unit_Hero_Invoker = 'npc_dota_hero_invoker'
    CDOTA_Unit_Hero_Jakiro = 'npc_dota_hero_jakiro'
    CDOTA_Unit_Hero_Juggernaut = 'npc_dota_hero_juggernaut'
    CDOTA_Unit_Hero_KeeperOfTheLight = 'npc_dota_hero_keeper_of_the_light'
    CDOTA_Unit_Hero_Kunkka = 'npc_dota_hero_kunkka'
    CDOTA_Unit_Hero_Legion_Commander = 'npc_dota_hero_legion_commander'
    CDOTA_Unit_Hero_Leshrac = 'npc_dota_hero_leshrac'
    CDOTA_Unit_Hero_Lich = 'npc_dota_hero_lich'
    CDOTA_Unit_Hero_Life_Stealer = 'npc_dota_hero_life_stealer'
    CDOTA_Unit_Hero_Lina = 'npc_dota_hero_lina'
    CDOTA_Unit_Hero_Lion = 'npc_dota_hero_lion'
    CDOTA_Unit_Hero_LoneDruid = 'npc_dota_hero_lone_druid'
    CDOTA_Unit_Hero_Luna = 'npc_dota_hero_luna'
    CDOTA_Unit_Hero_Lycan = 'npc_dota_hero_lycan'
    CDOTA_Unit_Hero_Magnataur = 'npc_dota_hero_magnataur'
    CDOTA_Unit_Hero_Marci = 'npc_dota_hero_marci'
    CDOTA_Unit_Hero_Mars = 'npc_dota_hero_mars'
    CDOTA_Unit_Hero_Medusa = 'npc_dota_hero_medusa'
    CDOTA_Unit_Hero_Meepo = 'npc_dota_hero_meepo'
    CDOTA_Unit_Hero_Mirana = 'npc_dota_hero_mirana'
    CDOTA_Unit_Hero_MonkeyKing = 'npc_dota_hero_monkey_king'
    CDOTA_Unit_Hero_Morphling = 'npc_dota_hero_morphling'
    CDOTA_Unit_Hero_Naga_Siren = 'npc_dota_hero_naga_siren'
    CDOTA_Unit_Hero_Necrolyte = 'npc_dota_hero_necrolyte'
    CDOTA_Unit_Hero_Nevermore = 'npc_dota_hero_nevermore'
    CDOTA_Unit_Hero_NightStalker = 'npc_dota_hero_night_stalker'
    CDOTA_Unit_Hero_Nyx_Assassin = 'npc_dota_hero_nyx_assassin'
    CDOTA_Unit_Hero_Obsidian_Destroyer = 'npc_dota_hero_obsidian_destroyer'
    CDOTA_Unit_Hero_Ogre_Magi = 'npc_dota_hero_ogre_magi'
    CDOTA_Unit_Hero_Omniknight = 'npc_dota_hero_omniknight'
    CDOTA_Unit_Hero_Oracle = 'npc_dota_hero_oracle'
    CDOTA_Unit_Hero_Pangolier = 'npc_dota_hero_pangolier'
    CDOTA_Unit_Hero_PhantomAssassin = 'npc_dota_hero_phantom_assassin'
    CDOTA_Unit_Hero_PhantomLancer = 'npc_dota_hero_phantom_lancer'
    CDOTA_Unit_Hero_Phoenix = 'npc_dota_hero_phoenix'
    CDOTA_Unit_Hero_PrimalBeast = 'npc_dota_hero_primal_beast'
    CDOTA_Unit_Hero_Puck = 'npc_dota_hero_puck'
    CDOTA_Unit_Hero_Pudge = 'npc_dota_hero_pudge'
    CDOTA_Unit_Hero_Pugna = 'npc_dota_hero_pugna'
    CDOTA_Unit_Hero_QueenOfPain = 'npc_dota_hero_queenofpain'
    CDOTA_Unit_Hero_Rattletrap = 'npc_dota_hero_rattletrap'
    CDOTA_Unit_Hero_Razor = 'npc_dota_hero_razor'
    CDOTA_Unit_Hero_Riki = 'npc_dota_hero_riki'
    CDOTA_Unit_Hero_Rubick = 'npc_dota_hero_rubick'
    CDOTA_Unit_Hero_SandKing = 'npc_dota_hero_sand_king'
    CDOTA_Unit_Hero_ShadowShaman = 'npc_dota_hero_shadow_shaman'
    CDOTA_Unit_Hero_Shadow_Demon = 'npc_dota_hero_shadow_demon'
    CDOTA_Unit_Hero_Shredder = 'npc_dota_hero_shredder'
    CDOTA_Unit_Hero_Silencer = 'npc_dota_hero_silencer'
    CDOTA_Unit_Hero_SkeletonKing = 'npc_dota_hero_skeleton_king'
    CDOTA_Unit_Hero_Skywrath_Mage = 'npc_dota_hero_skywrath_mage'
    CDOTA_Unit_Hero_Slardar = 'npc_dota_hero_slardar'
    CDOTA_Unit_Hero_Slark = 'npc_dota_hero_slark'
    CDOTA_Unit_Hero_Snapfire = 'npc_dota_hero_snapfire'
    CDOTA_Unit_Hero_Sniper = 'npc_dota_hero_sniper'
    CDOTA_Unit_Hero_Spectre = 'npc_dota_hero_spectre'
    CDOTA_Unit_Hero_SpiritBreaker = 'npc_dota_hero_spirit_breaker'
    CDOTA_Unit_Hero_StormSpirit = 'npc_dota_hero_storm_spirit'
    CDOTA_Unit_Hero_Sven = 'npc_dota_hero_sven'
    CDOTA_Unit_Hero_Techies = 'npc_dota_hero_techies'
    CDOTA_Unit_Hero_TemplarAssassin = 'npc_dota_hero_templar_assassin'
    CDOTA_Unit_Hero_Terrorblade = 'npc_dota_hero_terrorblade'
    CDOTA_Unit_Hero_Tidehunter = 'npc_dota_hero_tidehunter'
    CDOTA_Unit_Hero_Tinker = 'npc_dota_hero_tinker'
    CDOTA_Unit_Hero_Tiny = 'npc_dota_hero_tiny'
    CDOTA_Unit_Hero_Treant = 'npc_dota_hero_treant'
    CDOTA_Unit_Hero_TrollWarlord = 'npc_dota_hero_troll_warlord'
    CDOTA_Unit_Hero_Tusk = 'npc_dota_hero_tusk'
    CDOTA_Unit_Hero_Undying = 'npc_dota_hero_undying'
    CDOTA_Unit_Hero_Ursa = 'npc_dota_hero_ursa'
    CDOTA_Unit_Hero_VengefulSpirit = 'npc_dota_hero_vengefulspirit'
    CDOTA_Unit_Hero_Venomancer = 'npc_dota_hero_venomancer'
    CDOTA_Unit_Hero_Viper = 'npc_dota_hero_viper'
    CDOTA_Unit_Hero_Visage = 'npc_dota_hero_visage'
    CDOTA_Unit_Hero_Void_Spirit = 'npc_dota_hero_void_spirit'
    CDOTA_Unit_Hero_Warlock = 'npc_dota_hero_warlock'
    CDOTA_Unit_Hero_Weaver = 'npc_dota_hero_weaver'
    CDOTA_Unit_Hero_Windrunner = 'npc_dota_hero_windrunner'
    CDOTA_Unit_Hero_Winter_Wyvern = 'npc_dota_hero_winter_wyvern'
    CDOTA_Unit_Hero_Wisp = 'npc_dota_hero_wisp'
    CDOTA_Unit_Hero_WitchDoctor = 'npc_dota_hero_witch_doctor'
    CDOTA_Unit_Hero_Zuus = 'npc_dota_hero_zuus'


class Match:
    """Dota 2 match metadata and events from replay"""

    def __init__(self, match_id: int, jsonlines_path: PosixPath | str):
        self.match_id = match_id
        self.jsonlines_path = jsonlines_path
        self._events = None
        self.unit_to_slot = None
        self.slot_to_unit = None
        self.name_to_slot = None
        self.slot_to_name = None
        self.steam_ids = None
        self._players = None

    def __str__(self) -> str:
        parsed = self._events is not None
        return f'Match: {self.match_id}, parsed: {parsed}'

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def events(self) -> List[Dict]:
        if self._events is not None:
            return self._events

        self._parse_events()
        return self._events

    @property
    def players(self) -> List:
        if self._players is not None:
            return self._players

        self._parse_events()
        players = []
        for slot, hero_name, steam_id in zip(self.slot_to_name.keys(), self.name_to_slot.keys(), self.steam_ids):
            player = MatchPlayer(self, slot, hero_name, steam_id)
            players.append(player)
        self._players = players
        return self._players

    @lru_cache
    def _parse_events(self):
        """
        Load events from the parsed replay.

        Note: Memory Intensive!
        """
        if self._events is not None:
            return self._events

        events = []
        unit_to_slot = dict()
        epilogue = None
        with open(self.jsonlines_path, 'r') as fin:
            for line in fin:
                e = json.loads(line)
                events.append(e)

                if e['type'] == 'interval' and e.get('unit'):
                    unit_to_slot[e['unit']] = e['slot']

                if e['type'] == 'epilogue':
                    epilogue = e

        self._events = events
        self.unit_to_slot = unit_to_slot
        self.slot_to_unit = {slot: name for name, slot in self.unit_to_slot.items()}
        self.name_to_slot = {UnitToName[unit].value: slot for unit, slot in unit_to_slot.items()}
        self.slot_to_name = {slot: name for name, slot in self.name_to_slot.items()}
        self.steam_ids = self._get_steam_ids_from_epilogue(epilogue)

    def _get_steam_ids_from_epilogue(self, epilogue: Dict) -> List[int]:
        epilogue = json.loads(epilogue['key'])
        game_info = epilogue['gameInfo_']
        dota_info = game_info['dota_']
        players_info = dota_info['playerInfo_']
        steam_ids = [p['steamid_'] for p in players_info]
        return steam_ids


class TimeSeries(pd.Series):
    def __init__(self, *args: Tuple, **kwargs: Dict):
        super().__init__(*args, **kwargs)

    def t(self, start_time: int = None, end_time: int = None) -> pd.Series:
        if start_time is not None and end_time is not None:
            series = self[(self.index >= start_time) & (self.index <= end_time)]
        elif start_time is not None and end_time is None:
            series = self[(self.index >= start_time)]
        elif end_time is not None and start_time is None:
            series = self[(self.index <= end_time)]
        else:
            series = self
        return series


class MatchPlayer:
    """Dota 2 match participant"""

    def __init__(self, match: Match, slot: int, hero_name: str, steam_id: int = None):
        self.match = match
        self.slot = slot
        self.hero_name = hero_name
        self.steam_id = steam_id
        self.unit = match.slot_to_unit[slot]

    def __str__(self) -> str:
        match_id = self.match.match_id
        slot = self.slot
        hero_name = self.hero_name
        steam_id = self.steam_id
        return f'MatchPlayer at match: {match_id}, slot: {slot}, hero_name: {hero_name}, steam_id: {steam_id}'

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def events(self) -> List[Dict]:
        return self.match.events

    @property
    @lru_cache
    def hp(self) -> TimeSeries:
        time = []
        health = []
        for e in self.events:
            if e['type'] == 'interval' and e.get('unit', 'unknown_unit') == self.unit:
                time.append(e['time'])
                health.append(e['hp'])
        series = TimeSeries(index=time, data=health, name='hp')
        return series
