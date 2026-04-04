from __future__ import annotations

import logging
import math
from enum import IntEnum
from typing import Callable

from .options import PeaksOfYoreOptions, RequirementsDifficulty, GameMode
from BaseClasses import ItemClassification, Item, Location, CollectionState
from worlds.AutoWorld import World

peak_offset: int = 1
rope_offset: int = 1000
artefact_offset: int = 2000
book_offset: int = 3000
bird_seed_offset: int = 4000
tool_offset: int = 5000
extra_item_offset: int = 6000
free_solo_peak_offset: int = 7000
time_attack_time_offset: int = 8000
time_attack_ropes_offset: int = 9000
time_attack_holds_offset: int = 10000

# To whoever is reviewing this, just know that I pray for you
# I basically rewrote this entire file from scratch, so don't go looking at the differences

class PeaksOfYoreItem(Item):
    game = "Peaks of Yore"

class PeaksOfYoreLocation(Location):
    game = "Peaks of Yore"

class POYItemLocationType(IntEnum):
    PEAK = 1
    ROPE = 1000
    ARTEFACT = 2000
    BOOK = 3000
    BIRDSEED = 4000
    TOOL = 5000
    EXTRA = 6000
    FREESOLO = 7000
    TIMEATTACK_TIME = 8000
    TIMEATTACK_ROPES = 9000
    TIMEATTACK_HOLDS = 10000

class ItemDataOld:
    """
    ItemData is an internal class for me to specify items
    is_starter_item, is_enabled and is_early are all called later to determine how to handle the item
    based on the current options
    """
    name: str
    type: POYItemLocationType
    id: int
    classification: ItemClassification
    is_starter_item: Callable[[PeaksOfYoreOptions], bool]
    is_enabled: Callable[[PeaksOfYoreOptions], bool]
    is_early: Callable[[PeaksOfYoreOptions], bool]

    def __init__(self, name: str, item_id: int, classification: ItemClassification, item_type: POYItemLocationType,
                 is_starter_item: Callable[[PeaksOfYoreOptions], bool] = lambda opts: False,
                 is_enabled: Callable[[PeaksOfYoreOptions], bool] = lambda opts: True,
                 is_early: Callable[[PeaksOfYoreOptions], bool] = lambda opts: False):
        self.name = name
        self.type = item_type
        self.id = item_id
        self.classification = classification
        self.is_starter_item = is_starter_item
        self.is_enabled = is_enabled
        self.is_early = is_early

class ItemData:
    name: str
    type: POYItemLocationType
    id: int
    classification: ItemClassification
    min_count: int
    max_count: int
    is_starter_item: Callable[[PeaksOfYoreOptions], bool]
    is_early: Callable[[PeaksOfYoreOptions], bool]
    is_enabled: Callable[[PeaksOfYoreOptions], bool]

    def __init__(self, name: str, item_id: int, classification: ItemClassification, item_type: POYItemLocationType,
                 min_count = 1, max_count = 1,
                 is_starter_item: Callable[[PeaksOfYoreOptions], bool] = lambda opts: False,
                 is_early: Callable[[PeaksOfYoreOptions], bool] = lambda opts: False,
                 is_enabled: Callable[[PeaksOfYoreOptions], bool] = lambda opts: True):
        self.name = name
        self.type = item_type
        self.id = item_id
        self.classification = classification
        self.min_count = min_count
        self.max_count = max_count
        self.is_starter_item = is_starter_item
        self.is_early = is_early
        self.is_enabled = is_enabled

class LocationData:
    name: str
    type: POYItemLocationType
    id: int
    requirements: Requirements
    enable_override: Callable[[PeaksOfYoreOptions], bool]
    is_event: bool
    has_override: bool

    def __init__(self, name: str, type: POYItemLocationType, loc_id: int, requirements: Requirements=None,
                 enable_override: Callable[[PeaksOfYoreOptions], bool] = None, is_event: bool = False):
        if requirements is None:
            requirements = SimpleRequirements({})
        if enable_override is None:
            self.has_override = False
            enable_override = lambda opts: True
        else:
            self.has_override = True
        self.name = name
        self.type = type
        self.id = loc_id
        self.requirements = requirements
        self.enable_override = enable_override
        self.is_event = is_event

    def get_id(self) -> int | None:
        if self.is_event:
            return None
        return self.id + self.type

class Requirements:
    """
    Requirements is a class to help me specify requirements, difficulties and/or different possible sets of requirements
    can_reach is used by generation logic to check if the requirements are satisfied
    evaluate_items gives **a possible** set of items necessary to satisfy the requirements
    (used to define starting items/what items are marked as progression)

    start_priority is used by AnyRequirements to determine what set of items is to be used to start with
    """
    start_priority: int
    def __init__(self, start_priority: int = 0):
        self.start_priority = start_priority

    def can_reach(self, opts: PeaksOfYoreOptions, state: CollectionState, world: World) -> bool:
        return state.has_all_counts(self.evaluate_items(opts), world.player)

    def evaluate_items(self, opts: PeaksOfYoreOptions) -> dict[str, int]:
        return {}

    def is_empty(self) -> bool:
        return True

    def __and__(self, other): # &
        if not isinstance(other, Requirements):
            return NotImplemented
        return AllRequirements([self, other])

    def __or__(self, other):
        if not isinstance(other, Requirements):
            return NotImplemented
        return AnyRequirements([self, other])

# SimpleRequirements, LeveledRequirements and AllRequirements use default can_reach implementation
class SimpleRequirements(Requirements):
    requirements: dict[str, int]

    def __init__(self, requirements: dict[str, int], start_priority:int = 0):
        super().__init__(start_priority)
        self.requirements = requirements

    def evaluate_items(self, opts: PeaksOfYoreOptions) -> dict[str, int]:
        return self.requirements

    def is_empty(self) -> bool:
        return self.requirements == {}

class AllRequirements(Requirements):
    requirements: list[Requirements]

    def __init__(self, requirements: list[Requirements], start_priority: int = 0):
        super().__init__(start_priority)
        self.requirements = []
        for req in requirements:
            if isinstance(req, AllRequirements):
                self.requirements.extend(req.requirements)
            else:
                self.requirements.append(req)

    def evaluate_items(self, opts: PeaksOfYoreOptions) -> dict[str, int]:
        final: dict[str, int] = {}
        for requirement in self.requirements:
            items: dict[str, int] = requirement.evaluate_items(opts)
            for item in items.keys():
                if item not in final:
                    final[item] = items[item]
                else:
                    final[item] = max(final[item], items[item])
        return final

    def is_empty(self) -> bool:
        return all(reqs.is_empty() for reqs in self.requirements)

class AnyRequirements(Requirements):
    requirements: list[Requirements]

    def __init__(self, requirements: list[Requirements], start_priority: int = 0):
        super().__init__(start_priority)
        self.requirements = []
        for req in requirements:
            if isinstance(req, AnyRequirements):
                self.requirements.extend(req.requirements)
            else:
                self.requirements.append(req)

    def can_reach(self, opts: PeaksOfYoreOptions, state: CollectionState, world: World) -> bool:
        return all(state.has_all_counts(reqs.evaluate_items(opts), world.player) for reqs in self.requirements)

    # returns first set of items with highest priority
    def evaluate_items(self, opts: PeaksOfYoreOptions) -> dict[str, int]:
        prior: int = 0
        req_list: list[Requirements] = []
        for reqs in self.requirements:
            if reqs.start_priority > prior:
                prior = reqs.start_priority
                req_list = []
            if reqs.start_priority == prior:
                req_list.append(reqs)

        if len(req_list) == 0:
            return {}
        return req_list[0].evaluate_items(opts)

    def is_empty(self) -> bool:
        return all(reqs.is_empty() for reqs in self.requirements)

# Default can_reach again :)
class ConditionalRequirements(Requirements):
    requirements: Requirements
    condition: Callable[[PeaksOfYoreOptions], bool]

    def __init__(self, requirements: Requirements, condition: Callable[[PeaksOfYoreOptions], bool], start_priority: int = 0):
        super().__init__(start_priority)
        self.requirements = requirements
        self.condition = condition

    def evaluate_items(self, opts: PeaksOfYoreOptions) -> dict[str, int]:
        return self.requirements.evaluate_items(opts) if self.condition(opts) else {}

    def is_empty(self) -> bool:
        return self.requirements.is_empty()

class LeveledRequirements(ConditionalRequirements):
    def __init__(self, difficulty: RequirementsDifficulty, requirements: Requirements, start_priority: int = 0):
        super().__init__(requirements,  lambda opts: opts.requirements_difficulty == difficulty, start_priority)

def get_rope_requirement(rope_count: int, start_priority = 0) -> Requirements:
    """
    this assumes that the change to make extra ropes worth 2 has been made!!
    requires either ropecount ropes, or ropecount * .75 ropes + rope length upgrade
    Warning: currently broken somehow
    """
    logging.warning("get_rope_requirement may not work correctly at this time but was used!")
    item_count: int = math.ceil(rope_count/2)
    min_item_count: int = math.ceil(item_count*0.75)
    short_rope_addition: int = item_count-min_item_count
    reqs: Requirements = (SimpleRequirements({"Rope Unlock": 1, "Extra Rope": min_item_count})
        & (
            SimpleRequirements({"Extra Rope": short_rope_addition}, 200)   # base case: has required rope count
            | SimpleRequirements({"Rope Length Upgrade": 1}, 0)               # also accepted with 75% ropes and length upgrade
        ))

    if short_rope_addition == 0:
        reqs = SimpleRequirements({"Rope Unlock": 1, "Extra Rope": min_item_count})

    reqs.start_priority = start_priority

    return reqs

class POYRegion:
    """
    POYRegion is used later to define Regions, allowing me to define the regions in this file
    with entry_requirements being a dict of item: count, to define entry requirements
    enable_requirements is called later in regions.py to determine whether to include the region based on the user's options
    e.g. not including the time attack regions if Time Attack is disabled
    """
    name: str
    entry_requirements: Requirements
    enable_requirements: Callable[[PeaksOfYoreOptions], bool]
    is_start: Callable[[PeaksOfYoreOptions], bool]
    subregions: list[POYRegion]
    locations: list[LocationData]
    is_peak: bool
    is_book: bool

    def __init__(self, name: str, entry_requirements: Requirements | dict[str, int]=None, subregions: list[POYRegion]=None,
                 locations: list[LocationData]=None,
                 enable_requirements: Callable[[PeaksOfYoreOptions], bool] = lambda opts: True, is_book: bool = False,
                 is_start: Callable[[PeaksOfYoreOptions], bool] = lambda opts: False):
        if subregions is None:
            subregions = []

        if isinstance(entry_requirements, dict):
            entry_requirements = SimpleRequirements(entry_requirements)
        if entry_requirements is None:
            entry_requirements = SimpleRequirements({})
        if locations is None:
            locations = []

        self.name = name
        self.entry_requirements = entry_requirements
        self.subregions = subregions
        self.locations = locations
        self.enable_requirements = enable_requirements
        self.is_book = is_book
        self.is_peak = False
        self.is_start = is_start

    def get_all_locations_dict(self) -> dict[str, int]:
        """
        Get all locations in the region AND its subregions
        {name: id}
        """
        v = self.get_locations_dict()
        for r in self.subregions:
            v.update(r.get_all_locations_dict())
        return v

    def get_locations_dict(self) -> dict[str, int]:
        """
        Get all location in the region, not it's subregions
        {name: id}
        """
        return {i.name: i.get_id() for i in self.locations}

class PeakRegion(POYRegion):
    """
    PeakRegion is a descendant of POYRegion, and simply helps me by doing the necessary setup by:
     - Adding a location for the peak itself
     - Creating a subregion for Time attack locations (only accessible with the pocketwatch)
     - creating a location for Free Soloing the peak
    """
    peak_id: int
    generate_time_attack: bool

    def __init__(self, name: str, peak_id: int, entry_requirements: Requirements | dict[str,int]=None, subregions=None, locations=None,
                 enable_requirements: Callable[[PeaksOfYoreOptions], bool] = lambda opts: True,
                 generate_time_attack: bool = True, generate_free_solo: bool = False):
        self.peak_id = peak_id
        self.generate_time_attack = generate_time_attack
        self.generate_free_solo = generate_free_solo
        super().__init__(name, entry_requirements, subregions, locations, enable_requirements)
        self.prepare_peak_region()
        self.is_peak = True
        self.is_book = False
        self.is_start = lambda opts: (opts.starting_peak.value == self.peak_id
                                      if opts.game_mode == GameMode.option_peak_unlock
                                      else opts.starting_book.get_start_peak_id() == self.peak_id)

    def prepare_peak_region(self):
        # add a ConditionalRequirement to the peak
        self.entry_requirements = (self.entry_requirements
                                   & ConditionalRequirements(
                                      SimpleRequirements({self.name: 1}),
                                      condition = lambda opts: opts.game_mode == GameMode.option_peak_unlock
                                  ))
        self.locations.append(LocationData(self.name, POYItemLocationType.PEAK, self.peak_id))

        for location in self.locations.copy():
            if location.has_override or not location.requirements.is_empty():
                # the usage of has_override could be moved to regions.py, but this is kinda easier, and that would allow
                # for creation of empty regions
                self.locations.remove(location)
                # move the location to a subregion so it's access requirements can be fulfilled :)
                self.subregions.append(POYRegion(self.name + ": " + location.name.split(": ")[-1],
                                                 location.requirements, locations=[
                        LocationData(location.name, location.type, location.id, None, None, location.is_event)
                    ],
                                                 enable_requirements=location.enable_override))

        if self.generate_free_solo:
            self.subregions.append(POYRegion(
                self.name + " Free Solo", locations=[
                    LocationData(self.name + ": Free Solo", POYItemLocationType.FREESOLO, self.peak_id),
                ], enable_requirements=lambda options: options.include_free_solo,
            ))

        if self.generate_time_attack:
            ta_entry_requirements: Requirements = SimpleRequirements({"Pocketwatch": 1})
            self.subregions.append(POYRegion(
                self.name + " Time Attack", entry_requirements=ta_entry_requirements,
                locations=[
                    LocationData(self.name + ": Time Record", POYItemLocationType.TIMEATTACK_TIME, self.peak_id),
                    LocationData(self.name + ": Ropes Record", POYItemLocationType.TIMEATTACK_ROPES, self.peak_id),
                    LocationData(self.name + ": Holds Record", POYItemLocationType.TIMEATTACK_HOLDS, self.peak_id),
                ], enable_requirements=lambda options: options.include_time_attack))

class BookRegion(POYRegion):
    """
    Similar to PeakRegion, BookRegion is a descendant of POYRegion, that will (semi) automatically be set up as a book.
    """
    def __init__(self, name: str, item_name:str=None, entry_requirements: Requirements | dict[str,int]=None, subregions: list[POYRegion]=None,
                 enable_requirements: Callable[[PeaksOfYoreOptions], bool] = lambda opts: True):
        super().__init__(name, entry_requirements, subregions, None, enable_requirements)
        self.item_name = item_name
        if self.item_name is None:
            self.item_name = name + " Book"
        self.is_peak = False
        self.is_book = True
        self.prepare_book_region()

    def prepare_book_region(self):
        conditional = ConditionalRequirements(SimpleRequirements({f"{self.item_name}": 1}), lambda opts: opts.game_mode == GameMode.option_book_unlock)
        if self.entry_requirements.is_empty():
            self.entry_requirements = conditional
        else:
            self.entry_requirements = self.entry_requirements & conditional

dlc_enabled: Callable[[PeaksOfYoreOptions], bool] = lambda opts: opts.enable_dlc
# simple lambda just to make sure that I don't have to copy this everywhere

# All of the items in the randomiser are defined here, with functions to define whether they are not enabled,
# starter items, or early
all_items: list[ItemData] = [
    # Tools
    ItemData("Pipe", 0, ItemClassification.useful, POYItemLocationType.TOOL),
    ItemData("Rope Length Upgrade", 1, ItemClassification.useful, POYItemLocationType.TOOL),
    ItemData("Barometer", 2, ItemClassification.useful, POYItemLocationType.TOOL,
             is_starter_item=lambda options: options.start_with_barometer),
    ItemData("Progressive Crampons", 3, ItemClassification.progression, POYItemLocationType.TOOL,
             min_count=2, max_count=2),
    ItemData("Monocular", 4, ItemClassification.filler, POYItemLocationType.TOOL),
    ItemData("Phonograph", 5, ItemClassification.filler, POYItemLocationType.TOOL),
    ItemData("Pocketwatch", 6, ItemClassification.progression, POYItemLocationType.TOOL, min_count=0),
    ItemData("Chalkbag", 7, ItemClassification.useful, POYItemLocationType.TOOL,
             is_starter_item=lambda options: options.start_with_chalk),
    ItemData("Rope Unlock", 8, ItemClassification.progression, POYItemLocationType.TOOL,
             is_starter_item=lambda options: options.rope_unlock_mode == 0,
             is_early=lambda options: options.rope_unlock_mode == 1),
    ItemData("Coffee Unlock", 9, ItemClassification.useful, POYItemLocationType.TOOL,
             is_starter_item=lambda options: options.start_with_coffee),
    ItemData("Oil Lamp", 10, ItemClassification.useful, POYItemLocationType.TOOL,
             is_starter_item=lambda options: options.start_with_oil_lamp),
    ItemData("Left Hand", 11, ItemClassification.progression, POYItemLocationType.TOOL,
             is_starter_item=lambda options: options.start_with_hands in (0, 1),
             is_early=lambda options: options.early_hands),
    ItemData("Right Hand", 12, ItemClassification.progression, POYItemLocationType.TOOL,
             is_starter_item=lambda options: options.start_with_hands in (0, 2),
             is_early=lambda options: options.early_hands),
    ItemData("Ice Axes", 13, ItemClassification.useful, POYItemLocationType.TOOL),

    # Books
    ItemData("Fundamentals Book", 0, ItemClassification.progression, POYItemLocationType.BOOK,
             min_count = 0),
    ItemData("Intermediate Book", 1, ItemClassification.progression, POYItemLocationType.BOOK,
             min_count = 0),
    ItemData("Advanced Book", 2, ItemClassification.progression, POYItemLocationType.BOOK,
             min_count = 0),
    ItemData("Northern Range Ticket", 3, ItemClassification.progression, POYItemLocationType.BOOK,
             min_count = 0),

    # Fundamental Peaks
    ItemData("Greenhorn's Top", 0, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Paltry Peak", 1, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Old Mill", 2, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Gray Gully", 3, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Lighthouse", 4, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Old Man Of Sjór", 5, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Giant's Shelf", 6, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Evergreen's End", 7, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("The Twins", 8, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Old Grove's Skelf", 9, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Land's End", 10, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Hangman's Leap", 11, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Old Langr", 12, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Aldr Grotto", 13, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Three Brothers", 14, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Walter's Crag", 15, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("The Great Crevice", 16, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Old Hagger", 17, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Ugsome Storr", 18, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Wuthering Crest", 19, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    # Intermediate Peaks
    ItemData("Porter's Boulder", 20, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Jotunn's Thumb", 21, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Old Skerry", 22, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Hamarr Stone", 23, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Giant's Nose", 24, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Walter's Boulder", 25, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Sundered Sons", 26, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Old Weald's Boulder", 27, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Leaning Spire", 28, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Cromlech", 29, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    # Advanced Peaks
    ItemData("Walker's Pillar", 30, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Eldenhorn", 31, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Great Gaol", 32, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("St. Haelga", 33, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Ymir's Shadow", 34, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    # Expert Peaks
    ItemData("The Great Bulwark", 35, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0),
    ItemData("Solemn Tempest", 36, ItemClassification.progression, POYItemLocationType.PEAK,
             min_count = 0, is_enabled=lambda options: not options.disable_solemn_tempest),

    # artefacts
    ItemData("Old Mill: Hat", 0, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Evergreen's End: Fisherman's Cap", 1, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Old Grove's Skelf: Safety Helmet", 2, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Old Man Of Sjór: Climbing Shoe", 3, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Three Brothers: Shovel", 4, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Giant's Shelf: Sleeping Bag", 5, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Aldr Grotto: Backpack", 6, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Old Langr: Coffee Box", 7, ItemClassification.useful, POYItemLocationType.ARTEFACT),
    ItemData("Wuthering Crest: Coffee Box", 8, ItemClassification.useful, POYItemLocationType.ARTEFACT),
    ItemData("Walker's Pillar: Chalk Box", 9, ItemClassification.useful, POYItemLocationType.ARTEFACT),
    ItemData("Eldenhorn: Chalk Box", 10, ItemClassification.useful, POYItemLocationType.ARTEFACT),
    ItemData("Leaning Spire: Intermediate Trophy", 11, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Ymir's Shadow: Advanced Trophy", 12, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("The Great Bulwark: Expert Trophy", 13, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Gray Gully: Picture Piece #1", 14, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Land's End: Picture Piece #2", 15, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("The Great Crevice: Picture Piece #3", 16, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("St. Haelga: Picture Piece #4", 17, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Great Gaol: Picture Frame", 18, ItemClassification.filler, POYItemLocationType.ARTEFACT),
    ItemData("Walter's Crag: Fundamentals Trophy", 19, ItemClassification.filler, POYItemLocationType.ARTEFACT),

    # Bird seeds
    ItemData("Three Brothers: Bird Seed", 0, ItemClassification.useful, POYItemLocationType.BIRDSEED),
    ItemData("Old Skerry: Bird Seed", 1, ItemClassification.useful, POYItemLocationType.BIRDSEED),
    ItemData("Great Gaol: Bird Seed", 2, ItemClassification.useful, POYItemLocationType.BIRDSEED),
    ItemData("Eldenhorn: Bird Seed", 3, ItemClassification.useful, POYItemLocationType.BIRDSEED),
    ItemData("Ymir's Shadow: Bird Seed", 4, ItemClassification.useful, POYItemLocationType.BIRDSEED),

    # Extra items
    ItemData("Extra Rope", 0, ItemClassification.filler, POYItemLocationType.EXTRA, min_count=21, max_count=99999999),
    # 21 extra ropes adds up to 42 total ropes, which is the normal max
    ItemData("Extra Chalk", 1, ItemClassification.filler, POYItemLocationType.EXTRA, min_count=3, max_count=99999999),
    ItemData("Extra Coffee", 2, ItemClassification.filler, POYItemLocationType.EXTRA, min_count=3, max_count=99999999),
    ItemData("Extra Seed", 3, ItemClassification.filler, POYItemLocationType.EXTRA, min_count=0, max_count=99999999),
    ItemData("Trap", 4, ItemClassification.filler, POYItemLocationType.EXTRA, min_count=0, max_count=99999999),

    # DLC Items
    ItemData("Alps Ticket", 14, ItemClassification.progression, POYItemLocationType.TOOL, min_count=0),

    # DLC Artefacts
    ItemData("Crimps Idol #1", 20, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Crimps Idol #2", 21, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Slopers Idol #1", 22, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Slopers Idol #2", 23, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Feathers Idol #1", 24, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Feathers Idol #2", 25, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Pitches Idol #1", 26, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Pitches Idol #2", 27, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Ice Idol #1", 28, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Ice Idol #2", 29, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Pinches Idol #1", 30, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Pinches Idol #2", 31, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Greater Balance Idol #1", 32, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Greater Balance Idol #2", 33, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Sundown Idol #1", 34, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Sundown Idol #2", 35, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Seeds Idol #1", 36, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Seeds Idol #2", 37, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Gravity Idol #1", 38, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Gravity Idol #2", 39, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),

    ItemData("Gentiana #1", 40, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Gentiana #2", 41, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Gentiana #3", 42, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Gentiana #4", 43, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Gentiana #5", 44, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Gentiana #6", 45, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Gentiana #7", 46, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),

    ItemData("Edelweiss #1", 47, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Edelweiss #2", 48, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Edelweiss #3", 49, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Edelweiss #4", 50, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Edelweiss #5", 51, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Edelweiss #6", 52, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),
    ItemData("Edelweiss #7", 53, ItemClassification.filler, POYItemLocationType.ARTEFACT, is_enabled=dlc_enabled),

    # DLC Books
    ItemData("Essentials Book", 4, ItemClassification.progression, POYItemLocationType.BOOK,
             min_count=0, is_enabled=dlc_enabled),
    ItemData("Alpine Greats Book", 5, ItemClassification.progression, POYItemLocationType.BOOK,
             min_count=0, is_enabled=dlc_enabled),
    ItemData("Arduous & Arctic Book", 6, ItemClassification.progression, POYItemLocationType.BOOK,
             min_count=0, is_enabled=dlc_enabled),

    #DLC Peaks
    ItemData("Tutor's Tower", 37, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Stougr Boulder", 38, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Mara's Arch", 39, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Grainne Spire", 40, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Great Bók Tree", 41, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Treppenwald", 42, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Castle of the Swan King", 43, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Seaside Tribune", 44, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Ivory Granites", 45, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Old Rekkja", 46, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Quietude", 47, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Eljun's Folly", 48, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Einvald Falls", 49, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Almáttr Dam", 50, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Dunderhorn", 51, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Mhòr Druim", 52, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Welkin Pass", 53, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Seigr Craeg", 54, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Ullr's Chasm", 55, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Great Silf", 56, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Towering Visír", 57, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Eldris Wall", 58, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),
    ItemData("Mount Mhòrgorm", 59, ItemClassification.progression, POYItemLocationType.PEAK, min_count = 0, is_enabled=dlc_enabled),

]

item_name_to_id: dict[str, int] = {i.name: i.id + i.type for i in all_items}

item_id_to_classification: dict[int, ItemClassification] = {i.id + i.type: i.classification for i in all_items}

# poy_regions defines all the regions, their entry requirements, locations and requirements to be included
poy_regions: POYRegion = POYRegion("Peaks of Yore", subregions=[
    POYRegion("Base Game", subregions=[
        BookRegion("Fundamentals", subregions=[
            PeakRegion("Greenhorn's Top", 0),
            PeakRegion("Paltry Peak", 1),
            PeakRegion("Old Mill", 2, locations=[
                LocationData("Old Mill: Hat", POYItemLocationType.ARTEFACT, 0)
            ]),
            PeakRegion("Gray Gully", 3, locations=[
                LocationData("Gray Gully: Picture Piece #1", POYItemLocationType.ARTEFACT, 14),
            ]),
            PeakRegion("Lighthouse", 4),
            PeakRegion("Old Man Of Sjór", 5, locations=[
                LocationData("Old Man Of Sjór: Climbing Shoe", POYItemLocationType.ARTEFACT, 3),
                LocationData("Old Man Of Sjór: Rope: Rope", POYItemLocationType.ROPE, 4)
            ]),
            PeakRegion("Giant's Shelf", 6, locations=[
                LocationData("Giant's Shelf: Sleeping Bag", POYItemLocationType.ARTEFACT, 5),
            ]),
            PeakRegion("Evergreen's End", 7, locations=[
                LocationData("Evergreen's End: Fisherman's Cap", POYItemLocationType.ARTEFACT, 1),
                LocationData("Evergreen's End: Rope", POYItemLocationType.ROPE, 13),
            ]),
            PeakRegion("The Twins", 8),
            PeakRegion("Old Grove's Skelf", 9, locations=[
                LocationData("Old Grove's Skelf: Safety Helmet", POYItemLocationType.ARTEFACT, 2)
            ]),
            PeakRegion("Land's End", 10, locations=[
                LocationData("Land's End: Picture Piece #2", POYItemLocationType.ARTEFACT, 15),
                LocationData("Land's End: Rope", POYItemLocationType.ROPE, 12),
            ]),
            PeakRegion("Hangman's Leap", 11, locations=[
                LocationData("Hangman's Leap: Rope", POYItemLocationType.ROPE, 5),
                LocationData("Walker Interaction Event", POYItemLocationType.EXTRA, 0, is_event=True),
            ]),
            PeakRegion("Old Langr", 12, locations=[
                LocationData("Old Langr: Coffee Box", POYItemLocationType.ARTEFACT, 7),
            ]),
            PeakRegion("Aldr Grotto", 13, entry_requirements=SimpleRequirements({"Oil Lamp": 1}), locations=[
                LocationData("Aldr Grotto: Backpack", POYItemLocationType.ARTEFACT, 6),
            ]),
            PeakRegion("Three Brothers", 14, locations=[
                LocationData("Three Brothers: Shovel", POYItemLocationType.ARTEFACT, 4),
                LocationData("Three Brothers: Bird Seed", POYItemLocationType.BIRDSEED, 0),
            ]),
            PeakRegion("Walter's Crag", 15, locations=[
                LocationData("Walter's Crag: Fundamentals Trophy", POYItemLocationType.ARTEFACT, 19),
                LocationData("Walter's Crag: Rope (Co-Climb)", POYItemLocationType.ROPE, 0),
                LocationData("Walter's Crag: Rope", POYItemLocationType.ROPE, 11),
            ]),
            PeakRegion("The Great Crevice", 16, locations=[
                LocationData("The Great Crevice: Picture Piece #3", POYItemLocationType.ARTEFACT, 16),
                LocationData("The Great Crevice: Rope", POYItemLocationType.ROPE, 14),
            ],entry_requirements=LeveledRequirements(RequirementsDifficulty.option_easy, SimpleRequirements({"Progressive Crampons": 1})),
            ),
            PeakRegion("Old Hagger", 17, locations=[
                LocationData("Old Hagger: Rope", POYItemLocationType.ROPE, 15),
            ],entry_requirements=LeveledRequirements(RequirementsDifficulty.option_easy, SimpleRequirements({"Progressive Crampons": 1})),
            ),
            PeakRegion("Ugsome Storr", 18, locations=[
                LocationData("Ugsome Storr: Rope", POYItemLocationType.ROPE, 6),
            ],entry_requirements=LeveledRequirements(RequirementsDifficulty.option_easy, SimpleRequirements({"Progressive Crampons": 1})),
            ),
            PeakRegion("Wuthering Crest", 19, locations=[
                LocationData("Wuthering Crest: Coffee Box", POYItemLocationType.ARTEFACT, 8),
                LocationData("Wuthering Crest: Rope", POYItemLocationType.ROPE, 9),
            ],entry_requirements=LeveledRequirements(RequirementsDifficulty.option_easy, SimpleRequirements({"Progressive Crampons": 1})),
            ),
        ], enable_requirements=lambda options: options.enable_fundamental),
        BookRegion("Intermediate", subregions=[
            PeakRegion("Porter's Boulder", 20),
            PeakRegion("Jotunn's Thumb", 21),
            PeakRegion("Old Skerry", 22, locations=[
                LocationData("Old Skerry: Bird Seed", POYItemLocationType.BIRDSEED, 1),
            ]),
            PeakRegion("Hamarr Stone", 23),
            PeakRegion("Giant's Nose", 24),
            PeakRegion("Walter's Boulder", 25),
            PeakRegion("Sundered Sons", 26),
            PeakRegion("Old Weald's Boulder", 27),
            PeakRegion("Leaning Spire", 28, locations=[
                LocationData("Leaning Spire: Intermediate Trophy", POYItemLocationType.ARTEFACT, 11),
            ]),
            PeakRegion("Cromlech", 29),
        ], enable_requirements=lambda options: options.enable_intermediate),
        BookRegion("Advanced", entry_requirements=LeveledRequirements(RequirementsDifficulty.option_easy, SimpleRequirements({"Progressive Crampons": 1})), subregions=[
            PeakRegion("Walker's Pillar", 30, locations=[
                LocationData("Walker's Pillar: Chalk Box", POYItemLocationType.ARTEFACT, 9),
                LocationData("Walker's Pillar: Rope (Co-Climb)", POYItemLocationType.ROPE, 1,
                             requirements=SimpleRequirements({"Walker Interaction Event": 1}),
                             enable_override= lambda options: options.enable_fundamental),
            ], generate_free_solo=True),
            PeakRegion("Eldenhorn", 31, locations=[
                LocationData("Eldenhorn: Chalk Box", POYItemLocationType.ARTEFACT, 10),
                LocationData("Eldenhorn: Rope", POYItemLocationType.ROPE, 7),
                LocationData("Eldenhorn: Bird Seed", POYItemLocationType.BIRDSEED, 3),
            ], generate_free_solo=True),
            PeakRegion("Great Gaol", 32, locations=[
                LocationData("Great Gaol: Picture Frame", POYItemLocationType.ARTEFACT, 18,
                             requirements=ConditionalRequirements(SimpleRequirements({"Progressive Crampons": 2}),
                                                                  lambda opts: opts.requirements_difficulty != RequirementsDifficulty.option_free_solo)),
                LocationData("Great Gaol: Rope (Encounter)", POYItemLocationType.ROPE, 2),
                LocationData("Great Gaol: Rope", POYItemLocationType.ROPE, 10),
                LocationData("Great Gaol: Bird Seed", POYItemLocationType.BIRDSEED, 2),
            ], generate_free_solo=True),
            PeakRegion("St. Haelga", 33, locations=[
                LocationData("St. Haelga: Rope (Encounter)", POYItemLocationType.ROPE, 3),
                LocationData("St. Haelga: Picture Piece #4", POYItemLocationType.ARTEFACT, 17),
            ], generate_free_solo=True),
            PeakRegion("Ymir's Shadow", 34, locations=[
                LocationData("Ymir's Shadow: Advanced Trophy", POYItemLocationType.ARTEFACT, 12,
                             requirements=ConditionalRequirements(SimpleRequirements({"Progressive Crampons": 2}),
                                          lambda opts: opts.requirements_difficulty != RequirementsDifficulty.option_free_solo)
                             ),
                LocationData("Ymir's Shadow: Rope", POYItemLocationType.ROPE, 8),
                LocationData("Ymir's Shadow: Bird Seed", POYItemLocationType.BIRDSEED, 4),
            ], generate_free_solo=True),
        ], enable_requirements=lambda options: options.enable_advanced),
        BookRegion("Expert", "Northern Range Ticket", entry_requirements=(
                SimpleRequirements({"Ice Axes": 1}) &
                ConditionalRequirements(SimpleRequirements({"Progressive Crampons": 1}), lambda opts: opts.requirements_difficulty != RequirementsDifficulty.option_free_solo) &
                LeveledRequirements(RequirementsDifficulty.option_easy, SimpleRequirements({"Pipe": 1}))
        ), subregions=[
            PeakRegion("The Great Bulwark", 35, locations=[
                LocationData("The Great Bulwark: Expert Trophy", POYItemLocationType.ARTEFACT, 13),
            ], generate_time_attack=False, generate_free_solo=True),
            PeakRegion("Solemn Tempest", 36, entry_requirements=ConditionalRequirements(SimpleRequirements({"Progressive Crampons": 2}), lambda opts: opts.requirements_difficulty != RequirementsDifficulty.option_free_solo),
                       enable_requirements=lambda options: not options.disable_solemn_tempest, generate_time_attack=False,
                       generate_free_solo=True),
        ], enable_requirements=lambda options: options.enable_expert),
    ]),
    POYRegion("DLC", entry_requirements={"Alps Ticket": 1}, subregions=[
        BookRegion("Essentials", subregions=[
            PeakRegion("Tutor's Tower", 37),
            PeakRegion("Stougr Boulder", 38),
            PeakRegion("Mara's Arch", 39, locations=[
                LocationData("Mara's Arch: Gentiana #1", POYItemLocationType.ARTEFACT, 40),
            ]),
            PeakRegion("Grainne Spire", 40, locations=[
                LocationData("Grainne Spire: Crimps Idol #1", POYItemLocationType.ARTEFACT, 20),
            ]),
            PeakRegion("Great Bók Tree", 41, locations=[
                LocationData("Great Bók Tree: Edelweiss #2", POYItemLocationType.ARTEFACT, 48),
                LocationData("Great Bók Tree: Crimps Idol #2", POYItemLocationType.ARTEFACT, 21),
            ]),
            PeakRegion("Treppenwald", 42, locations=[
                LocationData("Treppenwald: Gentiana #2", POYItemLocationType.ARTEFACT, 41),
                LocationData("Treppenwald: Seeds Idol #1", POYItemLocationType.ARTEFACT, 36),
            ]),
            PeakRegion("Castle of the Swan King", 43, locations=[
                LocationData("Castle of the Swan King: Edelweiss #3", POYItemLocationType.ARTEFACT, 49),
                LocationData("Castle of the Swan King: Slopers Idol #1", POYItemLocationType.ARTEFACT, 22),
                LocationData("Castle of the Swan King: Sundown Idol #1", POYItemLocationType.ARTEFACT, 34),
                LocationData("Castle of the Swan King: Pitches Idol #1", POYItemLocationType.ARTEFACT, 26),
            ]),
            PeakRegion("Seaside Tribune", 44, locations=[
                LocationData("Seaside Tribune: Pinches Idol #2", POYItemLocationType.ARTEFACT, 31),
            ]),
            PeakRegion("Ivory Granites", 45, locations=[
                LocationData("Ivory Granites: Edelweiss #4", POYItemLocationType.ARTEFACT, 50),
                LocationData("Ivory Granites: Gravity Idol #2", POYItemLocationType.ARTEFACT, 39),
            ]),
            PeakRegion("Old Rekkja", 46, locations=[
                LocationData("Old Rekkja: Slopers Idol #2", POYItemLocationType.ARTEFACT, 23),
            ]),
            PeakRegion("Quietude", 47, locations=[
                LocationData("Quietude: Gentiana #4", POYItemLocationType.ARTEFACT, 43),
            ]),
            PeakRegion("Eljun's Folly", 48, locations=[
                LocationData("Eljun's Folly: Gentiana #3", POYItemLocationType.ARTEFACT, 42),
                LocationData("Eljun's Folly: Pitches Idol #2", POYItemLocationType.ARTEFACT, 27),
            ]),
        ], enable_requirements=lambda options: options.enable_essentials),
        BookRegion("Alpine Greats", subregions=[
            PeakRegion("Einvald Falls", 49, locations=[
                LocationData("Eivald Falls: Gentiana #5", POYItemLocationType.ARTEFACT, 44),
            ]),
            PeakRegion("Almáttr Dam", 50),
            PeakRegion("Dunderhorn", 51, locations=[
                LocationData("Dunderhorn: Edelweiss #7", POYItemLocationType.ARTEFACT, 53),
                LocationData("Dunderhorn: Sundown Idol #2", POYItemLocationType.ARTEFACT, 35),
            ]),
            PeakRegion("Mhòr Druim", 52, locations=[
                LocationData("Mhòr Druim: Ice Idol #1", POYItemLocationType.ARTEFACT, 28),
                LocationData("Mhòr Druim: Feathers Idol #1", POYItemLocationType.ARTEFACT, 24),
                LocationData("Mhòr Druim: Gentiana #6", POYItemLocationType.ARTEFACT, 45),
            ]),
            PeakRegion("Welkin Pass", 53, locations=[
                LocationData("Welkin Pass: Edeweiss #6", POYItemLocationType.ARTEFACT, 52),
                LocationData("Welkin Pass: Feathers Idol #2", POYItemLocationType.ARTEFACT, 25),
            ])
        ], enable_requirements=lambda options: options.enable_alpine_greats),
        BookRegion("Arduous & Arctic", entry_requirements={"Ice Axes": 1}, subregions=[
            PeakRegion("Seigr Craeg", 54,
                       generate_free_solo=True),
            PeakRegion("Ullr's Chasm", 55, locations=[
                LocationData("Ullr's Chasm: Greater Balance Idol #2", POYItemLocationType.ARTEFACT, 33),
            ], generate_free_solo=True),
            PeakRegion("Great Silf", 56, generate_free_solo=True),
            PeakRegion("Towering Visír", 57, locations=[
                LocationData("Towering Visír: Greater Balance Idol #1", POYItemLocationType.ARTEFACT, 32),
                LocationData("Towering Visír: Gentiana #7", POYItemLocationType.ARTEFACT, 46),
                LocationData("Towering Visír: Edelweiss #1", POYItemLocationType.ARTEFACT, 47),
                LocationData("Towering Visír: Pinches Idol #1", POYItemLocationType.ARTEFACT, 30),

            ], generate_free_solo=True),
            PeakRegion("Eldris Wall", 58, locations=[
                LocationData("Eldris Wall: Ice Idol #2", POYItemLocationType.ARTEFACT, 29),
                LocationData("Eldris Wall: Edelweiss #5", POYItemLocationType.ARTEFACT, 51),
                LocationData("Eldris Wall: Seeds Idol #2", POYItemLocationType.ARTEFACT, 37),
            ], generate_free_solo=True),
            PeakRegion("Mount Mhòrgorm", 59, locations=[
                LocationData("Mount Mhòrgorm: Gravity Idol #1", POYItemLocationType.ARTEFACT, 38),
            ], generate_free_solo=True),
        ], enable_requirements=lambda options: options.enable_arduous_arctic),
    ], enable_requirements=lambda options: options.enable_dlc,),
])
all_locations_to_ids: dict[str, int] = poy_regions.get_all_locations_dict()
ids_to_locations: dict[int, str] = {v: k for k, v in all_locations_to_ids.items()}