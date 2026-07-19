"""
GAME MACHINE - ISO file parsing for cover art extraction.
Parses PSP/PS3 ISO9660 filesystem to extract ICON0.PNG and PIC1.PNG.
Also reads PARAM.SFO to identify game serials / disc IDs for save-state matching.
"""
import re


def parse_dir_record(data, offset):
    if offset + 33 > len(data):
        return None
    length = data[offset]
    if length == 0 or offset + length > len(data):
        return None
    
    lba = int.from_bytes(data[offset+2 : offset+6], byteorder='little')
    data_len = int.from_bytes(data[offset+10 : offset+14], byteorder='little')
    flags = data[offset+25]
    is_dir = bool(flags & 2)
    fi_len = data[offset+32]
    
    if offset + 33 + fi_len > len(data):
        return None
        
    fi = data[offset+33 : offset+33+fi_len]
    return {
        "lba": lba,
        "length": data_len,
        "is_dir": is_dir,
        "name": fi
    }


def read_directory(f, lba, data_len):
    records = []
    num_sectors = (data_len + 2047) // 2048
    for s in range(num_sectors):
        try:
            f.seek((lba + s) * 2048)
            sector_data = f.read(2048)
            if len(sector_data) < 2048:
                break
            offset = 0
            while offset < 2048:
                length = sector_data[offset]
                if length == 0:
                    break
                rec = parse_dir_record(sector_data, offset)
                if rec is None:
                    break
                records.append(rec)
                offset += length
        except Exception:
            break
    return records


def extract_iso_images(iso_path, game_dir_name):
    """
    Parses a PSP/PS3 ISO file and returns a tuple (icon0_data, pic1_data) as bytes,
    or (None, None) if not found or error.
    """
    try:
        with open(iso_path, "rb") as f:
            # Read Primary Volume Descriptor at sector 16
            f.seek(16 * 2048)
            pvd = f.read(2048)
            if len(pvd) < 2048 or pvd[1:6] != b"CD001":
                return None, None
                
            # Root directory record starts at offset 156 of the PVD
            root_rec = parse_dir_record(pvd, 156)
            if not root_rec:
                return None, None
                
            # Read Root Directory records
            root_records = read_directory(f, root_rec['lba'], root_rec['length'])
            game_rec = None
            for r in root_records:
                name = r['name'].decode('utf-8', errors='ignore').split(';')[0].rstrip('.')
                if name.upper() == game_dir_name.upper():
                    game_rec = r
                    break
                    
            if not game_rec:
                return None, None
                
            # Read game_dir records
            game_records = read_directory(f, game_rec['lba'], game_rec['length'])
            icon0_rec = None
            pic1_rec = None
            for r in game_records:
                name = r['name'].decode('utf-8', errors='ignore').split(';')[0].rstrip('.')
                name_upper = name.upper()
                if name_upper == "ICON0.PNG":
                    icon0_rec = r
                elif name_upper == "PIC1.PNG":
                    pic1_rec = r
                    
            icon0_data = None
            pic1_data = None
            if icon0_rec:
                f.seek(icon0_rec['lba'] * 2048)
                icon0_data = f.read(icon0_rec['length'])
            if pic1_rec:
                f.seek(pic1_rec['lba'] * 2048)
                pic1_data = f.read(pic1_rec['length'])
                
            return icon0_data, pic1_data
    except Exception as e:
        print(f"[ISO Parser] Error reading {iso_path}: {e}")
        return None, None


# ============================================================
# PARAM.SFO parsing - lets us identify games by serial / disc ID
# (used by core/savestates.py to find matching save-state files).
# ============================================================
def _read_iso_file(iso_path, dir_name, file_name):
    """Read bytes of a single file from a directory in an ISO9660 image.

    Returns the file contents or None if the file / directory / ISO is missing.
    Mirrors the directory-walk logic of extract_iso_images but is parameterized
    so we can pull any file (e.g. PARAM.SFO) out of any subdirectory.
    """
    try:
        with open(iso_path, "rb") as f:
            f.seek(16 * 2048)
            pvd = f.read(2048)
            if len(pvd) < 2048 or pvd[1:6] != b"CD001":
                return None
            root_rec = parse_dir_record(pvd, 156)
            if not root_rec:
                return None
            root_records = read_directory(f, root_rec['lba'], root_rec['length'])
            target_dir = None
            for r in root_records:
                name = r['name'].decode('utf-8', errors='ignore').split(';')[0].rstrip('.')
                if name.upper() == dir_name.upper():
                    target_dir = r
                    break
            if not target_dir:
                return None
            dir_records = read_directory(f, target_dir['lba'], target_dir['length'])
            target_file = None
            for r in dir_records:
                name = r['name'].decode('utf-8', errors='ignore').split(';')[0].rstrip('.')
                if name.upper() == file_name.upper():
                    target_file = r
                    break
            if not target_file:
                return None
            f.seek(target_file['lba'] * 2048)
            return f.read(target_file['length'])
    except Exception as e:
        print(f"[ISO Parser] Error reading {iso_path}/{dir_name}/{file_name}: {e}")
        return None


def parse_param_sfo(data):
    """Parse a PARAM.SFO binary blob into a dict of {key: value}.

    The SFO format (used by PSP and PS3 discs) is:
      header (20 bytes): magic "\x00PSF" | version | key_table_offset |
                         data_table_offset | index_entries
      index table:      one 16-byte record per entry
                        (key_offset:u16, data_fmt:u16, data_len:u32,
                         data_max_len:u32, data_offset:u32)
      key table:        null-terminated UTF-8 strings
      data table:        values (UTF-8 strings for fmt 0x0404 / 0x0204,
                        little-endian u32 for fmt 0x0402)

    Only string and integer values are decoded; raw/unknown formats
    are stored as bytes so callers can still inspect them if needed.
    """
    if not data or len(data) < 20:
        return {}
    if data[0:4] != b"\x00PSF":
        return {}

    key_table_offset = int.from_bytes(data[8:12], "little")
    data_table_offset = int.from_bytes(data[12:16], "little")
    index_entries = int.from_bytes(data[16:20], "little")

    result = {}
    for i in range(index_entries):
        rec_off = 20 + i * 16
        if rec_off + 16 > len(data):
            break
        key_offset = int.from_bytes(data[rec_off:rec_off + 2], "little")
        data_fmt = int.from_bytes(data[rec_off + 2:rec_off + 4], "little")
        data_len = int.from_bytes(data[rec_off + 4:rec_off + 8], "little")
        data_offset = int.from_bytes(data[rec_off + 12:rec_off + 16], "little")

        key_start = key_table_offset + key_offset
        key_end = data.find(b"\x00", key_start)
        if key_end == -1:
            continue
        key = data[key_start:key_end].decode("utf-8", errors="ignore")

        val_start = data_table_offset + data_offset
        val_end = val_start + data_len
        if val_end > len(data):
            continue
        raw = data[val_start:val_end]

        if data_fmt in (0x0404, 0x0204):
            null_idx = raw.find(b"\x00")
            if null_idx != -1:
                raw = raw[:null_idx]
            result[key] = raw.decode("utf-8", errors="ignore")
        elif data_fmt == 0x0402:
            if len(raw) >= 4:
                result[key] = int.from_bytes(raw[:4], "little")
            else:
                result[key] = raw
        else:
            result[key] = raw

    return result


def get_psp_disc_id(iso_path):
    """Return (DISC_ID, DISC_VERSION) from a PSP ISO's PARAM.SFO,
    e.g. ("ULUS12345", "1.00"). Returns (None, None) if unavailable."""
    sfo_data = _read_iso_file(iso_path, "PSP_GAME", "PARAM.SFO")
    if not sfo_data:
        return None, None
    sfo = parse_param_sfo(sfo_data)
    return sfo.get("DISC_ID"), sfo.get("DISC_VERSION")


def get_ps3_title_id(iso_path):
    """Return TITLE_ID (e.g. "BLUS30450") from a PS3 ISO's PARAM.SFO,
    or None if unavailable."""
    sfo_data = _read_iso_file(iso_path, "PS3_GAME", "PARAM.SFO")
    if not sfo_data:
        return None
    sfo = parse_param_sfo(sfo_data)
    return sfo.get("TITLE_ID")
