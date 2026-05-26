import json
import hashlib

# ============================================================
#  CONFIGURATION - Edit these variables
# ============================================================

PET_IDS = [
  1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010,
  1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020,
  1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030,
  1031, 1032, 1033, 1034, 1035, 1036, 1038, 1039, 1040, 1041,
  1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 1050, 1051,
  1053, 1054, 1055, 1056, 1057, 1059, 1060, 1061, 1062, 1063,
  1064, 1065, 1066, 1068, 1069, 1070, 1072, 1073, 1075, 1077,
  1078, 1079, 1080, 1081, 1082, 1083, 1084, 1085, 1086, 1087,
  1088, 1089, 1090, 1091, 1092, 1093, 1094, 1095, 1096, 1097,
  1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107,
  1108, 1109, 1110, 1111, 1112, 1113, 1116, 1117,
]

USER_ID       = "VVG0000034278"

STAR_ID       = "4"       # 0-4  (star rating)
STAR_SPIRIT   = "10"      # star spirit count
LEVEL         = "20"      # pet level
QUALITY       = "4"       # 0-4  (rarity/quality)
CURRENT_HP    = "99"
CURRENT_RHP   = "99"
CURRENT_ATK   = "99"
EXP           = "99"
PVP_MIGHT     = "99"
PVE_SET_LV    = "0"
PVP_SET_LV    = "0"
AWAKE_LEVEL   = "0"       # awakening level
AWAKE_STAR    = "0"       # awakening star
SOURCE_FROM   = "summon"
CREATE_TIME   = "2024-03-12 19:12:44"
LAST_UPDATE   = "2026-02-21 02:05:04"

# ============================================================
#  OUTPUT OPTIONS
# ============================================================

# What to output:
#   "burp_replace"  ->  full "pet_list_v2":[...] ready to paste into Burp Replace field
#   "array"         ->  just the [...] JSON array
#   "pretty"        ->  pretty-printed JSON array (for readability/debugging)
#   "patch"         ->  patches an actual response file (set INPUT_RESPONSE_FILE below)
OUTPUT_MODE = "burp_replace"

OUTPUT_FILE          = "output_payload.txt"  # set to None to print to console
INPUT_RESPONSE_FILE  = None   # e.g. "response.txt" — only used when OUTPUT_MODE = "patch"

# ============================================================
#  SCRIPT - No need to edit below this line
# ============================================================

def make_serial(pet_id):
    a = hashlib.md5(f"pet_{pet_id}".encode()).hexdigest()
    b = hashlib.md5(f"s2_{pet_id}".encode()).hexdigest()[:8]
    return a + b

def make_pet(pet_id):
    return {
        "pet_serial_id":              make_serial(pet_id),
        "user_id":                    USER_ID,
        "pet_id":                     str(pet_id),
        "current_hp":                 CURRENT_HP,
        "current_rhp":                CURRENT_RHP,
        "current_atk":                CURRENT_ATK,
        "level":                      LEVEL,
        "quality":                    QUALITY,
        "star_id":                    STAR_ID,
        "star_spirit":                STAR_SPIRIT,
        "pvp_might":                  PVP_MIGHT,
        "exp":                        EXP,
        "pve_set_lv":                 PVE_SET_LV,
        "pvp_set_lv":                 PVP_SET_LV,
        "solid_passive_skill_serial": None,
        "source_from":                SOURCE_FROM,
        "awake_level":                AWAKE_LEVEL,
        "awake_star":                 AWAKE_STAR,
        "create_time":                CREATE_TIME,
        "last_update_time":           LAST_UPDATE,
        "active_skills":              [],
        "solid_passive_skills":       [],
        "succinct_passive_skills":    [],
        "active_skills_id":           f"7{pet_id}",
        "pvp_active_skills_id":       f"72{pet_id}"
    }

def build_array(pets):
    return '[' + ','.join(json.dumps(p, separators=(',', ':')) for p in pets) + ']'

def extract_pet_list_v2(text):
    """
    Bracket-depth aware extractor.
    Finds "pet_list_v2":[ and walks characters forward tracking depth,
    respecting strings and escape sequences, so nested [] inside pet
    objects are never mistaken for the closing bracket of the outer array.
    Returns (start_index, end_index_exclusive) of the full key+array substring.
    """
    key = '"pet_list_v2":['
    start = text.find(key)
    if start == -1:
        return None, None

    bracket_start = start + len(key) - 1  # index of opening [
    depth = 0
    i = bracket_start
    in_string = False
    escape = False

    while i < len(text):
        c = text[i]
        if escape:
            escape = False
        elif c == '\\' and in_string:
            escape = True
        elif c == '"' and not escape:
            in_string = not in_string
        elif not in_string:
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return start, i + 1  # end is exclusive
        i += 1

    return None, None  # unmatched brackets

def patch_response(response_text, new_array_json):
    start, end = extract_pet_list_v2(response_text)
    if start is None:
        raise ValueError("Could not find pet_list_v2 in response")
    return response_text[:start] + '"pet_list_v2":' + new_array_json + response_text[end:]

def generate():
    pets = [make_pet(pid) for pid in PET_IDS]
    array_json = build_array(pets)

    if OUTPUT_MODE == "pretty":
        result = json.dumps(pets, indent=2)

    elif OUTPUT_MODE == "array":
        result = array_json

    elif OUTPUT_MODE == "patch":
        if not INPUT_RESPONSE_FILE:
            print("❌ Set INPUT_RESPONSE_FILE to use patch mode.")
            return
        with open(INPUT_RESPONSE_FILE, 'r') as f:
            response_text = f.read()
        result = patch_response(response_text, array_json)
        print(f"✅ Patched! pet_list_v2 replaced with {len(pets)} pets.")

    else:  # burp_replace
        result = '"pet_list_v2":' + array_json

    if OUTPUT_FILE:
        with open(OUTPUT_FILE, 'w') as f:
            f.write(result)
        print(f"✅ Done! {len(pets)} pets generated.")
        print(f"   Output mode : {OUTPUT_MODE}")
        print(f"   Saved to    : {OUTPUT_FILE}")
        print(f"   Length      : {len(result):,} chars")

        if OUTPUT_MODE == "burp_replace":
            print()
            print("=" * 57)
            print("  BURP SUITE  →  Proxy → Match and Replace → Add")
            print("=" * 57)
            print("  Type        : Response body")
            print("  Regex match : ON")
            print('  Match       : "pet_list_v2":\\[.*?\\],"pet_god_list"')
            print(f'  Replace     : <contents of {OUTPUT_FILE}>,"pet_god_list"')
            print("=" * 57)
            print()
            print("  ⚠️  If Burp silently does nothing (replace string too large),")
            print("     switch OUTPUT_MODE to 'patch' and use a mitmproxy script instead.")
    else:
        print(result)

if __name__ == "__main__":
    generate()