"""Apply Patch data to the ROM."""
import codecs
import json
import pickle
import random

import js

from randomizer.DKTV import randomize_dktv
from randomizer.EntranceRando import randomize_entrances
from randomizer.Enums.Transitions import Transitions
from randomizer.KRoolRando import randomize_krool
from randomizer.MoveLocationRando import randomize_moves
from randomizer.MusicRando import randomize_music
from randomizer.Patcher import ROM
from randomizer.PriceRando import randomize_prices
from randomizer.BossRando import randomize_bosses
from randomizer.BarrelRando import randomize_barrels
from randomizer.BananaPortRando import randomize_bananaport

# from randomizer.Spoiler import Spoiler
from randomizer.Settings import Settings
from ui.progress_bar import ProgressBar


def patching_response(responded_data):
    """Response data from the background task.

    Args:
        responded_data (str): Pickled data (or json)
    """
    try:
        loaded_data = json.loads(responded_data)
        if loaded_data.get("error"):
            error = loaded_data.get("error")
            ProgressBar().set_class("bg-danger")
            ProgressBar().update_progress(10, f"Error: {error}")
            ProgressBar().reset()
            return None
    except Exception:
        pass

    ProgressBar().update_progress(5, "Applying Patches")
    # spoiler: Spoiler = pickle.loads(codecs.decode(responded_data.encode(), "base64"))
    spoiler = pickle.loads(codecs.decode(responded_data.encode(), "base64"))
    spoiler.settings.verify_hash()
    Settings({"seed": 0}).compare_hash(spoiler.settings.public_hash)
    # Make sure we re-load the seed id
    spoiler.settings.set_seed()
    if spoiler.settings.download_patch_file:
        spoiler.settings.download_patch_file = False

        js.save_text_as_file(codecs.encode(pickle.dumps(spoiler), "base64").decode(), f"dk64-{spoiler.settings.seed_id}.lanky")
    # Starting index for our settings
    sav = 0x1FED020

    # Shuffle Levels
    if spoiler.settings.shuffle_levels:
        ROM().seek(sav + 0x000)
        ROM().write(1)

        # Update Level Order
        vanilla_lobby_entrance_order = [
            Transitions.IslesMainToJapesLobby,
            Transitions.IslesMainToAztecLobby,
            Transitions.IslesMainToFactoryLobby,
            Transitions.IslesMainToGalleonLobby,
            Transitions.IslesMainToForestLobby,
            Transitions.IslesMainToCavesLobby,
            Transitions.IslesMainToCastleLobby,
        ]
        vanilla_lobby_exit_order = [
            Transitions.IslesJapesLobbyToMain,
            Transitions.IslesAztecLobbyToMain,
            Transitions.IslesFactoryLobbyToMain,
            Transitions.IslesGalleonLobbyToMain,
            Transitions.IslesForestLobbyToMain,
            Transitions.IslesCavesLobbyToMain,
            Transitions.IslesCastleLobbyToMain,
        ]
        order = 0
        for level in vanilla_lobby_entrance_order:
            ROM().seek(sav + 0x001 + order)
            ROM().write(vanilla_lobby_exit_order.index(spoiler.shuffled_exit_data[int(level)].reverse))
            order += 1

        # Key Order
        map_pointers = {
            Transitions.IslesMainToJapesLobby: Transitions.IslesJapesLobbyToMain,
            Transitions.IslesMainToAztecLobby: Transitions.IslesAztecLobbyToMain,
            Transitions.IslesMainToFactoryLobby: Transitions.IslesFactoryLobbyToMain,
            Transitions.IslesMainToGalleonLobby: Transitions.IslesGalleonLobbyToMain,
            Transitions.IslesMainToForestLobby: Transitions.IslesForestLobbyToMain,
            Transitions.IslesMainToCavesLobby: Transitions.IslesCavesLobbyToMain,
            Transitions.IslesMainToCastleLobby: Transitions.IslesCastleLobbyToMain,
        }
        key_mapping = {
            # key given in each level. (Item 1 is Japes etc. flags=[0x1A,0x4A,0x8A,0xA8,0xEC,0x124,0x13D] <- Item 1 of this array is Key 1 etc.)
            Transitions.IslesJapesLobbyToMain: 0x1A,
            Transitions.IslesAztecLobbyToMain: 0x4A,
            Transitions.IslesFactoryLobbyToMain: 0x8A,
            Transitions.IslesGalleonLobbyToMain: 0xA8,
            Transitions.IslesForestLobbyToMain: 0xEC,
            Transitions.IslesCavesLobbyToMain: 0x124,
            Transitions.IslesCastleLobbyToMain: 0x13D,
        }
        order = 0
        for key, value in map_pointers.items():
            new_world = spoiler.shuffled_exit_data.get(key).reverse
            ROM().seek(sav + 0x01E + order)
            ROM().writeMultipleBytes(key_mapping[int(new_world)], 2)
            order += 2

    # Color Banana Requirements
    order = 0
    for count in spoiler.settings.BossBananas:
        ROM().seek(sav + 0x008 + order)
        ROM().writeMultipleBytes(count, 2)
        order += 2

    # Golden Banana Requirements
    order = 0
    for count in spoiler.settings.EntryGBs:
        ROM().seek(sav + 0x016 + order)
        ROM().writeMultipleBytes(count, 1)
        order += 1

    # Unlock All Kongs
    if spoiler.settings.unlock_all_kongs:
        ROM().seek(sav + 0x02C)
        ROM().write(1)

    # Unlock All Moves
    if spoiler.settings.unlock_all_moves:
        ROM().seek(sav + 0x02D)
        ROM().write(1)

    # Fast Start game
    if spoiler.settings.fast_start_beginning_of_game:
        ROM().seek(sav + 0x02E)
        ROM().write(1)

    # Unlock Shockwave
    if spoiler.settings.unlock_fairy_shockwave:
        ROM().seek(sav + 0x02F)
        ROM().write(1)

    # Enable Tag Anywhere
    if spoiler.settings.enable_tag_anywhere:
        ROM().seek(sav + 0x030)
        ROM().write(1)

    # Fast Hideout
    if spoiler.settings.fast_start_hideout_helm:
        ROM().seek(sav + 0x031)
        ROM().write(1)

    # Crown Door Open
    if spoiler.settings.crown_door_open:
        ROM().seek(sav + 0x032)
        ROM().write(1)

    # Coin Door Open
    if spoiler.settings.coin_door_open:
        ROM().seek(sav + 0x033)
        ROM().write(1)

    # Quality of Life
    if spoiler.settings.quality_of_life:
        ROM().seek(sav + 0x034)
        ROM().write(1)

    # Damage amount
    ROM().seek(sav + 0x0A5)
    if spoiler.settings.damage_amount != "default":
        if spoiler.settings.damage_amount == "double":
            ROM().write(2)
        elif spoiler.settings.damage_amount == "ohko":
            ROM().write(12)
        elif spoiler.settings.damage_amount == "quad":
            ROM().write(4)
    else:
        ROM().write(1)

    # Disable healing
    if spoiler.settings.no_healing:
        ROM().seek(sav + 0x0A6)
        ROM().write(1)

    # Disable melon drops
    if spoiler.settings.no_melons:
        ROM().seek(sav + 0x119)
        ROM().write(1)

    # Auto complete bonus barrels
    if spoiler.settings.bonus_barrel_auto_complete:
        ROM().seek(sav + 0x117)
        ROM().write(3)

    # Enable or disable the warp to isles option in the UI
    if spoiler.settings.warp_to_isles:
        ROM().seek(sav + 0x125)
        ROM().write(1)

    # Enables the counter for the shop indications
    if spoiler.settings.shop_indicator:
        ROM().seek(sav + 0x124)
        ROM().write(1)

    # Currently crashing most of the time
    # randomize_dktv(spoiler)
    randomize_music(spoiler)
    randomize_entrances(spoiler)
    randomize_moves(spoiler)
    randomize_prices(spoiler)
    randomize_bosses(spoiler)
    randomize_krool(spoiler)
    randomize_barrels(spoiler)
    randomize_bananaport(spoiler)

    # Apply Hash
    hash_images = [random.randint(0, 9) for i in range(5)]
    order = 0
    for count in hash_images:
        ROM().seek(sav + 0x11A + order)
        ROM().write(count)
        order += 1

    ProgressBar().update_progress(10, "Seed Generated.")
    if spoiler.settings.generate_spoilerlog is True:
        js.document.getElementById("nav-spoiler-tab").style.display = ""
        js.document.getElementById("spoiler_log_text").value = spoiler.toJson()
        js.save_text_as_file(spoiler.toJson(), f"dk64-{spoiler.settings.seed_id}-spoiler-log.json")
    else:
        js.document.getElementById("nav-spoiler-tab").style.display = "none"
        js.document.getElementById("spoiler_log_text").value = ""
    ROM().fixSecurityValue()
    ROM().save(f"dk64-{spoiler.settings.seed_id}.z64")
    ProgressBar().reset()
