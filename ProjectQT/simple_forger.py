import json
import random
import hashlib
import os

# --- Editable Variables ---
STAR_ID = "0"
AWAKE_STAR = "0"
PET_IDS = ["1009", "1010", "1011", "1012"] # Add your IDs here\
ALL_PET_IDS=["1001","1002","1003","1004","1005","1006","1007","1008","1009","1010","1011","1012","1013","1014","1015","1016","1017","1018","1019","1020","1021","1022","1023","1024","1025","1026","1027","1028","1029","1030","1031","1032","1033","1034","1035","1036","1038","1039","1040","1041","1042","1043","1044","1045","1046","1047","1048","1049","1050","1051","1053","1054","1055","1056","1057","1059","1060","1061","1062","1063","1064","1065","1066","1068","1069","1070","1072","1073","1075","1077","1078","1079","1080","1081","1082","1083","1084","1085","1086","1087","1088","1089","1090","1091","1092","1093","1094","1095","1096","1097","1098","1099","1100","1101","1102","1103","1104","1105","1106","1107","1108","1109","1110","1111","1112","1113","1116","1117"]

# --- Constants / Template Values ---
USER_ID = "VVG0000034278"
HP = "7476"
RHP = "1086"
ATK = "1097"
LEVEL = "39"
QUALITY = "2"
STAR_SPIRIT = "12"
PVP_MIGHT = "11593"
EXP = "16295"
PVE_SET_LV = "0"
PVP_SET_LV = "0"
SOURCE_FROM = "0"
AWAKE_LEVEL = "0"
CREATE_TIME = "2024-03-14 10:52:45"
LAST_UPDATE_TIME = "2026-02-21 02:05:04"

def make_random_serial():
    """Generates a random 40-char hex string."""
    return hashlib.sha1(os.urandom(32)).hexdigest()

def forge():
    results = []
    
    for pid in PET_IDS:
        pid_str = str(pid)
        pet_obj = {
            "pet_serial_id": make_random_serial(),
            "user_id": USER_ID,
            "pet_id": pid_str,
            "current_hp": HP,
            "current_rhp": RHP,
            "current_atk": ATK,
            "level": LEVEL,
            "quality": QUALITY,
            "star_id": STAR_ID,
            "star_spirit": STAR_SPIRIT,
            "pvp_might": PVP_MIGHT,
            "exp": EXP,
            "pve_set_lv": PVE_SET_LV,
            "pvp_set_lv": PVP_SET_LV,
            "solid_passive_skill_serial": None,
            "source_from": SOURCE_FROM,
            "awake_level": AWAKE_LEVEL,
            "awake_star": AWAKE_STAR,
            "create_time": CREATE_TIME,
            "last_update_time": LAST_UPDATE_TIME,
            "active_skills": [],
            "solid_passive_skills": [],
            "succinct_passive_skills": [],
            "active_skills_id": f"7{pid_str}",
            "pvp_active_skills_id": f"72{pid_str}"
        }
        results.append(pet_obj)
    
    # Generate the final string for Burp
    payload_str = f'"pet_list_v2":{json.dumps(results, separators=(",", ":"))}'
    
    with open("payload", "w", encoding="utf-8") as f:
        f.write(payload_str)
    
    print(f"Successfully forged {len(results)} pets into file 'payload'")
    print(f"Sample serial used: {results[0]['pet_serial_id']}")

if __name__ == "__main__":
    forge()
