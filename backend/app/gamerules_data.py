"""
Bedrock's known gamerules. Unlike Java, Bedrock has no gamerules.json or
similar file — the only way to read or change one is the /gamerule
console command, and there's no query-response channel to reliably read
a live value back out of server stdout. So the panel treats "what we
last told the server to set" as the source of truth (see
gamerules_store.py) rather than pretending to show a value it can't
actually verify.

Names are lowercase with no separators, matching Bedrock's own command
syntax (Java uses camelCase; Bedrock does not).
"""
from typing import Literal, TypedDict


class GameruleDef(TypedDict):
    name: str
    type: Literal["boolean", "int"]
    default: object
    label: str


KNOWN_GAMERULES: list[GameruleDef] = [
    {"name": "commandblockoutput", "type": "boolean", "default": True, "label": "Command block output"},
    {"name": "commandblocksenabled", "type": "boolean", "default": True, "label": "Command blocks enabled"},
    {"name": "dodaylightcycle", "type": "boolean", "default": True, "label": "Day/night cycle"},
    {"name": "doentitydrops", "type": "boolean", "default": True, "label": "Entity drops"},
    {"name": "dofiretick", "type": "boolean", "default": True, "label": "Fire spread"},
    {"name": "doimmediaterespawn", "type": "boolean", "default": False, "label": "Immediate respawn"},
    {"name": "doinsomnia", "type": "boolean", "default": True, "label": "Phantoms spawn from insomnia"},
    {"name": "domobloot", "type": "boolean", "default": True, "label": "Mob loot"},
    {"name": "domobspawning", "type": "boolean", "default": True, "label": "Mob spawning"},
    {"name": "dotiledrops", "type": "boolean", "default": True, "label": "Block drops"},
    {"name": "doweathercycle", "type": "boolean", "default": True, "label": "Weather cycle"},
    {"name": "drowningdamage", "type": "boolean", "default": True, "label": "Drowning damage"},
    {"name": "falldamage", "type": "boolean", "default": True, "label": "Fall damage"},
    {"name": "firedamage", "type": "boolean", "default": True, "label": "Fire damage"},
    {"name": "freezedamage", "type": "boolean", "default": True, "label": "Freeze damage"},
    {"name": "keepinventory", "type": "boolean", "default": False, "label": "Keep inventory on death"},
    {"name": "mobgriefing", "type": "boolean", "default": True, "label": "Mob griefing"},
    {"name": "naturalregeneration", "type": "boolean", "default": True, "label": "Natural health regeneration"},
    {"name": "pvp", "type": "boolean", "default": True, "label": "Player vs player damage"},
    {"name": "recipesunlock", "type": "boolean", "default": False, "label": "Recipes unlock progressively"},
    {"name": "respawnblocksexplode", "type": "boolean", "default": True, "label": "Respawn anchors/beds explode"},
    {"name": "sendcommandfeedback", "type": "boolean", "default": True, "label": "Send command feedback"},
    {"name": "showcoordinates", "type": "boolean", "default": False, "label": "Show coordinates"},
    {"name": "showdeathmessages", "type": "boolean", "default": True, "label": "Show death messages"},
    {"name": "showtags", "type": "boolean", "default": True, "label": "Show entity interaction tags"},
    {"name": "tntexplodes", "type": "boolean", "default": True, "label": "TNT explodes"},
    {"name": "maxcommandchainlength", "type": "int", "default": 65536, "label": "Max command chain length"},
    {"name": "randomtickspeed", "type": "int", "default": 1, "label": "Random tick speed"},
    {"name": "spawnradius", "type": "int", "default": 10, "label": "Spawn point radius"},
    {"name": "playerssleepingpercentage", "type": "int", "default": 100, "label": "Players sleeping percentage"},
]

VALID_GAMERULE_NAMES = {r["name"] for r in KNOWN_GAMERULES}
