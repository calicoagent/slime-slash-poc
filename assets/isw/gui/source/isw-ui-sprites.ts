// Real icon art for the UI kit.
//
// The PNGs in `assets/icons/` are cut from the shared icon sheets by
// `scripts/extract-ui-icons.py` — the sheets themselves live on the shared
// NAS volume, not in this repository, so the script is the provenance. This
// file is the id -> sprite table; re-run the script and edit the table
// together when a sheet changes.
//
// Items draw from the keys sheet: every `item.*` id points at one key, so a
// full inventory reads as distinct objects rather than repeated glyphs.

const FILES = import.meta.glob('./assets/icons/*.png', {
  eager: true,
  query: '?url',
  import: 'default',
}) as Record<string, string>;

// Single top-level crops (not cut from the shared sheets by
// `scripts/extract-ui-icons.py`): the rebirth egg is cropped from the egg
// sheet's row 2 col 2 blue striped cell at
// `packages/isw-ui/src/assets/rebirth-egg-blue.png`. Same `?url` mechanism,
// separate glob so the icons/ provenance comment above stays exact.
const TOP_FILES = import.meta.glob('./assets/*.png', {
  eager: true,
  query: '?url',
  import: 'default',
}) as Record<string, string>;

export const SPRITES: Record<string, string> = {
  // slime skills (content/skills.json)
  'skill.tidal_lash': 'wave',
  'skill.deep_mending': 'wave_heal',
  'skill.ember_burst': 'fire_burst',
  'skill.mend': 'mend_leaf',
  'skill.venom_sting': 'venom_slash',
  'skill.gunk_toss': 'gunk',
  // tamer skills (content/tamer_skills.json)
  'skill.fishing': 'fishing_rod',
  'skill.bond': 'heart_bandage',
  'skill.first_aid': 'bandage',
  'skill.hunters_instinct': 'eye_inspect',
  'skill.long_leash': 'leash',
  'skill.soft_step': 'boots_wind',
  'skill.chef': 'chef_hat',
  'skill.drill': 'drill_post',
  'skill.reserve': 'hourglass',
  'skill.composure': 'moon',
  'skill.keeper': 'shield_wood',
  'skill.focus': 'eye_mark',
  'skill.beckon': 'paw_blue',
  'skill.lure': 'hook',
  // #537: existing coin art until a vending sheet is generated.
  'skill.vending': 'coin_gold',
  // items, all from the keys sheet
  'item.weapon': 'key_000',
  'item.armor': 'key_009',
  'item.accessory': 'key_018',
  'item.consumable': 'key_027',
  'item.poultice': 'key_036',
  'item.dew': 'key_045',
  'item.loot': 'key_054',
  'item.scale': 'key_063',
  'item.shell': 'key_072',
  'item.wing': 'key_081',
  'item.fibre': 'key_090',
  'item.food': 'key_099',
  'item.fish': 'key_004',
  'item.egg': 'key_013',
  'item.mushroom': 'key_022',
  'item.coin': 'key_031',
  // generated item/fishing icons (~/scratchpad/icons-out/, 2026-09-24):
  // one real sprite per content/items.json id, replacing the generic
  // key_* art above for these specific ids. File name equals the id.
  'item.worn_fang': 'worn_fang',
  'item.cave_fang_blade': 'cave_fang_blade',
  'item.hide_barding': 'hide_barding',
  'item.wolf_tooth_charm': 'wolf_tooth_charm',
  'item.hatchling_shell': 'hatchling_shell',
  'item.bog_reed_stave': 'bog_reed_stave',
  'item.oracle_wrap': 'oracle_wrap',
  'item.barrow_maul': 'barrow_maul',
  'item.sentinel_plate': 'sentinel_plate',
  'item.titan_cleaver': 'titan_cleaver',
  'item.deeps_carapace': 'deeps_carapace',
  // gear expansion (Handler ruling 2026-09-27): one generated icon per item
  'item.driftwood_cudgel': 'driftwood_cudgel',
  'item.patched_canvas_vest': 'patched_canvas_vest',
  'item.twine_luck_knot': 'twine_luck_knot',
  'item.fieldhand_sickle': 'fieldhand_sickle',
  'item.quilted_jerkin': 'quilted_jerkin',
  'item.copper_band': 'copper_band',
  'item.lakeside_hatchet': 'lakeside_hatchet',
  'item.boiled_leather_coat': 'boiled_leather_coat',
  'item.brass_compass_charm': 'brass_compass_charm',
  'item.salvage_spear': 'salvage_spear',
  'item.studded_hide_vest': 'studded_hide_vest',
  'item.tin_whistle_pendant': 'tin_whistle_pendant',
  'item.forged_longknife': 'forged_longknife',
  'item.ringmail_shirt': 'ringmail_shirt',
  'item.silver_bead_bracelet': 'silver_bead_bracelet',
  'item.tempered_warpick': 'tempered_warpick',
  'item.scaled_brigandine': 'scaled_brigandine',
  'item.garnet_signet': 'garnet_signet',
  'item.steel_broadsword': 'steel_broadsword',
  'item.banded_cuirass': 'banded_cuirass',
  'item.moonstone_amulet': 'moonstone_amulet',
  'item.wayfarers_brooch': 'wayfarers_brooch',
  'item.deepwater_pearl_torc': 'deepwater_pearl_torc',
  'item.mite_mandible_dirk': 'mite_mandible_dirk',
  'item.mite_chitin_vest': 'mite_chitin_vest',
  'item.dustmote_bead': 'dustmote_bead',
  'item.chirrup_reed_whip': 'chirrup_reed_whip',
  'item.hopper_wing_cape': 'hopper_wing_cape',
  'item.cricket_song_charm': 'cricket_song_charm',
  'item.sproutwood_club': 'sproutwood_club',
  'item.leafweave_tunic': 'leafweave_tunic',
  'item.seedpod_locket': 'seedpod_locket',
  'item.gelskin_mace': 'gelskin_mace',
  'item.gelskin_wrap': 'gelskin_wrap',
  'item.wobble_bell': 'wobble_bell',
  'item.bracken_scythe': 'bracken_scythe',
  'item.frondmail_coat': 'frondmail_coat',
  'item.curled_fern_ring': 'curled_fern_ring',
  'item.hooting_gale_staff': 'hooting_gale_staff',
  'item.owl_down_mantle': 'owl_down_mantle',
  'item.night_eye_talisman': 'night_eye_talisman',
  'item.dawnfeather_wand': 'dawnfeather_wand',
  'item.bogwater_trident': 'bogwater_trident',
  'item.toadhide_jerkin': 'toadhide_jerkin',
  'item.peat_pearl_earring': 'peat_pearl_earring',
  'item.croaking_spring_rod': 'croaking_spring_rod',
  'item.adder_fang_stiletto': 'adder_fang_stiletto',
  'item.heatherscale_vest': 'heatherscale_vest',
  'item.coiled_adder_bangle': 'coiled_adder_bangle',
  'item.venom_briar_whip': 'venom_briar_whip',
  'item.briarback_shell_hammer': 'briarback_shell_hammer',
  'item.tortoise_plate_cuirass': 'tortoise_plate_cuirass',
  'item.thornback_ring': 'thornback_ring',
  'item.tusk_pike': 'tusk_pike',
  'item.bramblehide_barding': 'bramblehide_barding',
  'item.boar_bristle_charm': 'boar_bristle_charm',
  'item.gloomwing_sickle': 'gloomwing_sickle',
  'item.dusk_moth_shawl': 'dusk_moth_shawl',
  'item.moth_eye_pendant': 'moth_eye_pendant',
  'item.umbral_dust_wand': 'umbral_dust_wand',
  'item.mossfang_sabre': 'mossfang_sabre',
  'item.mossy_wolfpelt': 'mossy_wolfpelt',
  'item.mossfang_tooth_necklace': 'mossfang_tooth_necklace',
  'item.scaldshell_axe': 'scaldshell_axe',
  'item.beetle_carapace_mail': 'beetle_carapace_mail',
  'item.cinder_beetle_brooch': 'cinder_beetle_brooch',
  'item.brimstone_horn_maul': 'brimstone_horn_maul',
  'item.ramfleece_coat': 'ramfleece_coat',
  'item.sulphur_crystal_ring': 'sulphur_crystal_ring',
  'item.kindlewing_dagger': 'kindlewing_dagger',
  'item.batwing_cloak': 'batwing_cloak',
  'item.ember_fang_earring': 'ember_fang_earring',
  'item.wispflame_rod': 'wispflame_rod',
  'item.ashen_robe': 'ashen_robe',
  'item.wisp_lantern_charm': 'wisp_lantern_charm',
  'item.cinderfell_glaive': 'cinderfell_glaive',
  'item.nightfang_claymore': 'nightfang_claymore',
  'item.cave_wolf_mantle': 'cave_wolf_mantle',
  'item.howling_moon_charm': 'howling_moon_charm',
  'item.duskhowl_knife': 'duskhowl_knife',
  'item.granite_warhammer': 'granite_warhammer',
  'item.sentinel_stone_aegis': 'sentinel_stone_aegis',
  'item.runestone_signet': 'runestone_signet',
  'item.quarry_pick': 'quarry_pick',
  'item.tidebreaker_lance': 'tidebreaker_lance',
  'item.bulwark_shell_plate': 'bulwark_shell_plate',
  'item.pearl_current_charm': 'pearl_current_charm',
  'item.flitterwing_blade': 'flitterwing_blade',
  'item.twilight_silk_vest': 'twilight_silk_vest',
  'item.dusk_flitter_pin': 'dusk_flitter_pin',
  'item.eclipse_chakram': 'eclipse_chakram',
  'item.miasma_staff': 'miasma_staff',
  'item.oracle_bogweave_robe': 'oracle_bogweave_robe',
  'item.oracles_eye_amulet': 'oracles_eye_amulet',
  'item.spirit_totem_staff': 'spirit_totem_staff',
  'item.shaman_feather_mantle': 'shaman_feather_mantle',
  'item.wailing_charm': 'wailing_charm',
  'item.spiritward_censer': 'spiritward_censer',
  'item.titanbone_greatsword': 'titanbone_greatsword',
  'item.mire_titan_hauberk': 'mire_titan_hauberk',
  'item.grave_mire_seal': 'grave_mire_seal',
  'item.sunken_reliquary_blade': 'sunken_reliquary_blade',
  'item.prismatic_scale': 'prismatic_scale',
  'item.mite_shell': 'mite_shell',
  'item.moth_wing': 'moth_wing',
  'item.sprout_fibre': 'sprout_fibre',
  'item.minor_poultice': 'minor_poultice',
  // shop / NPC mock S3: Medium Poultice draws as potion_red
  'item.medium_poultice': 'potion_red',
  'item.spirit_dew': 'spirit_dew',
  'item.greater_poultice': 'greater_poultice',
  'item.deep_spirit_dew': 'deep_spirit_dew',
  'item.pond_fry': 'pond_fry',
  'item.silver_minnow': 'silver_minnow',
  'item.reed_carp': 'reed_carp',
  'item.amber_perch': 'amber_perch',
  'item.moon_goby': 'moon_goby',
  'item.brook_loach': 'brook_loach',
  'item.slime_chow': 'slime_chow',
  'item.meadow_mash': 'meadow_mash',
  'item.bog_truffle': 'bog_truffle',
  'item.barrow_crumble': 'barrow_crumble',
  'item.deeps_roe': 'deeps_roe',
  // extras with no content/items.json row yet, generated in the same batch
  'item.hatchling_chow': 'hatchling_chow',
  'item.early_access_key': 'early_access_key',
  'item.training_ticket': 'training_ticket',
  // #496: the Rebirth Ticket wears the hourglass (invite mock rungs 2-3)
  'item.rebirth_ticket': 'hourglass',
  // Daily Gift (src/daily-window.ts; daily-login mock a/coin_gold.png, a/sparkle.png)
  'daily.coin': 'coin_gold',
  'daily.new_day': 'sparkle',
  // Invite Friends (src/invite-window.ts; invite mock egg_prism.png): the
  // Prism Egg, egg_039 re-sliced whole at 54 x 64 (the first cut clipped it)
  'invite.egg': 'egg_039',
  // fishing minigame art (src/ui: bag/fishing mock), not inventory items
  'fish.bobber': 'bobber',
  'fish.bobber_dip': 'bobber_dip',
  'fish.nothing_bit': 'nothing_bit',
  // B5 bag / slime window (src/bag-window.ts; fishing-bag mock KINDS, topTabs, coins)
  'bag.slime': 'paw',
  'bag.bag': 'bag_leather',
  'bag.skills': 'sparkle_rainbow',
  'bag.slime_skills': 'drop_blue',
  // Quests tab (#595): the route map, as the defeat window's spawn point
  'bag.quests': 'map_route',
  'skill.hp_recovery': 'heart_red',
  'skill.mp_recovery': 'crystal',
  'bag.all': 'bag_leather',
  'bag.equipment': 'sword',
  'bag.consumable': 'potion_red',
  'bag.food': 'bowl_food',
  'bag.loot': 'shell_green',
  'bag.coin': 'coin_gold',
  // Share card (#541, mock slime-share statChips): ATK, DEF, ASPD, WINS and the sparkles.
  'share.atk': 'sword',
  'share.def': 'shield',
  'share.aspd': 'sparkle',
  'share.wins': 'coin_gold',
  'share.sparkle_rainbow': 'sparkle_rainbow',
  // S3 shop window (src/shop-window.ts; shop-npc mock coin_gold.png)
  'shop.coin': 'coin_gold',
  // D1 defeat window (src/defeat.ts; defeat mock SP icons, coin)
  'defeat.bed': 'bed',
  'defeat.spawn': 'map_route',
  'defeat.coin': 'coin_gold',
  // T4 interaction bubble (src/thought-bubble.ts; interaction-bubble mock ACTS)
  'act.fish': 'fishing_rod',
  'act.talk': 'chat_dots',
  'act.shop': 'coin_gold',
  'act.train': 'drill_post',
  'act.stable': 'stable',
  'act.save': 'crystal',
  'act.exit': 'door',
  // CH4 chat (src/chat-panel.ts, src/chat-log.ts; chat mock IC('chat'), SEED/EVENTS icons)
  'chat.open': 'chat',
  'chat.refused': 'hourglass',
  'pickup.apple': 'apple',
  'pickup.herb': 'herb',
  // menubar (src/ui/menubar.ts)
  'menu.character': 'portrait',
  'menu.bag': 'bag_travel',
  'menu.skills': 'sparkle_rainbow',
  'menu.forms': 'banner',
  'menu.care': 'bowl_food',
  'menu.shop': 'scales',
  'menu.logs': 'chat_plain',
  'menu.settings': 'gear',
  'menu.records': 'compass',
  // Rebirth egg: blue striped crop (row 2 col 2 of the egg sheet), not the
  // grey key_013 item.egg art — the vitals rebirth button draws menu.egg.
  'menu.egg': 'rebirth-egg-blue',
  // buffs (src/ui/buffs.ts)
  'buff.well_fed': 'apple',
  'buff.content': 'heart_red',
  'buff.resting': 'moon',
  'buff.hunting': 'claw',
  'buff.expiring': 'hourglass',
  'buff.debuff': 'hex',
  'buff.guarded': 'shield_wood',
  // B4 effect chips (src/effects.ts; buffs mock chipsHTML/starveCard art)
  'effect.well_fed': 'bowl_food',
  'effect.hungry': 'bowl',
  'effect.starving': 'bowl',
  'effect.resting': 'bed',
  'effect.poison': 'drop',
  'effect.stun': 'hex',
};

export function spriteName(id: string): string | null {
  return SPRITES[id] ?? null;
}

export function spriteUrl(id: string): string | null {
  const name = SPRITES[id];
  if (!name) return null;
  return FILES[`./assets/icons/${name}.png`] ?? TOP_FILES[`./assets/${name}.png`] ?? null;
}

export function spriteIds(): string[] {
  return Object.keys(SPRITES).sort();
}
