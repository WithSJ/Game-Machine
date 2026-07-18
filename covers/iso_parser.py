"""
GAME MACHINE - ISO file parsing for cover art extraction.
Parses PSP/PS3 ISO9660 filesystem to extract ICON0.PNG and PIC1.PNG.
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
