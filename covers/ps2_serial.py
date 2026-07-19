"""
GAME MACHINE - PS2 serial number extraction from ISO files.
"""
import re

from covers.iso_parser import parse_dir_record, read_directory


def get_ps2_serial(iso_path):
    """
    Extracts the PlayStation 2 game serial number from SYSTEM.CNF in a PS2 ISO file.
    Returns format prefix-XXXXX (e.g. SLUS-21134).
    """
    try:
        with open(iso_path, "rb") as f:
            # Read PVD at sector 16
            f.seek(16 * 2048)
            pvd = f.read(2048)
            if len(pvd) < 2048 or pvd[1:6] != b"CD001":
                return None
                
            # Root directory record at offset 156 in PVD
            root_rec = parse_dir_record(pvd, 156)
            if not root_rec:
                return None
                
            # Read Root Directory
            root_records = read_directory(f, root_rec['lba'], root_rec['length'])
            system_cnf_rec = None
            for r in root_records:
                name = r['name'].decode('utf-8', errors='ignore').split(';')[0].rstrip('.')
                if name.upper() == "SYSTEM.CNF":
                    system_cnf_rec = r
                    break
            
            if not system_cnf_rec:
                return None
                
            # Read SYSTEM.CNF file content
            f.seek(system_cnf_rec['lba'] * 2048)
            cnf_data = f.read(system_cnf_rec['length']).decode('utf-8', errors='ignore')
            
            # Match BOOT2 = cdrom0:\SLUS_211.34;1
            match = re.search(r'BOOT2\s*=\s*cdrom0:\\\\?([^;]+)', cnf_data, re.IGNORECASE)
            if not match:
                match = re.search(r'BOOT2\s*=\s*\S*\\([^;]+)', cnf_data, re.IGNORECASE)
                
            if match:
                raw_filename = match.group(1).strip()
                # PCSX2 stores save states under the hyphenated serial form
                # (e.g. "SLUS-21134 (CRC).00.p2s"), while the BOOT2 line in
                # SYSTEM.CNF uses an underscore + dotted number ("SLUS_211.34").
                # Normalize the dotted form to the hyphenated one so the serial
                # matches the actual state-file / cover-art names.
                # PCSX2 serials appear in two forms:
                #   * file/state form:  "SLUS-21134"  (4 letters, '-', 5 digits)
                #   * SYSTEM.CNF BOOT2: "SLUS_211.34" (4 letters, '_', 3 digits, '.', 2 digits)
                # Normalize both to the hyphenated "SLUS-21134" used by save
                # states and cover-art repositories.
                clean_match = re.search(r'([A-Z]{4})[_\.\-](\d{3})[_\.\-](\d{2})', raw_filename.upper())
                if clean_match:
                    prefix, num1, num2 = clean_match.groups()
                    return f"{prefix}-{num1}{num2}"
                clean_match = re.search(r'([A-Z]{4})[_\.\-](\d{5})', raw_filename.upper())
                if clean_match:
                    prefix, digits = clean_match.groups()
                    return f"{prefix}-{digits}"
                else:
                    return raw_filename.replace('_', '-').replace('.', '')
    except Exception as e:
        print(f"[ISO Parser] Error reading PS2 ISO {iso_path}: {e}")
    return None
