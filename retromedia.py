#!/usr/bin/env python3
"""
RetroMedia - Virtual removable & fixed media emulator

Copyright (c) 2026 Chris McGimpsey-Jones
Released under the MIT License

https://github.com/fpucore/retromedia

Authentic capacities, transfer speeds, write buffering, Audio CD (CD-DA) creation,
LightScribe physical etching, Multi-Era Copy Protection, Pirate/Hacker Overrides, 
Drive Rigs, Cross-transfers, Cloning, Batch Ripping, and Playback via FFmpeg.
"""

import os
import sys
import json
import time
import struct
import random
import hashlib
import argparse
import shlex
import shutil
import tempfile
import subprocess
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# ==== Optional Image Processing ====
try:
    from PIL import Image, ImageOps, ImageDraw, ImageEnhance, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

KB = 1024
MB = 1024 * KB
GB = 1024 * MB

MAGIC = b"RETROFD\x02"
VERSION = 2

# ====
# Media specifications
# ====
MEDIA_SPECS = {
    # ---- Floppy ----
    "5.25-360k": {
        "size": 360 * KB, "read": 25_600, "write": 22_500,
        "seek_ms": 200, "buffer": 0, "label": '5.25" DD 360K',
        "family": "floppy", "recordable": True, "rewritable": True, "type": "data",
    },
    "5.25-1.2m": {
        "size": 1200 * KB, "read": 51_200, "write": 46_000,
        "seek_ms": 100, "buffer": 0, "label": '5.25" HD 1.2M',
        "family": "floppy", "recordable": True, "rewritable": True, "type": "data",
    },
    "3.5-720k": {
        "size": 720 * KB, "read": 30_720, "write": 25_600,
        "seek_ms": 150, "buffer": 0, "label": '3.5" DD 720K',
        "family": "floppy", "recordable": True, "rewritable": True, "type": "data",
    },
    "3.5-1.44m": {
        "size": 1440 * KB, "read": 63_488, "write": 56_320,
        "seek_ms": 90, "buffer": 0, "label": '3.5" HD 1.44M',
        "family": "floppy", "recordable": True, "rewritable": True, "type": "data",
    },
    "3.5-2.88m": {
        "size": 2880 * KB, "read": 102_400, "write": 92_160,
        "seek_ms": 80, "buffer": 0, "label": '3.5" ED 2.88M',
        "family": "floppy", "recordable": True, "rewritable": True, "type": "data",
    },

    # ---- Magnetic (Zip) ----
    "zip-100": {
        "size": 100 * MB, "read": 1_400_000, "write": 1_000_000,
        "seek_ms": 29, "buffer": 0, "label": "Zip 100",
        "family": "magnetic", "recordable": True, "rewritable": True, "type": "data",
    },
    "zip-250": {
        "size": 250 * MB, "read": 2_400_000, "write": 1_500_000,
        "seek_ms": 29, "buffer": 0, "label": "Zip 250",
        "family": "magnetic", "recordable": True, "rewritable": True, "type": "data",
    },

    # ---- USB Flash & External Solid-State Drives ----
    "usb-1.1-64m": {
        "size": 64 * MB, "read": 1_000_000, "write": 600_000,
        "seek_ms": 0, "buffer": 0, "label": "Trek ThumbDrive 64MB (USB 1.1)",
        "family": "usb", "recordable": True, "rewritable": True, "type": "data", "theatrics": False,
    },
    "usb-2.0-4g": {
        "size": 4 * GB, "read": 18 * MB, "write": 4 * MB,
        "seek_ms": 0, "buffer": 0, "label": "Kingston DataTraveler 4GB (USB 2.0)",
        "family": "usb", "recordable": True, "rewritable": True, "type": "data", "theatrics": False,
    },
    "usb-3.0-64g": {
        "size": 64 * GB, "read": 100 * MB, "write": 35 * MB,
        "seek_ms": 0, "buffer": 0, "label": "Corsair Flash Voyager 64GB (USB 3.0)",
        "family": "usb", "recordable": True, "rewritable": True, "type": "data", "theatrics": False,
    },
    "usb-3.2-256g": {
        "size": 256 * GB, "read": 400 * MB, "write": 240 * MB,
        "seek_ms": 0, "buffer": 0, "label": "SanDisk Extreme PRO 256GB (USB 3.2)",
        "family": "usb", "recordable": True, "rewritable": True, "type": "data", "theatrics": False,
    },
    "usb-3.2-1t": {
        "size": 1000 * GB, "read": 1050 * MB, "write": 1000 * MB,
        "seek_ms": 0, "buffer": 0, "label": "Samsung T7 Portable SSD 1TB (USB 3.2 Gen 2)",
        "family": "usb", "recordable": True, "rewritable": True, "type": "data", "theatrics": False,
    },

    # ---- Audio Optical (CD-DA / Red Book) Branded & Generic ----
    "cd-audio-74": {
        "size": 650 * MB, "max_seconds": 74 * 60, "read": 153_600 * 8, "write": 153_600 * 4,
        "seek_ms": 1500, "buffer": 2 * MB, "label": "Audio CD-R (74 Min / 650MB)",
        "family": "audio-cd", "recordable": True, "rewritable": False, "type": "audio",
    },
    "cd-audio-80": {
        "size": 700 * MB, "max_seconds": 80 * 60, "read": 153_600 * 16, "write": 153_600 * 8,
        "seek_ms": 1200, "buffer": 2 * MB, "label": "Audio CD-R (80 Min / 700MB)",
        "family": "audio-cd", "recordable": True, "rewritable": False, "type": "audio",
    },
    "cd-audio-tdk-74": {
        "size": 650 * MB, "max_seconds": 74 * 60, "read": 153_600 * 8, "write": 153_600 * 4,
        "seek_ms": 1500, "buffer": 2 * MB, "label": "TDK Music CD-R (74 Min)",
        "family": "audio-cd", "recordable": True, "rewritable": False, "type": "audio",
    },
    "cd-audio-sony-80": {
        "size": 700 * MB, "max_seconds": 80 * 60, "read": 153_600 * 16, "write": 153_600 * 8,
        "seek_ms": 1200, "buffer": 2 * MB, "label": "Sony CD-R Audio (80 Min)",
        "family": "audio-cd", "recordable": True, "rewritable": False, "type": "audio",
    },
    "cd-audio-maxell-80": {
        "size": 700 * MB, "max_seconds": 80 * 60, "read": 153_600 * 16, "write": 153_600 * 8,
        "seek_ms": 1200, "buffer": 2 * MB, "label": "Maxell CD-R Music Pro (80 Min)",
        "family": "audio-cd", "recordable": True, "rewritable": False, "type": "audio",
    },
    "minidisc-audio-74": {
        "size": 270 * MB, "max_seconds": 74 * 60, "read": 156_250 * 2, "write": 156_250,
        "seek_ms": 500, "buffer": 256 * KB, "label": "MiniDisc Audio 74 min",
        "family": "audio-cd", "recordable": True, "rewritable": True, "type": "audio",
    },
    "minidisc-audio-80": {
        "size": 291 * MB, "max_seconds": 80 * 60, "read": 156_250 * 2, "write": 156_250,
        "seek_ms": 500, "buffer": 256 * KB, "label": "MiniDisc Audio 80 min",
        "family": "audio-cd", "recordable": True, "rewritable": True, "type": "audio",
    },

    # ---- Data CD Generic & Branded ----
    "cd-1x": {
        "size": 650 * MB, "read": 153_600, "write": 153_600,
        "seek_ms": 2000, "buffer": 2 * MB, "label": "CD-R 1x (650MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "cd-2x": {
        "size": 650 * MB, "read": 307_200, "write": 307_200,
        "seek_ms": 2000, "buffer": 2 * MB, "label": "CD-R 2x (650MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "cd-4x": {
        "size": 650 * MB, "read": 614_400, "write": 614_400,
        "seek_ms": 1500, "buffer": 2 * MB, "label": "CD-R 4x (650MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "cd-8x": {
        "size": 700 * MB, "read": 1_228_800, "write": 1_228_800,
        "seek_ms": 1500, "buffer": 2 * MB, "label": "CD-R 8x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "cd-16x": {
        "size": 700 * MB, "read": 2_457_600, "write": 2_457_600,
        "seek_ms": 1000, "buffer": 2 * MB, "label": "CD-R 16x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "cd-32x": {
        "size": 700 * MB, "read": 4_915_200, "write": 4_915_200,
        "seek_ms": 1000, "buffer": 2 * MB, "label": "CD-R 32x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "cd-52x": {
        "size": 700 * MB, "read": 7_987_200, "write": 7_987_200,
        "seek_ms": 1000, "buffer": 2 * MB, "label": "CD-R 52x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "cd-rw-700": {
        "size": 700 * MB, "read": 1_228_800, "write": 614_400,
        "seek_ms": 2000, "buffer": 2 * MB, "label": "CD-RW 4x (700MB)",
        "family": "optical", "recordable": True, "rewritable": True, "type": "data",
    },
    "cd-r-taiyo-74": {
        "size": 650 * MB, "read": 153_600, "write": 153_600,
        "seek_ms": 2000, "buffer": 2 * MB, "label": "Taiyo Yuden CD-R 1x (650MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "cd-r-verbatim-80": {
        "size": 700 * MB, "read": 1_228_800, "write": 1_228_800,
        "seek_ms": 1500, "buffer": 2 * MB, "label": "Verbatim DataLifePlus CD-R 8x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "cd-r-memorex-80": {
        "size": 700 * MB, "read": 7_987_200, "write": 7_987_200,
        "seek_ms": 1000, "buffer": 2 * MB, "label": "Memorex CD-R 52x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "cd-rw-imation-80": {
        "size": 700 * MB, "read": 1_228_800, "write": 614_400,
        "seek_ms": 2000, "buffer": 2 * MB, "label": "Imation CD-RW 4x (700MB)",
        "family": "optical", "recordable": True, "rewritable": True, "type": "data",
    },
    "kodak-gold-74": {
        "size": 650 * MB, "read": 614_400, "write": 614_400,
        "seek_ms": 1500, "buffer": 2 * MB, "label": "Kodak Gold CD-R 4x (650MB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },

    # ---- DVD ----
    "dvd-r": {
        "size": 4_700_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1200, "buffer": 4 * MB, "label": "DVD-R 1x (4.7GB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "dvd+r": {
        "size": 4_700_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1200, "buffer": 4 * MB, "label": "DVD+R 1x (4.7GB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "dvd-rw": {
        "size": 4_700_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1200, "buffer": 4 * MB, "label": "DVD-RW 1x (4.7GB)",
        "family": "optical", "recordable": True, "rewritable": True, "type": "data",
    },
    "dvd+rw": {
        "size": 4_700_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1200, "buffer": 4 * MB, "label": "DVD+RW 1x (4.7GB)",
        "family": "optical", "recordable": True, "rewritable": True, "type": "data",
    },
    "dvd-r-dl": {
        "size": 8_500_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1800, "buffer": 4 * MB, "label": "DVD-R DL 1x (8.5GB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "dvd+r-dl": {
        "size": 8_500_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1800, "buffer": 4 * MB, "label": "DVD+R DL 1x (8.5GB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "dvd-ram-2.6": {
        "size": 2_600_000_000, "read": 5_540_000, "write": 1_385_000,
        "seek_ms": 1000, "buffer": 2 * MB, "label": "DVD-RAM 2.6GB",
        "family": "optical", "recordable": True, "rewritable": True, "type": "data",
    },
    "dvd-ram-4.7": {
        "size": 4_700_000_000, "read": 11_080_000, "write": 2_770_000,
        "seek_ms": 1200, "buffer": 4 * MB, "label": "DVD-RAM 4.7GB",
        "family": "optical", "recordable": True, "rewritable": True, "type": "data",
    },

    # ---- HD DVD ----
    "hd-dvd-r": {
        "size": 15 * GB, "read": 18_280_000, "write": 4_570_000,
        "seek_ms": 1800, "buffer": 8 * MB, "label": "HD DVD-R 1x (15GB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "hd-dvd-rw": {
        "size": 15 * GB, "read": 18_280_000, "write": 4_570_000,
        "seek_ms": 1800, "buffer": 8 * MB, "label": "HD DVD-RW 1x (15GB)",
        "family": "optical", "recordable": True, "rewritable": True, "type": "data",
    },

    # ---- Blu-ray ----
    "bd-r": {
        "size": 25 * GB, "read": 36_000_000, "write": 4_500_000,
        "seek_ms": 1800, "buffer": 8 * MB, "label": "BD-R 1x (25GB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "bd-re": {
        "size": 25 * GB, "read": 36_000_000, "write": 4_500_000,
        "seek_ms": 1800, "buffer": 8 * MB, "label": "BD-RE 1x (25GB)",
        "family": "optical", "recordable": True, "rewritable": True, "type": "data",
    },
    "bd-r-dl": {
        "size": 50 * GB, "read": 72_000_000, "write": 9_000_000,
        "seek_ms": 2400, "buffer": 8 * MB, "label": "BD-R DL 2x (50GB)",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "bd-r-xl": {
        "size": 100 * GB, "read": 72_000_000, "write": 9_000_000,
        "seek_ms": 3200, "buffer": 16 * MB, "label": "BD-R XL 100GB",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },
    "bd-r-ql": {
        "size": 128 * GB, "read": 72_000_000, "write": 9_000_000,
        "seek_ms": 3600, "buffer": 16 * MB, "label": "BD-R QL 128GB",
        "family": "optical", "recordable": True, "rewritable": False, "type": "data",
    },

    # ---- MiniDisc Data ----
    "minidisc-80": {
        "size": 291 * MB, "read": 156_250, "write": 156_250,
        "seek_ms": 500, "buffer": 256 * KB, "label": "MiniDisc Data 80 min",
        "family": "minidisc", "recordable": True, "rewritable": True, "type": "data",
    },

    # ---- Vintage HDDs ----
    "st-225": {
        "size": 20 * MB, "read": 625_000, "write": 625_000,
        "seek_ms": 65, "buffer": 0, "label": "ST-225 20MB MFM",
        "family": "hdd-vintage", "recordable": True, "rewritable": True, "theatrics": True, "type": "data",
    },
    "wd-caviar": {
        "size": 170 * MB, "read": 5_242_880, "write": 5_242_880,
        "seek_ms": 12, "buffer": 256 * KB, "label": "WD Caviar 170MB IDE",
        "family": "hdd-vintage", "recordable": True, "rewritable": True, "theatrics": True, "type": "data",
    },

    # ---- Modern Fixed Drives ----
    "hdd-sata-1t": {
        "size": 1000 * GB, "read": 160 * MB, "write": 160 * MB,
        "seek_ms": 8, "buffer": 32 * MB, "label": "SATA HDD 1TB 7200RPM",
        "family": "hdd-modern", "recordable": True, "rewritable": True, "theatrics": True, "type": "data",
    },
    "ssd-sata-1t": {
        "size": 1000 * GB, "read": 560 * MB, "write": 530 * MB,
        "seek_ms": 0, "buffer": 0, "label": "SATA SSD 1TB",
        "family": "ssd", "recordable": True, "rewritable": True, "theatrics": False, "type": "data",
    },
    "nvme-m2-1t": {
        "size": 1000 * GB, "read": 3_500 * MB, "write": 3_000 * MB,
        "seek_ms": 0, "buffer": 0, "label": "NVMe M.2 1TB Gen3",
        "family": "nvme", "recordable": True, "rewritable": True, "theatrics": False, "type": "data",
    },
}

# ====
# Hardware Drive Specifications & Features
# ====
DRIVE_MODELS = {
    # -- Floppy Drives --
    "COMMODORE-1541": {
        "family": "floppy", "read": 400, "write": 400, 
        "label": "Commodore 1541 5.25\" Floppy Drive", "features": []
    },
    "APPLE-DISK-II": {
        "family": "floppy", "read": 15 * KB, "write": 15 * KB, 
        "label": "Apple Disk II 5.25\" Floppy Drive", "features": []
    },
    "CHINON-FZ354": {
        "family": "floppy", "read": 31_744, "write": 28_160, 
        "label": "Chinon FZ-354 Amiga 3.5\" Floppy Drive", "features": []
    },
    "TEAC-FD-235HF": {
        "family": "floppy", "read": 63_488, "write": 56_320, 
        "label": "TEAC FD-235HF 3.5\" Floppy Drive", "features": []
    },
    "IBM-PS2-Model-30": {
        "family": "floppy", "read": 63_488, "write": 56_320, 
        "label": "IBM PS2 Model 30 3.5\" Floppy Drive", "features": []
    },
    "SONY-MPF920": {
        "family": "floppy", "read": 63_488, "write": 56_320, 
        "label": "Sony MPF920 3.5\" Floppy Drive", "features": []
    },
    
    # -- Zip Drives --
    "ZIP-100-PARALLEL": {
        "family": "magnetic", "read": 50 * KB, "write": 50 * KB, 
        "label": "Iomega Zip 100 (Parallel Port)", "features": []
    },
    
    # -- Optical Drives (CD/DVD/BD) --
    "SONY-CDU31A": {
        "family": ("optical", "audio-cd"), "read": 300 * KB, "write": 0, 
        "label": "Sony CDU31A 1x/2x Caddy CD-ROM", "features": []
    },
    "PLEXTOR-4012A": {
        "family": ("optical", "audio-cd"), "read": 6000 * KB, "write": 1800 * KB, 
        "label": "Plextor PlexWriter 40/12/40A", "features": ["burn-proof"]
    },
    "YAMAHA-CRWF1": {
        "family": ("optical", "audio-cd"), "read": 6600 * KB, "write": 3600 * KB, 
        "label": "Yamaha CRW-F1 (DiscT@2)", "features": ["burn-proof", "litescribe"]
    },
    "HP-DVD1040": {
        "family": ("optical", "audio-cd"), "read": 22000 * KB, "write": 11000 * KB, 
        "label": "HP dvd1040 LightScribe DVD Writer", "features": ["burn-proof", "litescribe"]
    },
    "PIONEER-DVR108": {
        "family": ("optical", "audio-cd"), "read": 22000 * KB, "write": 22000 * KB, 
        "label": "Pioneer DVR-108 16x DVD±RW", "features": ["burn-proof"]
    },
    "TOSHIBA-SDH903A": {
        "family": ("optical", "audio-cd"), "read": 18000 * KB, "write": 0, 
        "label": "Toshiba SD-H903A HD-DVD/DVD-ROM", "features": []
    },
    "TOSHIBA-SDH903A-V2": {
        "family": ("optical", "audio-cd"), "read": 18000 * KB, "write": 18000 * KB, 
        "label": "Toshiba SD-H903A-V2 HD-DVD/DVD±RW", "features": ["burn-proof"]
    },
    "PIONEER-BDR207": {
        "family": ("optical", "audio-cd"), "read": 54000 * KB, "write": 54000 * KB, 
        "label": "Pioneer BDR-207 Blu-ray Writer", "features": ["burn-proof"]
    },
    "LITEON-GENERIC-OEM": {
        "family": ("optical", "audio-cd"), "read": 24000 * KB, "write": 24000 * KB, 
        "label": "Lite-On Generic CD/DVD-RW", "features": ["justlink"]
    },
}

FAMILY_ORDER = [
    "floppy", "magnetic", "audio-cd", "optical", "minidisc", 
    "usb", "hdd-vintage", "hdd-modern", "ssd", "nvme"
]

FAMILY_TITLES = {
    "floppy": "FLOPPY DISKS",
    "magnetic": "MAGNETIC (ZIP)",
    "audio-cd": "AUDIO OPTICAL (CD-DA / COMPACT DISC DIGITAL AUDIO)",
    "optical": "DATA OPTICAL (CD / DVD / BLU-RAY)",
    "minidisc": "MINIDISC DATA",
    "usb": "USB FLASH & EXTERNAL SOLID STATE DRIVES",
    "hdd-vintage": "VINTAGE HARD DISKS (MFM / IDE)",
    "hdd-modern": "MODERN HARD DISKS (SATA)",
    "ssd": "SOLID STATE DRIVES (SATA SSD)",
    "nvme": "NVMe DRIVES",
}


def spec_theatrics(spec: dict) -> bool:
    return spec.get("theatrics", True)


def fmt_time(seconds: float) -> str:
    secs = max(0, int(round(seconds)))
    return f"{secs // 60:02d}:{secs % 60:02d}"


def ffprobe_duration(path: str) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise MediaError("ffprobe is required for audio CD operations. Please install FFmpeg.")
    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        raise MediaError(f"Could not read audio stream duration from: {path}")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class MediaError(Exception):
    pass


class BufferUnderrun(MediaError):
    pass


class VirtualDisk:
    def __init__(self, path: str):
        self.path = path
        self.media: Optional[str] = None
        self.size: int = 0
        self.label: str = ""
        self.artist: str = ""
        self.album: str = ""
        self.created: str = ""
        self.write_protect: bool = False
        self.protection_mode: str = "none" # "none", "safedisc", "cactus", "track0"
        self.finalized: bool = False
        self.burning_engine: str = ""
        self.toc: Dict[str, dict] = {}
        self.tracks: List[dict] = []
        self.data_blob: bytearray = bytearray()
        self.loaded = False
        self.hardware_id: str = "GENERIC"
        self.hardware_spec: Optional[dict] = None

    @classmethod
    def create(cls, path: str, media: str, label: str = "") -> "VirtualDisk":
        if media not in MEDIA_SPECS:
            raise MediaError(f"Unknown media type: {media}")
        spec = MEDIA_SPECS[media]
        d = cls(path)
        d.media = media
        d.size = spec["size"]
        d.label = label or os.path.splitext(os.path.basename(path))[0].upper()
        d.created = datetime.now().isoformat(timespec="seconds")
        d.write_protect = False
        d.protection_mode = "none"
        d.finalized = False
        d.burning_engine = ""
        d.toc = {}
        d.tracks = []
        d.data_blob = bytearray()
        d.loaded = True
        d.save()
        return d

    @property
    def is_audio(self) -> bool:
        return self.spec.get("type") == "audio"

    @property
    def used_seconds(self) -> float:
        return sum(t["duration"] for t in self.tracks)

    @property
    def max_seconds(self) -> float:
        if "max_seconds" not in self.spec:
            raise MediaError("Audio medium has no defined time capacity ('max_seconds' missing from spec)")
        return float(self.spec["max_seconds"])

    @property
    def free_seconds(self) -> float:
        return max(0.0, self.max_seconds - self.used_seconds)

    @property
    def used(self) -> int:
        if self.is_audio:
            return sum(t["size"] for t in self.tracks)
        return sum(e["size"] for e in self.toc.values())

    @property
    def free(self) -> int:
        return self.size - self.used

    @property
    def spec(self) -> dict:
        return MEDIA_SPECS[self.media]

    @property
    def theatrics(self) -> bool:
        return spec_theatrics(self.spec)

    def get_effective_speeds(self) -> Tuple[int, int]:
        media_r = self.spec["read"]
        media_w = self.spec["write"]
        if self.hardware_spec:
            hw_r = self.hardware_spec["read"]
            hw_w = self.hardware_spec["write"]
            return min(media_r, hw_r), min(media_w, hw_w)
        return media_r, media_w

    def save(self):
        header_obj = {
            "media": self.media,
            "size": self.size,
            "label": self.label,
            "artist": self.artist,
            "album": self.album,
            "created": self.created,
            "write_protect": self.write_protect,
            "protection_mode": self.protection_mode,
            "finalized": self.finalized,
            "burning_engine": self.burning_engine,
            "tracks": self.tracks,
        }
        header_json = json.dumps(header_obj, ensure_ascii=False).encode("utf-8")
        toc_json = json.dumps(self.toc, ensure_ascii=False).encode("utf-8")

        with open(self.path, "wb") as f:
            f.write(MAGIC)
            f.write(struct.pack("<H", VERSION))
            f.write(struct.pack("<H", len(header_json)))
            f.write(header_json)
            f.write(struct.pack("<I", len(toc_json)))
            f.write(toc_json)
            f.write(bytes(self.data_blob))

    def load(self):
        with open(self.path, "rb") as f:
            magic = f.read(8)
            if magic not in (b"RETROFD\x01", b"RETROFD\x02"):
                raise MediaError("Not a valid RetroMedia disc container")
            version = struct.unpack("<H", f.read(2))[0]
            if version > VERSION:
                raise MediaError(f"Unsupported container version {version}")

            hdr_len = struct.unpack("<H", f.read(2))[0]
            header = json.loads(f.read(hdr_len).decode("utf-8"))

            self.media = header["media"]
            self.size = header["size"]
            self.label = header["label"]
            self.artist = header.get("artist", "")
            self.album = header.get("album", "")
            self.created = header["created"]
            self.write_protect = header.get("write_protect", False)
            self.protection_mode = header.get("protection_mode", "none")
            self.finalized = header.get("finalized", False)
            self.burning_engine = header.get("burning_engine", "")
            self.tracks = header.get("tracks", [])

            toc_len = struct.unpack("<I", f.read(4))[0]
            self.toc = json.loads(f.read(toc_len).decode("utf-8"))
            self.data_blob = bytearray(f.read())

        if self.media not in MEDIA_SPECS:
            raise MediaError(f"Media type '{self.media}' is unsupported")
        self.loaded = True

    def validate_drm(self, ignore_protection=False):
        if self.protection_mode == "none" or ignore_protection:
            return
        
        mode = self.protection_mode
        if mode == "safedisc":
            raise MediaError("SAFEDISC ERROR: Authentication data structure mismatch (Intentional bad sectors 800-10009 detected)")
        elif mode == "securom":
            raise MediaError("SECUROM ERROR: Subchannel topology mismatch (Data Position Measurement failure)")
        elif mode == "cactus":
            raise MediaError("CACTUS DATA SHIELD: Audio session unreadable by host file system (Illegal TOC subcode)")
        elif mode == "track0":
            raise MediaError("DISK ERROR: Track 0 weak-bit synchronization failed (Copy-protection check triggered)")
        else:
            raise MediaError("MEDIA IS COPY-PROTECTED: Operation prohibited by creator")

    # --- Audio Operations ---
    def add_track(
        self,
        src_path: str,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        progress_cb=None,
        protection: Optional[str] = None,
        host_rate: Optional[int] = None,
        overburn: bool = False,
    ):
        if not self.is_audio:
            raise MediaError("This is a DATA medium. Use COPY to add data files.")
        if self.write_protect:
            raise MediaError("DISC IS WRITE-PROTECTED")
        if self.finalized:
            raise MediaError("AUDIO DISC IS FINALIZED")
        if not os.path.isfile(src_path):
            raise MediaError(f"Audio file not found: {src_path}")

        max_allowed_sec = self.max_seconds * (1.05 if overburn and self.spec["family"] in ("optical", "audio-cd") else 1.0)
        allowed_seconds = max(0.0, max_allowed_sec - self.used_seconds)

        duration = ffprobe_duration(src_path)
        if duration > allowed_seconds:
            raise MediaError(
                f"TRACK DOES NOT FIT: {fmt_time(duration)} needed, "
                f"{fmt_time(allowed_seconds)} available on disc "
                f"(Overburn: {'ON' if overburn else 'OFF'})"
            )

        file_size = os.path.getsize(src_path)
        spec = self.spec
        offset = len(self.data_blob)
        orig_len = len(self.data_blob)

        eff_r, eff_w = self.get_effective_speeds()
        try:
            self._throttled_copy(
                src_path,
                file_size,
                eff_w,
                spec["seek_ms"],
                write_mode=True,
                progress_cb=progress_cb,
                buffer_size=spec.get("buffer", 2 * MB),
                protection=protection,
                host_rate=host_rate,
            )
        except Exception:
            del self.data_blob[orig_len:]
            raise

        track_num = len(self.tracks) + 1
        track_title = title or os.path.splitext(os.path.basename(src_path))[0]
        self.tracks.append({
            "track": track_num,
            "title": track_title,
            "artist": artist or self.artist or "",
            "duration": duration,
            "size": file_size,
            "offset": offset,
            "ext": os.path.splitext(src_path)[1] or ".wav",
            "added": datetime.now().isoformat(timespec="seconds"),
            "sha256": sha256_file(src_path),
        })
        self.save()

    def track_bytes(self, index: int, ignore_protection: bool = False) -> bytes:
        self.validate_drm(ignore_protection)
        if index < 0 or index >= len(self.tracks):
            raise MediaError("Track index out of range")
        t = self.tracks[index]
        return bytes(self.data_blob[t["offset"]:t["offset"] + t["size"]])

    # --- Data Operations ---
    def list_files(self) -> List[Tuple[str, int, str]]:
        return [(name, e["size"], e["added"]) for name, e in sorted(self.toc.items())]

    def has_file(self, name: str) -> bool:
        return name in self.toc

    def add_file(
        self,
        src_path: str,
        dest_name: Optional[str] = None,
        progress_cb=None,
        protection: Optional[str] = None,
        host_rate: Optional[int] = None,
        overburn: bool = False,
    ):
        if self.is_audio:
            raise MediaError("This is an AUDIO CD. Use ADD / BURN to burn audio tracks.")
        if self.write_protect:
            raise MediaError("DISK IS WRITE-PROTECTED")
        if self.finalized:
            raise MediaError("MEDIUM IS FINALIZED")
        if not os.path.isfile(src_path):
            raise MediaError(f"Source file not found: {src_path}")

        size = os.path.getsize(src_path)

        max_allowed_bytes = self.size * (1.05 if overburn and self.spec["family"] in ("optical", "audio-cd") else 1.0)
        allowed_bytes = max(0, int(max_allowed_bytes) - self.used)

        if size > allowed_bytes:
            raise MediaError(
                f"NOT ENOUGH SPACE: need {size:,} bytes, "
                f"have {allowed_bytes:,} available "
                f"(Overburn: {'ON' if overburn else 'OFF'})"
            )

        name = dest_name or os.path.basename(src_path)
        if name in self.toc:
            raise MediaError(f"FILE EXISTS: {name}")

        spec = self.spec
        offset = len(self.data_blob)
        original_blob_len = len(self.data_blob)

        eff_r, eff_w = self.get_effective_speeds()
        try:
            self._throttled_copy(
                src_path,
                size,
                eff_w,
                spec["seek_ms"],
                write_mode=True,
                progress_cb=progress_cb,
                buffer_size=spec.get("buffer", 0),
                protection=protection,
                host_rate=host_rate,
            )
        except Exception:
            del self.data_blob[original_blob_len:]
            raise

        self.toc[name] = {
            "size": size,
            "offset": offset,
            "added": datetime.now().isoformat(timespec="seconds"),
        }
        self.save()

    def extract_file(self, name: str, dest_path: str, progress_cb=None, host_rate: Optional[int] = None, ignore_protection: bool = False):
        self.validate_drm(ignore_protection)
        if name not in self.toc:
            raise MediaError(f"FILE NOT FOUND: {name}")
        entry = self.toc[name]
        size, offset = entry["size"], entry["offset"]
        data = bytes(self.data_blob[offset:offset + size])

        eff_r, eff_w = self.get_effective_speeds()

        self._throttled_copy(
            None,
            size,
            eff_r,
            self.spec["seek_ms"],
            write_mode=False,
            progress_cb=progress_cb,
            data=data,
            dest_path=dest_path,
            host_rate=host_rate,
        )

    def delete_file(self, name: str):
        if self.write_protect:
            raise MediaError("DISK IS WRITE-PROTECTED")
        if self.finalized:
            raise MediaError("MEDIUM IS FINALIZED")
        if name not in self.toc:
            raise MediaError(f"FILE NOT FOUND: {name}")

        new_blob = bytearray()
        new_toc = {}
        for fname, entry in self.toc.items():
            if fname == name:
                continue
            chunk = bytes(self.data_blob[entry["offset"]:entry["offset"] + entry["size"]])
            new_toc[fname] = {
                "size": entry["size"],
                "offset": len(new_blob),
                "added": entry["added"],
            }
            new_blob.extend(chunk)

        self.data_blob = new_blob
        self.toc = new_toc
        self.save()

    def format(self):
        if self.write_protect:
            raise MediaError("DISK IS WRITE-PROTECTED")
        if self.finalized and not self.spec["rewritable"]:
            raise MediaError("WRITE-ONCE MEDIUM IS FINALIZED AND CANNOT BE FORMATTED")
        self.toc = {}
        self.tracks = []
        self.data_blob = bytearray()
        if self.spec["rewritable"]:
            self.finalized = False
        self.burning_engine = ""
        self.save()

    def finalize(self, engine: str = ""):
        if self.write_protect:
            raise MediaError("DISK IS WRITE-PROTECTED")
        if self.finalized:
            raise MediaError("MEDIUM IS ALREADY FINALIZED")
        if self.spec["family"] not in ("optical", "audio-cd"):
            raise MediaError("FINALIZE is only available for optical recordable media (CD/DVD/BD)")
        if not self.toc and not self.tracks:
            raise MediaError("CANNOT FINALIZE: MEDIUM IS EMPTY")
        
        self.burning_engine = engine
        self.finalized = True
        self.save()

    def set_write_protect(self, on: bool):
        self.write_protect = on
        self.save()

    # --- Transfer Throttle & Buffer Simulation ---
    def _throttled_copy(
        self,
        src_path: Optional[str],
        total: int,
        bytes_per_sec: int,
        seek_ms: int,
        write_mode: bool,
        progress_cb=None,
        data: Optional[bytes] = None,
        dest_path: Optional[str] = None,
        buffer_size: int = 0,
        protection: Optional[str] = None,
        host_rate: Optional[int] = None,
    ):
        effective_bps = min(bytes_per_sec, host_rate) if host_rate else bytes_per_sec
        effective_bps = max(1, effective_bps)

        if seek_ms > 0:
            if progress_cb:
                progress_cb(0, total, "SEEK" if seek_ms < 1000 else "SPIN-UP", 0, buffer_size, buffer_size)
            time.sleep(seek_ms / 1000.0)

        if write_mode and buffer_size > 0:
            self._buffered_write(src_path, total, effective_bps, buffer_size, progress_cb, protection)
            return

        chunk = max(512, effective_bps // 10)
        copied = 0
        start = time.monotonic()

        if write_mode:
            with open(src_path, "rb") as src:
                while copied < total:
                    this = min(chunk, total - copied)
                    block = src.read(this)
                    if not block:
                        raise MediaError("SOURCE READ FAILED")
                    self.data_blob.extend(block)
                    copied += len(block)
                    target = copied / effective_bps
                    elapsed = time.monotonic() - start
                    if elapsed < target:
                        time.sleep(target - elapsed)
                    if progress_cb:
                        progress_cb(copied, total, "WRITING", 0, 0, 0)
        else:
            with open(dest_path, "wb") as out:
                while copied < total:
                    this = min(chunk, total - copied)
                    out.write(data[copied:copied + this])
                    copied += this
                    target = copied / effective_bps
                    elapsed = time.monotonic() - start
                    if elapsed < target:
                        time.sleep(target - elapsed)
                    if progress_cb:
                        progress_cb(copied, total, "READING", 0, 0, 0)

    def _buffered_write(
        self,
        src_path: str,
        total: int,
        bytes_per_sec: int,
        buffer_size: int,
        progress_cb=None,
        protection: Optional[str] = None,
    ):
        buffer = bytearray()
        copied = 0
        written = 0
        last_tick = time.monotonic()
        producer_chunk = max(32 * KB, min(buffer_size, 256 * KB))

        with open(src_path, "rb") as src:
            while written < total:
                if copied < total and len(buffer) < buffer_size:
                    want = min(producer_chunk, buffer_size - len(buffer), total - copied)
                    block = src.read(want)
                    if not block:
                        raise MediaError("SOURCE READ FAILED")
                    buffer.extend(block)
                    copied += len(block)

                if not buffer:
                    if copied >= total:
                        break
                    if protection:
                        if progress_cb:
                            progress_cb(written, total, "BUFFER-RECOVERY", 0, buffer_size, copied)
                        
                        # JustLink historically claimed faster re-sync times than Burn-Proof
                        recovery_time = 0.15 if protection == "justlink" else 0.35
                        time.sleep(recovery_time)
                        continue
                        
                    raise BufferUnderrun("BUFFER UNDERRUN: recording failed (turn on BURN-PROOF or JUSTLINK)")

                drain = min(len(buffer), max(1, bytes_per_sec // 20), total - written)
                block = bytes(buffer[:drain])
                del buffer[:drain]
                self.data_blob.extend(block)
                written += drain
                time.sleep(drain / bytes_per_sec)

                now = time.monotonic()
                if progress_cb and (now - last_tick >= 0.05 or written >= total):
                    progress_cb(written, total, "BURNING", len(buffer), buffer_size, copied)
                    last_tick = now

        if written != total:
            raise MediaError(f"WRITE FAILED: expected {total} bytes, wrote {written}")


# ====
# Interactive Shell & Playback Engine
# ====
class Shell:
    def __init__(self):
        self.drives: Dict[str, VirtualDisk] = {}
        self.active: Optional[str] = None
        self.burn_proof = False
        self.justlink = False
        self.overburn = False
        self.pirate_mode = False
        self.host_rate: Optional[int] = None
        self._audio_proc = None
        self._block_lines = 0
        
        self.engines = {
            "NERO": "Nero Burning ROM",
            "ASHAMPOO": "Ashampoo Burning Studio",
            "ROXIO": "Roxio Easy CD Creator",
            "ALCOHOL": "Alcohol 120%",
            "CLONECD": "CloneCD",
            "IMGBURN": "ImgBurn"
        }
        self.burn_engine = self.engines["NERO"]

    @property
    def disk(self) -> Optional[VirtualDisk]:
        return self.drives.get(self.active) if self.active else None

    @property
    def disk_path(self) -> Optional[str]:
        d = self.drives.get(self.active) if self.active else None
        return d.path if d else None

    @staticmethod
    def fmt_bytes(n: int) -> str:
        if n < 1024:
            return f"{n} B"
        if n < MB:
            return f"{n / KB:.2f} KB"
        if n < GB:
            return f"{n / MB:.2f} MB"
        return f"{n / GB:.2f} GB"

    @staticmethod
    def fmt_size(n: int) -> str:
        return Shell.fmt_bytes(n)

    def optical_protection(self) -> Optional[str]:
        if self.burn_proof:
            return "burn-proof"
        if self.justlink:
            return "justlink"
        return None

    def intercept_protection(self, target_disk: VirtualDisk, action="read") -> bool:
        if target_disk.protection_mode == "none":
            return True
        if self.pirate_mode:
            print(f"[!] RAW OVERRIDE: Bypassing {target_disk.protection_mode.upper()} structural checks for {action}...")
            time.sleep(0.5)
            return True
        try:
            target_disk.validate_drm(ignore_protection=False)
        except MediaError as e:
            print(f"?{e}")
            return False
        return True

    def check_hardware_feature(self, feature_name: str) -> bool:
        if not self.disk or getattr(self.disk, "hardware_id", "GENERIC") == "GENERIC":
            return True # Generic god-mode drive allows all features
        
        features = self.disk.hardware_spec.get("features", [])
        if feature_name not in features:
            print(f"?HARDWARE ERROR: The attached [{self.disk.hardware_id}] does not support '{feature_name}'.")
            return False
        return True

    def _select_new_active(self):
        if self.active in self.drives:
            return
        self.active = next(iter(self.drives), None)

    def _play_spinup(self, spec: dict):
        if not spec_theatrics(spec):
            return
        if spec["family"] in ("hdd-vintage", "hdd-modern"):
            label = "Spinning up drive"
        elif spec["family"] == "floppy":
            label = "Seeking head"
        elif spec["family"] == "audio-cd":
            label = "TOC Read & Laser Calibration"
        else:
            label = "Loading disc"

        print(label, end="", flush=True)
        for _ in range(3):
            time.sleep(0.25)
            print(".", end="", flush=True)
        time.sleep(spec["seek_ms"] / 1000.0)

    def _play_eject(self, spec: dict):
        if spec["family"] in ("optical", "audio-cd", "minidisc"):
            print("Ejecting disc tray", end="", flush=True)
            for _ in range(3):
                time.sleep(0.2)
                print(".", end="", flush=True)
            print(" *clunk*\n")
        elif spec["family"] in ("hdd-vintage", "hdd-modern"):
            print("Spinning down", end="", flush=True)
            for _ in range(3):
                time.sleep(0.2)
                print(".", end="", flush=True)
            print(" *whirr* stopped.\n")
        else:
            print("*click* Ejected.\n")

    def progress(self, done: int, total: int, phase: str, buffer_used: int = 0, buffer_total: int = 0, source_done: int = 0):
        bar_w = 26
        if phase in ("SEEK", "SPIN-UP"):
            sys.stdout.write(f"[{phase:<14}] " + "." * bar_w + " ")
            sys.stdout.flush()
            return

        pct = done / total if total else 1
        filled = int(bar_w * pct)
        bar = "█" * filled + "░" * (bar_w - filled)

        elapsed = time.monotonic() - getattr(self, "_t0", time.monotonic())
        rate = done / max(0.001, elapsed)

        if phase == "BUFFER-RECOVERY":
            sys.stdout.write(f"\r[RECOVERY] {bar} {pct*100:5.1f}%  Buffer: EMPTY  ")
            sys.stdout.flush()
            return

        btext = ""
        if buffer_total:
            bpct = buffer_used / buffer_total if buffer_total else 0
            bfilled = int(14 * bpct)
            bbar = "█" * bfilled + "░" * (14 - bfilled)
            btext = f"BUF [{bbar}] {bpct*100:4.0f}% "

        protection = " [BurnProof]" if self.burn_proof else (" [JustLink]" if self.justlink else "")

        sys.stdout.write(
            f"\r[{phase:<8}] {bar} {pct*100:5.1f}%  "
            f"{self.fmt_size(done):>8}/{self.fmt_size(total):<8}  "
            f"{self.fmt_size(int(rate))}/s  {btext}{protection}"
        )
        sys.stdout.flush()
        if done >= total:
            sys.stdout.write("\n")

    def progress_start(self):
        self._t0 = time.monotonic()

    # ---- Audio Playback Methods ----
    def _draw(self, lines: List[str]):
        buf = ""
        if self._block_lines:
            buf += f"\033[{self._block_lines}A"
        for ln in lines:
            buf += "\r\033[K" + ln + "\n"
        sys.stdout.write(buf)
        sys.stdout.flush()
        self._block_lines = len(lines)

    def _stop_audio(self):
        p = self._audio_proc
        if p is not None and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass
            try:
                p.wait(timeout=1)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        self._audio_proc = None

    def play(self, *args):
        if not self.disk:
            print("?NO DISC LOADED")
            return
        d = self.disk
        if not d.is_audio:
            print("?PLAY is only for AUDIO CD media (use DIR/EXTRACT for data disks)")
            return
        if not d.tracks:
            print("?AUDIO CD IS EMPTY (use ADD / BURN to burn audio tracks)")
            return
        
        if not self.intercept_protection(d, "Audio Playback (TOC Read)"):
            return

        if not shutil.which("ffplay"):
            print("?ffplay not found. Please install FFmpeg to play Audio CDs.")
            return

        tracks_to_play = []
        if args:
            try:
                tnum = int(args[0])
                if tnum < 1 or tnum > len(d.tracks):
                    print(f"?Track number must be 1..{len(d.tracks)}")
                    return
                tracks_to_play = [(tnum, d.tracks[tnum - 1])]
            except ValueError:
                print("Usage: PLAY [track_number]")
                return
        else:
            tracks_to_play = list(enumerate(d.tracks, 1))

        tty = sys.stdout.isatty()
        try:
            if tty:
                sys.stdout.write("\033[?25l")
                sys.stdout.flush()

            print()
            disc_title = (d.album or d.label or "AUDIO COMPACT DISC")[:34]
            banner = f"COMPACT DISC DIGITAL AUDIO: {disc_title}"
            w = max(48, len(banner) + 4)
            print("  ╔" + "═" * w + "╗")
            print("  ║" + banner.center(w) + "║")
            print("  ╚" + "═" * w + "╝\n")
            print("  [▶] Laser focused / Spindle locked at 1x CLV\n")

            total_disc_time = d.used_seconds
            for idx, track in tracks_to_play:
                self._play_cd_track(d, idx, track, tty, total_disc_time)
                if idx < len(tracks_to_play):
                    time.sleep(0.8)

            print("\n  [■] DISC PLAYBACK COMPLETED.\n")
        except KeyboardInterrupt:
            self._stop_audio()
            print("\n\n  [■] Playback stopped by user.\n")
        finally:
            self._stop_audio()
            if tty:
                sys.stdout.write("\033[?25h")
                sys.stdout.flush()

    def _play_cd_track(self, d: VirtualDisk, idx: int, track: dict, tty: bool, disc_total: float):
        data = d.track_bytes(idx - 1, ignore_protection=True)
        suffix = track.get("ext") or ".audio"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(data)
        tmp.close()

        self._block_lines = 0
        self._audio_proc = None
        try:
            cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp.name]
            try:
                self._audio_proc = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
                )
            except Exception:
                self._audio_proc = None

            dur = max(0.1, float(track["duration"]))
            spinner = ["◓", "◑", "◒", "◐"]
            start = time.monotonic()
            frame = 0

            while True:
                elapsed = time.monotonic() - start
                if elapsed >= dur:
                    break
                frac = min(1.0, elapsed / dur)

                if tty:
                    # Laser lens track visualizer
                    pickup_w = 26
                    pos = int(frac * (pickup_w - 1))
                    laser = "─" * pos + "◎" + "─" * (pickup_w - 1 - pos)
                    bar_w = 26
                    filled = int(bar_w * frac)
                    bar = "█" * filled + "░" * (bar_w - filled)
                    spin = spinner[frame % len(spinner)]

                    lines = [
                        f"  TRACK {idx:02d}/{len(d.tracks):02d} : {track['title'][:34]}",
                        f"  Artist   : {track.get('artist') or d.artist or 'Unknown Artist'}",
                        f"  Time     : [▶] {fmt_time(elapsed)} / {fmt_time(dur)}   {spin}  [1x CLV 44.1kHz]",
                        f"  Laser    : |{laser}|",
                        f"  Progress : [{bar}] {frac*100:5.1f}%",
                    ]
                    self._draw(lines)
                else:
                    if frame % 10 == 0:
                        print(f"  [PLAY] Track {idx:02d} {track['title'][:24]} {fmt_time(elapsed)}/{fmt_time(dur)}")

                frame += 1
                time.sleep(0.15)

            if tty:
                sys.stdout.write("\n")
                sys.stdout.flush()
                self._block_lines = 0
        finally:
            self._stop_audio()
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

    # ---- Shell Commands ----
    def cmd_help(self, *args):
        print("""
RETROMEDIA COMMANDS:

  CREATE <file> <media> [label]                    Create a new virtual medium (Data or Audio CD)
  LOAD <file>                                      Insert / load a medium
  EJECT                                            Eject the current medium
  INFO                                             Show medium information
  DIR / LS                                         List files (or audio tracks) on medium
  COPY <src> [dest]                                Write host file → Data medium
  EXTRACT <name|num> [dest]                        Extract data file or Audio CD track → host
  DELETE / RM <name>                               Delete file from medium
  FORMAT                                           Erase medium
  FINALIZE                                         Close/finalize optical medium
  LITESCRIBE <image>                               Etch a LightScribe label onto the disc
  MEDIA                                            List supported media types

BUFFER, PROTECTION & COPY CONTROL:
  PROTECTION <NONE|SAFEDISC|SECUROM|CACTUS|TRACK0> Set copy protection (Anti-Rip):
                                                       NONE     [DEFAULT]
                                                       SAFEDISC (Introduced in 1998 by Macrovision 
                                                                  Corporation to disrupt optical 
                                                                  disc duplication.)
                                                       SECUROM  (Introduced in 1998 by Sony DADC to 
                                                                  prevent copying and reverse 
                                                                  engineering of software.)
                                                       CACTUS   (Developed by Israeli firm Midbar 
                                                                  Technologies, Cactus Data Shield 
                                                                  is copy protection for audio CDs.) 
                                                       TRACK0   (1980s floppy disk copy protection 
                                                                  using weak-bit and track 
                                                                  anomalies.)
  PIRATE ON|OFF                                    Toggle Admin Mode to bypass copy protections
  CLONE [dest_file.iso]                            Export a raw sector-by-sector clone
  RIP                                              Batch extract all tracks from an Audio CD
  BURN-PROOF ON|OFF                                Enable/disable Burn-Proof protection
  JUSTLINK ON|OFF                                  Enable/disable JustLink protection
  OVERBURN ON|OFF                                  Allow writing past logical disc capacity (+5%)
  ENGINE <name>                                    Set optical burning engine:
                                                       NERO     (Nero Burning ROM) [DEFAULT]
                                                       ASHAMPOO (Ashampoo Burning Studio)
                                                       ROXIO    (Roxio Easy CD Creator)
                                                       ALCOHOL  (Alcohol 120%)
                                                       CLONECD  (CloneCD)
                                                       IMGBURN  (ImgBurn)
  BUFFER                                           Show current recorder settings
  HOSTRATE <KBps>|OFF                              Cap host throughput (min with media rate)

AUDIO CD COMMANDS:
  ADD / BURN <audio> [title]                       Burn an audio track onto the Audio CD
  PLAY [track_number]                              Play the virtual Audio CD using ffplay
  ARTIST <name>                                    Set disc artist
  ALBUM <title>                                    Set disc album title

DRIVE RIG COMMANDS:
  ATTACH <slot> <file> [MODEL_ID]                  Load a drive into the rig (e.g. TEAC-FD235HF)
  DETACH <slot>                                    Remove a drive from the rig
  HARDWARE                                         List authentic historical drive models
  DRIVES                                           List all attached drives
  USE <slot>                                       Switch active drive
  XFER <slot>:<file> <slot>:<file>                 Copy file between drives
  XMOVE <slot>:<file> <slot>:<file>                Move file between drives

HOST COMMANDS:
  HOSTLS [path]                                    List host directory files
  CD <path>                                        Change host directory
  PWD                                              Show current host directory
  QUIT / EXIT                                      Leave program
""")

    def cmd_media(self, *args):
        by_family: Dict[str, List[Tuple[str, dict]]] = {}
        for key, spec in MEDIA_SPECS.items():
            by_family.setdefault(spec["family"], []).append((key, spec))

        line_w = 100
        for family in FAMILY_ORDER:
            entries = by_family.get(family)
            if not entries:
                continue
            title = FAMILY_TITLES.get(family, family.upper())
            print()
            dashes = max(0, line_w - len(title) - 4)
            print(f"── {title} " + "─" * dashes)

            if family == "audio-cd":
                print(f"{'KEY':<20}{'TIME LIMIT':>14}{'READ':>13}{'WRITE':>13}{'BUFFER':>10}  LABEL")
                for key, spec in entries:
                    buf = self.fmt_size(spec["buffer"]) if spec["buffer"] else "-"
                    print(
                        f"{key:<20}"
                        f"{fmt_time(spec['max_seconds']):>14}"
                        f"{self.fmt_size(spec['read'])+'/s':>13}"
                        f"{self.fmt_size(spec['write'])+'/s':>13}"
                        f"{buf:>10}  "
                        f"{spec['label']}"
                    )
            else:
                print(f"{'KEY':<20}{'CAPACITY':>14}{'READ':>13}{'WRITE':>13}{'BUFFER':>10}  LABEL")
                for key, spec in entries:
                    buf = self.fmt_size(spec["buffer"]) if spec["buffer"] else "-"
                    print(
                        f"{key:<20}"
                        f"{self.fmt_size(spec['size']):>14}"
                        f"{self.fmt_size(spec['read'])+'/s':>13}"
                        f"{self.fmt_size(spec['write'])+'/s':>13}"
                        f"{buf:>10}  "
                        f"{spec['label']}"
                    )
        print()

    def cmd_create(self, *args):
        if len(args) < 2:
            print("Usage: CREATE <file> <media> [label]")
            return
        path, media = args[0], args[1].lower()
        label = " ".join(args[2:]) if len(args) > 2 else ""

        if media not in MEDIA_SPECS:
            print(f"?UNKNOWN MEDIA: {media} (type MEDIA for listing)")
            return

        if os.path.exists(path) and input(f"'{path}' exists. Overwrite? [y/N] ").strip().lower() != "y":
            print("Cancelled.")
            return

        try:
            disk = VirtualDisk.create(path, media, label)
            spec = MEDIA_SPECS[media]
            print(f"\n✓ CREATED: {path}")
            print(f"  Media:     {spec['label']}")
            if disk.is_audio:
                print(f"  Capacity:  {fmt_time(disk.max_seconds)} ({self.fmt_size(spec['size'])})")
                print(f"  Type:      COMPACT DISC DIGITAL AUDIO (CD-DA)")
            else:
                print(f"  Capacity:  {self.fmt_size(spec['size'])}")
                print(f"  Type:      {'REWRITABLE' if spec['rewritable'] else 'WRITE-ONCE'}")
            print(f"  Finalized: NO\n")
        except Exception as e:
            print(f"?CREATE FAILED: {e}")

    def cmd_load(self, *args):
        if not args:
            print("Usage: LOAD <file>")
            return
        path = args[0]
        if not os.path.exists(path):
            print(f"?FILE NOT FOUND: {path}")
            return
        try:
            d = VirtualDisk(path)
            d.load()
            slot = "disk0"
            self.drives[slot] = d
            self.active = slot
            self._play_spinup(d.spec)
            print()
            self._show_disk_summary(d, path)
        except Exception as e:
            print(f"?LOAD FAILED: {e}")

    def cmd_attach(self, *args):
        if len(args) < 2:
            print("Usage: ATTACH <slot> <file> [MODEL_ID]")
            return
        slot, path = args[0], args[1]
        hw_id = args[2].upper() if len(args) > 2 else "GENERIC"

        if hw_id != "GENERIC" and hw_id not in DRIVE_MODELS:
            print(f"?UNKNOWN HARDWARE: {hw_id} (Type HARDWARE for a list)")
            return
            
        if slot in self.drives:
            print(f"?SLOT OCCUPIED: '{slot}' (DETACH first)")
            return
        if not os.path.exists(path):
            print(f"?FILE NOT FOUND: {path}")
            return
        try:
            d = VirtualDisk(path)
            d.load()
            
            # Apply Hardware Pairing
            if hw_id != "GENERIC":
                hw_spec = DRIVE_MODELS[hw_id]
                family_match = hw_spec["family"]
                media_fam = d.spec["family"]
                
                if (isinstance(family_match, tuple) and media_fam not in family_match) or \
                   (isinstance(family_match, str) and media_fam != family_match):
                    print(f"?HARDWARE MISMATCH: You cannot insert {d.spec['label']} into a {hw_spec['label']}.")
                    return
                
                d.hardware_id = hw_id
                d.hardware_spec = hw_spec

            self.drives[slot] = d
            if self.active is None:
                self.active = slot
            self._play_spinup(d.spec)
            print()
            self._show_disk_summary(d, path, slot=slot)
            if d.hardware_spec:
                print(f"  Hardware:        {d.hardware_spec['label']} [{hw_id}]\n")
        except Exception as e:
            print(f"?ATTACH FAILED: {e}")

    def cmd_hardware(self, *args):
        print("\n───── LEGACY HARDWARE DRIVES ─────")
        print(f"{'MODEL ID':<20}{'READ MAX':>12}{'WRITE MAX':>12}  DESCRIPTION")
        print("-" * 75)
        for hw_id, spec in DRIVE_MODELS.items():
            r_str = self.fmt_size(spec["read"])+"/s" if spec["read"] else "N/A"
            w_str = self.fmt_size(spec["write"])+"/s" if spec["write"] else "Read-Only"
            print(f"{hw_id:<20}{r_str:>12}{w_str:>12}  {spec['label']}")
        print("\nUsage: ATTACH <slot> <file> [MODEL ID]\n")

    def _show_disk_summary(self, d: VirtualDisk, path: str, slot: Optional[str] = None):
        spec = d.spec
        prefix = f"ATTACHED TO [{slot}]" if slot else "LOADED"
        print(f"✓ {prefix}: {path}")
        print(f"  Label:           {d.label}")
        if d.artist:
            print(f"  Artist:          {d.artist}")
        if d.album:
            print(f"  Album:           {d.album}")
        print(f"  Media:           {spec['label']}")
        if d.is_audio:
            print(f"  Playtime:        {fmt_time(d.used_seconds)} / {fmt_time(d.max_seconds)} ({len(d.tracks)} tracks)")
        else:
            print(f"  Capacity:        {self.fmt_size(d.used)} / {self.fmt_size(d.size)} ({len(d.toc)} files)")
        print(f"  Protection Mode: {d.protection_mode.upper()}")
        print(f"  Finalized:       {'YES' if d.finalized else 'NO'}\n")

    def cmd_detach(self, *args):
        if not args:
            print("Usage: DETACH <slot>")
            return
        slot = args[0]
        if slot not in self.drives:
            print(f"?NO SUCH SLOT: {slot}")
            return
        self._play_eject(self.drives[slot].spec)
        del self.drives[slot]
        if self.active == slot:
            self.active = None
            self._select_new_active()
        print(f"✓ Detached slot [{slot}]\n")

    def cmd_use(self, *args):
        if not args or args[0] not in self.drives:
            print("Usage: USE <slot>")
            return
        self.active = args[0]
        d = self.drives[self.active]
        print(f"✓ Active drive: [{self.active}] {d.label} ({d.spec['label']})\n")

    def cmd_drives(self, *args):
        if not self.drives:
            print("\n  (no drives attached)\n")
            return
        print(f"\n{'SLOT':<10}{'MEDIA':<18}{'LABEL':<18}{'USAGE':>16}{'ITEMS':>8}  ACTIVE")
        print("-" * 80)
        for slot, d in self.drives.items():
            active = "*" if slot == self.active else ""
            if d.is_audio:
                usage = f"{fmt_time(d.used_seconds)}/{fmt_time(d.max_seconds)}"
                items = f"{len(d.tracks)} trk"
            else:
                usage = f"{self.fmt_size(d.used)}/{self.fmt_size(d.size)}"
                items = f"{len(d.toc)} f"
            print(f"{slot:<10}{d.media:<18}{d.label[:17]:<18}{usage:>16}{items:>8}  {active}")
        print()

    def cmd_eject(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        slot = self.active
        self._play_eject(self.disk.spec)
        if slot in self.drives:
            del self.drives[slot]
        self.active = None
        self._select_new_active()

    def cmd_info(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        d = self.disk
        spec = d.spec
        print(f"\n  Slot:            {self.active}")
        print(f"  Path:            {self.disk_path}")
        print(f"  Label:           {d.label}")
        if d.artist:
            print(f"  Artist:          {d.artist}")
        if d.album:
            print(f"  Album:           {d.album}")
        print(f"  Media:           {spec['label']}")
        if d.is_audio:
            print(f"  Tracks:          {len(d.tracks)}")
            print(f"  Time:            {fmt_time(d.used_seconds)} / {fmt_time(d.max_seconds)}")
            print(f"  Remaining:       {fmt_time(d.free_seconds)}")
        else:
            print(f"  Files:           {len(d.toc)}")
            print(f"  Capacity:        {self.fmt_size(d.size)}")
            print(f"  Used:            {self.fmt_size(d.used)} ({d.used/d.size*100:.1f}%)")
            print(f"  Free:            {self.fmt_size(d.free)}")
            print(f"  Buffer:          {self.fmt_size(spec['buffer']) if spec['buffer'] else 'none'}")
            print(f"  Write-Protected: {'YES' if d.write_protect else 'NO'}")
            print(f"  Finalized:       {'YES' if d.finalized else 'NO'}")
        
        print(f"  Protection Mode: {d.protection_mode.upper()}")
        print(f"  Pirate Override: {'ACTIVE' if self.pirate_mode else 'DISABLED'}")
        if d.finalized and d.burning_engine:
            print(f"  Burn Eng.:       {d.burning_engine}")
            print(f"  Created:         {d.created}\n")

    def cmd_protection(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        modes = ["NONE", "SAFEDISC", "SECUROM", "CACTUS", "TRACK0"]
        if not args or args[0].upper() not in modes:
            print(f"Usage: PROTECTION <{' | '.join(modes)}>")
            return
        
        mode = args[0].upper()
        self.disk.protection_mode = mode.lower()
        self.disk.save()
        
        descriptions = {
            "NONE": "Standard unprotected media",
            "SAFEDISC": "SafeDisc intentional bad sector protection active",
            "SECUROM": "SecuROM subchannel geometry and DPM protection active",
            "CACTUS": "Cactus Data Shield audio-session obfuscation active",
            "TRACK0": "1980s Floppy Weak-Bit / Track 0 protection active"
        }
        print(f"✓ Protection mode set to: {mode}")
        print(f"  {descriptions[mode]}\n")

    def cmd_pirate(self, *args):
        if not args or args[0].upper() not in ("ON", "OFF"):
            status = "ACTIVE" if self.pirate_mode else "DISABLED"
            print(f"Pirate Mode: {status}  (Usage: PIRATE ON|OFF)\n")
            return
        
        on = args[0].upper() == "ON"
        self.pirate_mode = on
        if on:
            print("\n⚠ PIRATE MODE ENGAGED: Advanced sector overrides and protection bypasses enabled.\n")
        else:
            print("\n✓ Pirate mode disengaged. Standard DRM enforcement restored.\n")

    def cmd_burnproof(self, *args):
        if not args or args[0].upper() not in ("ON", "OFF"):
            print("Usage: BURN-PROOF ON|OFF")
            return
        self.burn_proof = args[0].upper() == "ON"
        if self.burn_proof:
            self.justlink = False
        print(f"Burn-Proof: {'ON' if self.burn_proof else 'OFF'}\n")

    def cmd_justlink(self, *args):
        if not args or args[0].upper() not in ("ON", "OFF"):
            print("Usage: JUSTLINK ON|OFF")
            return
        self.justlink = args[0].upper() == "ON"
        if self.justlink:
            self.burn_proof = False
        print(f"JustLink: {'ON' if self.justlink else 'OFF'}\n")
        
    def cmd_overburn(self, *args):
        if not args or args[0].upper() not in ("ON", "OFF"):
            print("Usage: OVERBURN ON|OFF")
            return
        self.overburn = args[0].upper() == "ON"
        print(f"Overburn (+5% optical capacity): {'ON' if self.overburn else 'OFF'}\n")

    def cmd_engine(self, *args):
        if not args or args[0].upper() not in self.engines:
            opts = " | ".join(self.engines.keys())
            print(f"Usage: ENGINE <{opts}>")
            return
        self.burn_engine = self.engines[args[0].upper()]
        print(f"Active burning engine set to: {self.burn_engine}\n")

    def cmd_buffer(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        spec = self.disk.spec
        print("\nRECORDER BUFFER")
        print(f"  Media:       {spec['label']}")
        print(f"  Buffer size: {self.fmt_size(spec['buffer']) if spec['buffer'] else 'none'}")
        print(f"  Burn-Proof:  {'ON' if self.burn_proof else 'OFF'}")
        print(f"  JustLink:    {'ON' if self.justlink else 'OFF'}")
        print(f"  Overburn:    {'ON' if self.overburn else 'OFF'}")
        print(f"  Engine:      {self.burn_engine}")
        print(f"  Host rate:   {self.fmt_size(self.host_rate) + '/s' if self.host_rate else 'unlimited'}\n")

    def cmd_hostrate(self, *args):
        if not args:
            cur = f"{self.fmt_size(self.host_rate)}/s" if self.host_rate else "unlimited"
            print(f"Host rate: {cur}  (usage: HOSTRATE <KBps>|OFF)")
            return
        val = args[0].upper()
        if val in ("OFF", "NONE", "0", "UNLIMITED"):
            self.host_rate = None
            print("Host rate: unlimited\n")
            return
        try:
            kbps = float(val)
            if kbps <= 0: raise ValueError
        except ValueError:
            print("Usage: HOSTRATE <KBps>|OFF")
            return
        self.host_rate = int(kbps * KB)
        print(f"Host rate: {self.fmt_size(self.host_rate)}/s ({kbps:g} KB/s)\n")

    def cmd_dir(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        d = self.disk
        if d.is_audio:
            print(f"\n 💿 AUDIO CD: {d.label}")
            if d.artist:
                print(f" Artist: {d.artist}")
            if d.album:
                print(f" Album : {d.album}")
            print(f" {'TRK':<5}{'TITLE':<36}{'DURATION':>10}")
            print(" " + "─" * 53)
            if not d.tracks:
                print("  <empty audio disc>")
            for t in d.tracks:
                print(f"  {t['track']:02d}  {t['title'][:34]:<36}{fmt_time(t['duration']):>10}")
            print(" " + "─" * 53)
            print(f"  TOTAL: {len(d.tracks)} tracks   {fmt_time(d.used_seconds)} / {fmt_time(d.max_seconds)}\n")
        else:
            files = d.list_files()
            print(f"\n 📁 VOLUME: {d.label}")
            print(f" {'NAME':<34}{'SIZE':>14}  ADDED")
            print(" " + "─" * 64)
            if not files:
                print("  <empty medium>")
            for name, size, added in files:
                print(f"  {name:<34}{self.fmt_size(size):>13}  {added}")
            print(f"\n {len(files)} FILE(S)   {self.fmt_size(d.used)} USED   {self.fmt_size(d.free)} FREE\n")

    def cmd_add_track(self, *args):
        if not self.disk:
            print("?NO DISC INSERTED")
            return
        if not self.disk.is_audio:
            print("?Active medium is a DATA drive. Use COPY to add data files.")
            return
        if not args:
            print("Usage: ADD <audio_file> [title]")
            return

        src = os.path.expanduser(args[0])
        title = " ".join(args[1:]) if len(args) > 1 else None

        try:
            print(f"[{self.burn_engine}] Preparing to write Audio track...")
            if self.burn_proof and not self.check_hardware_feature("burn-proof"):
                return
            if self.justlink and not self.check_hardware_feature("justlink"):
                return
            self.progress_start()
            self.disk.add_track(
                src,
                title=title,
                progress_cb=self.progress,
                protection=self.optical_protection(),
                host_rate=self.host_rate,
                overburn=self.overburn,
            )
            t = self.disk.tracks[-1]
            print(f"✓ {self.burn_engine} burned Track {t['track']:02d}: '{t['title']}' ({fmt_time(t['duration'])})\n")
        except Exception as e:
            print(f"\n?BURN FAILED: {e}")

    def cmd_copy(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        if self.disk.is_audio:
            print("?Active medium is an AUDIO CD. Use ADD <audio_file> [title] to burn tracks.")
            return
        if not args:
            print("Usage: COPY <src> [dest_name]")
            return

        src = os.path.expanduser(args[0])
        dest = args[1] if len(args) > 1 else None
        try:
            if self.disk.spec["family"] in ("optical", "audio-cd"):
                print(f"[{self.burn_engine}] Caching data...")
            if self.burn_proof and not self.check_hardware_feature("burn-proof"):
                return
            if self.justlink and not self.check_hardware_feature("justlink"):
                return
            self.progress_start()
            self.disk.add_file(
                src,
                dest,
                progress_cb=self.progress,
                protection=self.optical_protection(),
                host_rate=self.host_rate,
                overburn=self.overburn,
            )
            print(f"✓ Wrote {os.path.basename(dest or src)} to disk\n")
        except Exception as e:
            print(f"\n?COPY FAILED: {e}")

    def cmd_extract(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        if not args:
            print("Usage: EXTRACT <name_or_track_num> [dest_path]")
            return
            
        if not self.intercept_protection(self.disk, "Extraction"): 
            return

        d = self.disk
        if d.is_audio:
            try:
                track_num = int(args[0])
                if track_num < 1 or track_num > len(d.tracks):
                    print(f"?Track number out of range (1..{len(d.tracks)})")
                    return
                t = d.tracks[track_num - 1]
                dest = os.path.expanduser(args[1]) if len(args) > 1 else f"track_{track_num:02d}_{t['title']}{t['ext']}"
                data = d.track_bytes(track_num - 1, ignore_protection=True)
                with open(dest, "wb") as f:
                    f.write(data)
                print(f"✓ Extracted Track {track_num:02d} → {dest}\n")
            except ValueError:
                print("?For Audio CDs, provide the track number: EXTRACT <track_num> [dest]")
        else:
            name = args[0]
            dest = os.path.expanduser(args[1]) if len(args) > 1 else name
            try:
                self.progress_start()
                d.extract_file(name, dest, progress_cb=self.progress, host_rate=self.host_rate, ignore_protection=True)
                print(f"✓ Extracted {name} → {dest}\n")
            except Exception as e:
                print(f"\n?EXTRACT FAILED: {e}")

    def cmd_clone(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        if not self.intercept_protection(self.disk, "Raw Image Clone"): 
            return
        
        dest = args[0] if args else f"{self.disk.label}.iso"
        print(f"Cloning raw sector data to {dest}...")
        try:
            self.progress_start()
            shutil.copyfile(self.disk.path, dest)
            self.progress(100, 100, "CLONING")
            print(f"✓ Clone complete.\n")
        except Exception as e:
            print(f"\n?CLONE FAILED: {e}")

    def cmd_rip(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        if not self.disk.is_audio: 
            print("?RIP is for Audio CDs only. Use CLONE or EXTRACT for data media.")
            return
        if not self.intercept_protection(self.disk, "Batch Ripping"): 
            return
        
        print(f"Ripping {len(self.disk.tracks)} tracks from {self.disk.label}...")
        try:
            for i, t in enumerate(self.disk.tracks):
                dest = f"Track_{t['track']:02d}_{t['title']}{t['ext']}"
                print(f" -> Ripping Track {t['track']:02d}...", end="", flush=True)
                with open(dest, "wb") as f:
                    f.write(self.disk.track_bytes(i, ignore_protection=True))
                print(" Done.")
            print(f"✓ Batch Rip complete.\n")
        except Exception as e:
            print(f"\n?RIP FAILED: {e}")

    def _parse_slot_ref(self, ref: str) -> Tuple[str, str]:
        if ":" not in ref:
            raise MediaError(f"Invalid reference '{ref}' (expected slot:filename)")
        slot, _, name = ref.partition(":")
        if not slot or not name:
            raise MediaError(f"Invalid reference '{ref}' (expected slot:filename)")
        return slot, name

    def _cross_transfer(self, args, move: bool):
        verb = "XMOVE" if move else "XFER"
        if len(args) < 2:
            print(f"Usage: {verb} <slot>:<file> <slot>:<file>")
            return
        try:
            src_slot, src_name = self._parse_slot_ref(args[0])
            dst_slot, dst_name = self._parse_slot_ref(args[1])
        except MediaError as e:
            print(f"?{verb} FAILED: {e}")
            return

        if src_slot not in self.drives:
            print(f"?{verb} FAILED: source slot '{src_slot}' not attached")
            return
        if dst_slot not in self.drives:
            print(f"?{verb} FAILED: destination slot '{dst_slot}' not attached")
            return

        src = self.drives[src_slot]
        dst = self.drives[dst_slot]

        if src_slot == dst_slot and src_name == dst_name:
            print(f"?{verb} FAILED: source and destination are identical")
            return
        if src.is_audio:
            print(f"?{verb} FAILED: Source is an AUDIO CD. Use EXTRACT to rip tracks.")
            return
        
        if not self.intercept_protection(src, f"Cross-Drive {verb}"):
            return

        if not src.has_file(src_name):
            print(f"?{verb} FAILED: FILE NOT FOUND: {src_name}")
            return
        if dst.write_protect:
            print(f"?{verb} FAILED: destination DISK IS WRITE-PROTECTED")
            return
        if dst.finalized:
            print(f"?{verb} FAILED: destination MEDIUM IS FINALIZED")
            return
        if dst.has_file(dst_name):
            print(f"?{verb} FAILED: FILE EXISTS on destination: {dst_name}")
            return

        entry = src.toc[src_name]
        size = entry["size"]
        
        max_allowed_bytes = dst.size * (1.05 if self.overburn and dst.spec["family"] in ("optical", "audio-cd") else 1.0)
        allowed_bytes = max(0, int(max_allowed_bytes) - dst.used)

        if size > allowed_bytes:
            print(
                f"?{verb} FAILED: NOT ENOUGH SPACE on [{dst_slot}]: "
                f"need {size:,} bytes, have {allowed_bytes:,} available "
                f"(Overburn: {'ON' if self.overburn else 'OFF'})"
            )
            return

        if move and (not src.spec["rewritable"] or src.finalized):
            print(f"?{verb} FAILED: source is write-once/finalized (cannot remove source file)")
            return

        tmp_path = None
        try:
            src_spec = src.spec
            dst_spec = dst.spec
            src_eff_r, _ = src.get_effective_speeds()
            _, dst_eff_w = dst.get_effective_speeds()
            eff = min(src_eff_r, dst_eff_w)
            if self.host_rate:
                eff = min(eff, self.host_rate)

            print(f"\nTransfer [{src_slot}] → [{dst_slot}]  {src_name}")
            print(f"  Source read:  {self.fmt_size(src_spec['read'])}/s")
            print(f"  Dest write:   {self.fmt_size(dst_spec['write'])}/s")
            print(f"  Effective:    {self.fmt_size(eff)}/s" + (f"  (host cap {self.fmt_size(self.host_rate)}/s)" if self.host_rate else ""))

            with tempfile.NamedTemporaryFile(delete=False) as tf:
                tmp_path = tf.name

            self.progress_start()
            src.extract_file(
                src_name,
                tmp_path,
                progress_cb=lambda *a: self.progress(a[0], a[1], "XFER-READ" if a[2] in ("READING", "WRITING") else a[2], *a[3:]),
                host_rate=self.host_rate,
                ignore_protection=True
            )

            if dst.spec["family"] in ("optical", "audio-cd"):
                print(f"[{self.burn_engine}] Caching data...")
            dst_hw = getattr(dst, "hardware_id", "GENERIC")
            dst_features = dst.hardware_spec.get("features", []) if dst_hw != "GENERIC" else ["burn-proof", "justlink"]
            
            if self.burn_proof and "burn-proof" not in dst_features:
                print(f"?HARDWARE ERROR: The destination drive [{dst_hw}] does not support 'burn-proof'.")
                return
            if self.justlink and "justlink" not in dst_features:
                print(f"?HARDWARE ERROR: The destination drive [{dst_hw}] does not support 'justlink'.")
                return
            self.progress_start()
            dst.add_file(
                tmp_path,
                dst_name,
                progress_cb=lambda *a: self.progress(a[0], a[1], "XFER-WRITE" if a[2] in ("READING", "WRITING") else a[2], *a[3:]),
                protection=self.optical_protection(),
                host_rate=self.host_rate,
                overburn=self.overburn,
            )

            if move:
                src.delete_file(src_name)
                print(f"✓ Moved {src_name} [{src_slot}] → [{dst_slot}]:{dst_name}\n")
            else:
                print(f"✓ Copied {src_name} [{src_slot}] → [{dst_slot}]:{dst_name}\n")

        except Exception as e:
            print(f"\n?{verb} FAILED: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def cmd_xfer(self, *args):
        self._cross_transfer(args, move=False)

    def cmd_xmove(self, *args):
        self._cross_transfer(args, move=True)

    def cmd_artist(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        if not args:
            print(f"Artist: {self.disk.artist or '(none)'}\n")
            return
        self.disk.artist = " ".join(args)
        self.disk.save()
        print(f"Artist set: {self.disk.artist}\n")

    def cmd_album(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        if not args:
            print(f"Album: {self.disk.album or '(none)'}\n")
            return
        self.disk.album = " ".join(args)
        self.disk.save()
        print(f"Album set: {self.disk.album}\n")

    def cmd_finalize(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        if input("Finalize this medium? No further writes/tracks can be added. [y/N] ").strip().lower() != "y":
            print("Cancelled.")
            return
        try:
            if self.disk.spec["family"] in ("optical", "audio-cd"):
                print(f"[{self.burn_engine}] Writing optical lead-out and Table of Contents...", end="", flush=True)
            else:
                print("Finalizing medium...", end="", flush=True)
                
            for _ in range(5):
                time.sleep(0.3)
                print(".", end="", flush=True)
            self.disk.finalize(engine=self.burn_engine)
            print("\n✓ MEDIUM FINALIZED (Disc closed)\n")
        except Exception as e:
            print(f"\n?FINALIZE FAILED: {e}")

    def cmd_format(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        if input(f"Format '{self.disk.label}'? All data will be lost! [y/N] ").strip().lower() != "y":
            print("Cancelled.")
            return
        try:
            self.disk.format()
            print("✓ Medium formatted.\n")
        except Exception as e:
            print(f"?FORMAT FAILED: {e}")

    def cmd_delete(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        if self.disk.is_audio:
            print("?Cannot delete individual tracks from Audio CD (use FORMAT to erase CD-RW)")
            return
        if not args:
            print("Usage: DELETE <filename>")
            return
        try:
            self.disk.delete_file(args[0])
            print(f"✓ Deleted {args[0]}\n")
        except Exception as e:
            print(f"?DELETE FAILED: {e}")

    def cmd_litescribe(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
            
        # Enforce optical media only
        if self.disk.spec["family"] not in ("optical", "audio-cd"):
            print("?LITESCRIBE is only available for optical media (CD/DVD/BD)")
            return
            
        if not args:
            print("Usage: LITESCRIBE <input_image_path>")
            return
        
        if not self.check_hardware_feature("litescribe"):
            return
            
        if not HAS_PIL:
            print("?Pillow library is required for LightScribe. Install it via: pip install Pillow")
            return

        input_path = os.path.expanduser(args[0])
        if not os.path.exists(input_path):
            print(f"?IMAGE NOT FOUND: {input_path}")
            return

        # Output the label right next to the virtual disc file
        base_name, _ = os.path.splitext(self.disk.path)
        output_path = f"{base_name}_label.png"

        try:
            print("Warming up LightScribe laser...", end="", flush=True)
            for _ in range(3):
                time.sleep(0.4)
                print(".", end="", flush=True)
            print("\nEtching disc label... (this takes a moment)")
            
            # 1. Open, standardize resolution, and square the image
            TARGET_SIZE = 600
            img = Image.open(input_path).convert("L")
            img = ImageOps.fit(img, (TARGET_SIZE, TARGET_SIZE), method=Image.Resampling.LANCZOS)
            
            # 2. Reduce the harsh contrast for a softer, muddier burn
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(0.45)
            
            # 3. Apply LightScribe Palette
            lightscribe_gold = "#d4b982" 
            laser_burn_brown = "#3a2b1d"
            ls_image = ImageOps.colorize(img, black=laser_burn_brown, white=lightscribe_gold)
            
            # 4. Simulate Concentric Laser Grooves and Restrict Speed
            draw = ImageDraw.Draw(ls_image, "RGBA")
            center = (TARGET_SIZE // 2, TARGET_SIZE // 2)
            outer_radius = TARGET_SIZE // 2
            
            # Real CD hole is 15mm on a 120mm disc (12.5% of diameter, or ~38px)
            inner_radius = int(TARGET_SIZE * 0.0625) 
            
            tracks = list(range(inner_radius, outer_radius, 1))
            total_tracks = len(tracks)
            
            print("\nCalibrating radial laser position...")
            self.progress_start()
            
            # Automatically calculate sleep to maintain exactly ~7 mins total (420 seconds)
            sleep_time = 420.0 / total_tracks if total_tracks else 0
            
            for i, r in enumerate(tracks, 1):
                # Draw faint, semi-transparent tracks
                draw.ellipse(
                    (center[0]-r, center[1]-r, center[0]+r, center[1]+r), 
                    outline=(0, 0, 0, 15)
                )
                time.sleep(sleep_time)
                self.progress(i, total_tracks, "ETCHING")
            
            # 5. Mask the image into a physical disc shape
            mask = Image.new("L", (TARGET_SIZE, TARGET_SIZE), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, TARGET_SIZE, TARGET_SIZE), fill=255) # Outer edge
            mask_draw.ellipse(
                (center[0]-inner_radius, center[1]-inner_radius, center[0]+inner_radius, center[1]+inner_radius), 
                fill=0 # Cut out the inner hole
            )
            
            # 6. Composite the basic disc shape
            final_image = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0,0,0,0))
            final_image.paste(ls_image, (0,0), mask)
            
            # 7. Render Authentic Hub Rings & Manufacturer Matrix
            hub_draw = ImageDraw.Draw(final_image, "RGBA")
            
            # Properly scale the clear stacking ring to 35mm physical equivalent
            stack_r = int(TARGET_SIZE * 0.145)
            hub_draw.ellipse(
                (center[0]-stack_r, center[1]-stack_r, center[0]+stack_r, center[1]+stack_r),
                fill=None, outline=(220, 220, 220, 90), width=4
            )
            
            # Create a thick, reflective silver matrix band (not dark brown!)
            matrix_r = int(TARGET_SIZE * 0.19)
            hub_draw.ellipse(
                (center[0]-matrix_r, center[1]-matrix_r, center[0]+matrix_r, center[1]+matrix_r),
                fill=None, outline=(170, 170, 170, 140), width=24
            )
            
            # Stamp the dark text perfectly centered over the silver matrix band
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            
            if font:
                label_text = self.disk.spec.get("label", "OPTICAL MEDIA").upper()
                matrix_text = f"IFPI L{random.randint(100,999)} - {label_text}"
                
                # Top text math
                bbox = hub_draw.textbbox((0,0), matrix_text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                hub_draw.text(
                    (center[0] - tw//2, center[1] - matrix_r - th//2 - 2), 
                    matrix_text, fill=(30, 25, 20, 230), font=font
                )
                
                # Bottom text math
                bbox2 = hub_draw.textbbox((0,0), "MADE IN JAPAN", font=font)
                tw2 = bbox2[2] - bbox2[0]
                th2 = bbox2[3] - bbox2[1]
                hub_draw.text(
                    (center[0] - tw2//2, center[1] + matrix_r - th2//2 - 2), 
                    "MADE IN JAPAN", fill=(30, 25, 20, 230), font=font
                )
            
            final_image.save(output_path)
            print(f"\n✓ LightScribe label successfully etched to: {output_path}\n")

        except Exception as e:
            print(f"\n?LITESCRIBE FAILED: {e}")

    def cmd_hostls(self, *args):
        path = args[0] if args else "."
        path = os.path.expanduser(path)
        try:
            entries = sorted(os.listdir(path))
            for e in entries:
                full = os.path.join(path, e)
                if os.path.isdir(full):
                    print(f"  {e}/")
                else:
                    sz = os.path.getsize(full)
                    print(f"  {e:<40} {self.fmt_size(sz):>10}")
        except Exception as e:
            print(f"?ERROR: {e}")

    def cmd_cd(self, *args):
        if not args:
            print(os.getcwd())
            return
        try:
            os.chdir(os.path.expanduser(args[0]))
            print(os.getcwd())
        except Exception as e:
            print(f"?ERROR: {e}")

    def cmd_pwd(self, *args):
        print(os.getcwd())

    def prompt(self) -> str:
        if self.active and self.disk:
            label = self.disk.label[:12]
            icon = "CDA" if self.disk.is_audio else "DATA"
            return f"[{self.active}:{label} ({icon})] > "
        return "(no drive) > "

    def run(self):
        print("""
╔══════════════════════════════════════════════════════╗
║        RETROMEDIA ULTIMATE - VIRTUAL MEDIA           ║
║  Data Disks • Audio CDs (CD-DA) • Fixed Drives Rig   ║
╚══════════════════════════════════════════════════════╝
Type HELP for commands, MEDIA for media types.
""")
        commands = {
            "HELP": self.cmd_help, "?": self.cmd_help,
            "MEDIA": self.cmd_media, "CREATE": self.cmd_create,
            "LOAD": self.cmd_load, "INSERT": self.cmd_load, "MOUNT": self.cmd_load,
            "EJECT": self.cmd_eject, "UMOUNT": self.cmd_eject,
            "INFO": self.cmd_info, "STAT": self.cmd_info,
            "ENGINE": self.cmd_engine,
            "BUFFER": self.cmd_buffer, "HOSTRATE": self.cmd_hostrate,
            "DIR": self.cmd_dir, "LS": self.cmd_dir,
            "COPY": self.cmd_copy, "WRITE": self.cmd_copy,
            "ADD": self.cmd_add_track, "BURN": self.cmd_add_track,
            "PLAY": self.play, "EXTRACT": self.cmd_extract,
            "CLONE": self.cmd_clone, "RIP": self.cmd_rip,
            "DELETE": self.cmd_delete, "RM": self.cmd_delete,
            "FORMAT": self.cmd_format, "FINALIZE": self.cmd_finalize,
            "CLOSE": self.cmd_finalize, "PROTECTION": self.cmd_protection,
            "LITESCRIBE": self.cmd_litescribe, "PIRATE": self.cmd_pirate,
            "ARTIST": self.cmd_artist, "ALBUM": self.cmd_album,
            "BURN-PROOF": self.cmd_burnproof, "JUSTLINK": self.cmd_justlink,
            "OVERBURN": self.cmd_overburn,
            "ATTACH": self.cmd_attach, "DETACH": self.cmd_detach,
            "USE": self.cmd_use, "DRIVES": self.cmd_drives,
            "HARDWARE": self.cmd_hardware,
            "XFER": self.cmd_xfer, "XMOVE": self.cmd_xmove,
            "HOSTLS": self.cmd_hostls, "CD": self.cmd_cd, "PWD": self.cmd_pwd,
        }

        while True:
            try:
                line = input(self.prompt()).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                continue
            try:
                parts = shlex.split(line)
            except ValueError as e:
                print(f"?PARSE ERROR: {e}")
                continue

            cmd, args = parts[0].upper(), parts[1:]
            if cmd == "LIST" and args and args[0].upper() == "DRIVES":
                self.cmd_drives(*args[1:])
                continue

            if cmd in ("QUIT", "EXIT", "BYE"):
                if self.disk:
                    self.cmd_eject()
                print("Goodbye!")
                break

            handler = commands.get(cmd)
            if handler:
                try:
                    handler(*args)
                except Exception as e:
                    print(f"?ERROR: {e}")
            else:
                print(f"?UNKNOWN COMMAND: {cmd} (type HELP)")


def main():
    parser = argparse.ArgumentParser(description="RetroMedia Ultimate - virtual media and Audio CD emulator")
    parser.add_argument("disk", nargs="?", help="Medium file to auto-load")
    args = parser.parse_args()

    shell = Shell()
    if args.disk:
        shell.cmd_load(args.disk)
    shell.run()


if __name__ == "__main__":
    main()
