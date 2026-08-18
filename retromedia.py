#!/usr/bin/env python3
"""
RetroMedia - Virtual removable media emulator
Copyright (c) 2026 Chris McGimpsey-Jones
Released under the MIT License
https://github.com/fpucore/retromedia

Authentic capacities, transfer speeds, write buffering, and vintage behavior.
"""

"""
RetroMedia is intentionally a virtual-media/container utility.  It does not
write physical discs.  Optical media use a real bounded write buffer in the
simulation, with optional Burn-Proof/JustLink-style underrun protection.

In addition to removable media, RetroMedia emulates fixed storage: vintage
MFM/RLL/IDE hard disks, modern SATA magnetic disks, SATA SSDs, and NVMe
drives.  Multiple drives can be attached at once in a "rig", and files can be
transferred between them with physically-plausible timing.

Usage:
  python3 retromedia.py
"""

import os
import sys
import json
import time
import struct
import argparse
import shlex
import tempfile
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ====
# Media specifications
# size       = virtual media capacity in bytes
# read/write = simulated sustained transfer rate in bytes/sec
# seek_ms    = initial seek/spin-up/load delay (0 == no mechanical delay)
# theatrics  = whether mechanical spin-up/seek animation is played
#              (defaults to True for legacy entries via .get())
# ====

KB = 1024
MB = 1024 * KB
GB = 1024 * MB

MEDIA_SPECS = {
    # ----
    # Floppy
    # ----
    "5.25-360k": {
        "size": 360 * KB, "read": 25_600, "write": 22_500,
        "seek_ms": 200, "buffer": 0, "label": '5.25" DD 360K',
        "family": "floppy", "recordable": True, "rewritable": True,
    },
    "5.25-1.2m": {
        "size": 1200 * KB, "read": 51_200, "write": 46_000,
        "seek_ms": 100, "buffer": 0, "label": '5.25" HD 1.2M',
        "family": "floppy", "recordable": True, "rewritable": True,
    },
    "3.5-720k": {
        "size": 720 * KB, "read": 30_720, "write": 25_600,
        "seek_ms": 150, "buffer": 0, "label": '3.5" DD 720K',
        "family": "floppy", "recordable": True, "rewritable": True,
    },
    "3.5-1.44m": {
        "size": 1440 * KB, "read": 63_488, "write": 56_320,
        "seek_ms": 90, "buffer": 0, "label": '3.5" HD 1.44M',
        "family": "floppy", "recordable": True, "rewritable": True,
    },
    "3.5-2.88m": {
        "size": 2880 * KB, "read": 102_400, "write": 92_160,
        "seek_ms": 80, "buffer": 0, "label": '3.5" ED 2.88M',
        "family": "floppy", "recordable": True, "rewritable": True,
    },

    # ----
    # Zip
    # ----
    "zip-100": {
        "size": 100 * MB, "read": 1_400_000, "write": 1_000_000,
        "seek_ms": 29, "buffer": 0, "label": "Zip 100",
        "family": "magnetic", "recordable": True, "rewritable": True,
    },
    "zip-250": {
        "size": 250 * MB, "read": 2_400_000, "write": 1_500_000,
        "seek_ms": 29, "buffer": 0, "label": "Zip 250",
        "family": "magnetic", "recordable": True, "rewritable": True,
    },

    # ----
    # CD
    # ----
    "cd-r-650": {
        "size": 650 * MB, "read": 153_600, "write": 153_600,
        "seek_ms": 2000, "buffer": 2 * MB, "label": "CD-R 1x (650MB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "cd-r-700": {
        "size": 700 * MB, "read": 153_600, "write": 153_600,
        "seek_ms": 2000, "buffer": 2 * MB, "label": "CD-R 1x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "cd-rw-700": {
        "size": 700 * MB, "read": 1_228_800, "write": 614_400,
        "seek_ms": 2000, "buffer": 2 * MB, "label": "CD-RW 4x (700MB)",
        "family": "optical", "recordable": True, "rewritable": True,
    },

    # Legacy aliases retained from the original RetroMedia interface.
    "cd-1x": {
        "size": 650 * MB, "read": 153_600, "write": 153_600,
        "seek_ms": 2000, "buffer": 2 * MB, "label": "CD-R 1x (650MB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "cd-2x": {
        "size": 650 * MB, "read": 307_200, "write": 307_200,
        "seek_ms": 2000, "buffer": 2 * MB, "label": "CD-R 2x (650MB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "cd-4x": {
        "size": 650 * MB, "read": 614_400, "write": 614_400,
        "seek_ms": 1500, "buffer": 2 * MB, "label": "CD-R 4x (650MB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "cd-8x": {
        "size": 700 * MB, "read": 1_228_800, "write": 1_228_800,
        "seek_ms": 1500, "buffer": 2 * MB, "label": "CD-R 8x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "cd-16x": {
        "size": 700 * MB, "read": 2_457_600, "write": 2_457_600,
        "seek_ms": 1000, "buffer": 2 * MB, "label": "CD-R 16x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "cd-32x": {
        "size": 700 * MB, "read": 4_915_200, "write": 4_915_200,
        "seek_ms": 1000, "buffer": 2 * MB, "label": "CD-R 32x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "cd-52x": {
        "size": 700 * MB, "read": 7_987_200, "write": 7_987_200,
        "seek_ms": 1000, "buffer": 2 * MB, "label": "CD-R 52x (700MB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },

    # ----
    # DVD: single-layer and dual-layer
    # ----
    "dvd-r": {
        "size": 4_700_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1200, "buffer": 4 * MB, "label": "DVD-R 1x (4.7GB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "dvd+r": {
        "size": 4_700_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1200, "buffer": 4 * MB, "label": "DVD+R 1x (4.7GB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "dvd-rw": {
        "size": 4_700_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1200, "buffer": 4 * MB, "label": "DVD-RW 1x (4.7GB)",
        "family": "optical", "recordable": True, "rewritable": True,
    },
    "dvd+rw": {
        "size": 4_700_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1200, "buffer": 4 * MB, "label": "DVD+RW 1x (4.7GB)",
        "family": "optical", "recordable": True, "rewritable": True,
    },
    "dvd-r-dl": {
        "size": 8_500_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1800, "buffer": 4 * MB, "label": "DVD-R DL 1x (8.5GB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "dvd+r-dl": {
        "size": 8_500_000_000, "read": 11_080_000, "write": 1_385_000,
        "seek_ms": 1800, "buffer": 4 * MB, "label": "DVD+R DL 1x (8.5GB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "dvd-ram-2.6": {
        "size": 2_600_000_000, "read": 5_540_000, "write": 1_385_000,
        "seek_ms": 1000, "buffer": 2 * MB, "label": "DVD-RAM 2.6GB",
        "family": "optical", "recordable": True, "rewritable": True,
    },
    "dvd-ram-5.2": {
        "size": 5_200_000_000, "read": 5_540_000, "write": 1_385_000,
        "seek_ms": 1400, "buffer": 2 * MB, "label": "DVD-RAM 5.2GB (double-sided)",
        "family": "optical", "recordable": True, "rewritable": True,
    },
    "dvd-ram-4.7": {
        "size": 4_700_000_000, "read": 11_080_000, "write": 2_770_000,
        "seek_ms": 1200, "buffer": 4 * MB, "label": "DVD-RAM 4.7GB",
        "family": "optical", "recordable": True, "rewritable": True,
    },
    "dvd-ram-9.4": {
        "size": 9_400_000_000, "read": 11_080_000, "write": 2_770_000,
        "seek_ms": 1600, "buffer": 4 * MB, "label": "DVD-RAM 9.4GB (double-sided)",
        "family": "optical", "recordable": True, "rewritable": True,
    },

    # ----
    # HD DVD
    # ----
    "hd-dvd-r": {
        "size": 15 * GB, "read": 18_280_000, "write": 4_570_000,
        "seek_ms": 1800, "buffer": 8 * MB, "label": "HD DVD-R 1x (15GB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "hd-dvd-r-dl": {
        "size": 30 * GB, "read": 18_280_000, "write": 4_570_000,
        "seek_ms": 2400, "buffer": 8 * MB, "label": "HD DVD-R DL 1x (30GB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "hd-dvd-rw": {
        "size": 15 * GB, "read": 18_280_000, "write": 4_570_000,
        "seek_ms": 1800, "buffer": 8 * MB, "label": "HD DVD-RW 1x (15GB)",
        "family": "optical", "recordable": True, "rewritable": True,
    },
    "hd-dvd-rw-dl": {
        "size": 30 * GB, "read": 18_280_000, "write": 4_570_000,
        "seek_ms": 2400, "buffer": 8 * MB, "label": "HD DVD-RW DL 1x (30GB)",
        "family": "optical", "recordable": True, "rewritable": True,
    },
    "hd-dvd-ram": {
        "size": 20 * GB, "read": 18_280_000, "write": 4_570_000,
        "seek_ms": 1800, "buffer": 8 * MB, "label": "HD DVD-RAM 20GB",
        "family": "optical", "recordable": True, "rewritable": True,
    },

    # ----
    # Blu-ray
    # ----
    "bd-r": {
        "size": 25 * GB, "read": 36_000_000, "write": 4_500_000,
        "seek_ms": 1800, "buffer": 8 * MB, "label": "BD-R 1x (25GB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "bd-re": {
        "size": 25 * GB, "read": 36_000_000, "write": 4_500_000,
        "seek_ms": 1800, "buffer": 8 * MB, "label": "BD-RE 1x (25GB)",
        "family": "optical", "recordable": True, "rewritable": True,
    },
    "bd-r-dl": {
        "size": 50 * GB, "read": 72_000_000, "write": 9_000_000,
        "seek_ms": 2400, "buffer": 8 * MB, "label": "BD-R DL 2x (50GB)",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "bd-re-dl": {
        "size": 50 * GB, "read": 72_000_000, "write": 9_000_000,
        "seek_ms": 2400, "buffer": 8 * MB, "label": "BD-RE DL 2x (50GB)",
        "family": "optical", "recordable": True, "rewritable": True,
    },
    "bd-r-xl": {
        "size": 100 * GB, "read": 72_000_000, "write": 9_000_000,
        "seek_ms": 3200, "buffer": 16 * MB, "label": "BD-R XL 100GB",
        "family": "optical", "recordable": True, "rewritable": False,
    },
    "bd-re-xl": {
        "size": 100 * GB, "read": 72_000_000, "write": 9_000_000,
        "seek_ms": 3200, "buffer": 16 * MB, "label": "BD-RE XL 100GB",
        "family": "optical", "recordable": True, "rewritable": True,
    },
    "bd-r-ql": {
        "size": 128 * GB, "read": 72_000_000, "write": 9_000_000,
        "seek_ms": 3600, "buffer": 16 * MB, "label": "BD-R QL 128GB",
        "family": "optical", "recordable": True, "rewritable": False,
    },

    # ----
    # MiniDisc / Hi-MD
    # ----
    "minidisc-60": {
        "size": 219 * MB, "read": 156_250, "write": 156_250,
        "seek_ms": 500, "buffer": 256 * KB, "label": "MiniDisc 60 min",
        "family": "minidisc", "recordable": True, "rewritable": True,
    },
    "minidisc-74": {
        "size": 270 * MB, "read": 156_250, "write": 156_250,
        "seek_ms": 500, "buffer": 256 * KB, "label": "MiniDisc 74 min",
        "family": "minidisc", "recordable": True, "rewritable": True,
    },
    "minidisc-80": {
        "size": 291 * MB, "read": 156_250, "write": 156_250,
        "seek_ms": 500, "buffer": 256 * KB, "label": "MiniDisc 80 min",
        "family": "minidisc", "recordable": True, "rewritable": True,
    },
    "hi-md-305": {
        "size": 305 * MB, "read": 546_250, "write": 546_250,
        "seek_ms": 600, "buffer": 512 * KB, "label": "Hi-MD 305MB",
        "family": "minidisc", "recordable": True, "rewritable": True,
    },
    "hi-md-1g": {
        "size": 1 * GB, "read": 1_228_750, "write": 1_228_750,
        "seek_ms": 700, "buffer": 1 * MB, "label": "Hi-MD 1GB",
        "family": "minidisc", "recordable": True, "rewritable": True,
    },

    # ----
    # Vintage hard disks (MFM / RLL / early IDE era)
    # ----
    "st-506": {
        "size": 5 * MB, "read": 625_000, "write": 625_000,
        "seek_ms": 150, "buffer": 0, "label": "ST-506 5MB MFM",
        "family": "hdd-vintage", "recordable": True, "rewritable": True,
        "theatrics": True,
    },
    "st-225": {
        "size": 20 * MB, "read": 625_000, "write": 625_000,
        "seek_ms": 65, "buffer": 0, "label": "ST-225 20MB MFM",
        "family": "hdd-vintage", "recordable": True, "rewritable": True,
        "theatrics": True,
    },
    "st-251": {
        "size": 40 * MB, "read": 937_500, "write": 937_500,
        "seek_ms": 40, "buffer": 0, "label": "ST-251 40MB MFM",
        "family": "hdd-vintage", "recordable": True, "rewritable": True,
        "theatrics": True,
    },
    "wd-93028": {
        "size": 20 * MB, "read": 1_250_000, "write": 1_250_000,
        "seek_ms": 40, "buffer": 0, "label": "WD 93028 20MB RLL",
        "family": "hdd-vintage", "recordable": True, "rewritable": True,
        "theatrics": True,
    },
    "wd-caviar": {
        "size": 170 * MB, "read": 5_242_880, "write": 5_242_880,
        "seek_ms": 12, "buffer": 256 * KB, "label": "WD Caviar 170MB IDE",
        "family": "hdd-vintage", "recordable": True, "rewritable": True,
        "theatrics": True,
    },
    "ibm-deskstar-16": {
        "size": 16 * GB, "read": 14 * MB, "write": 14 * MB,
        "seek_ms": 9, "buffer": 512 * KB, "label": "IBM Deskstar 16GB ATA-33",
        "family": "hdd-vintage", "recordable": True, "rewritable": True,
        "theatrics": True,
    },
    "quantum-bigfoot": {
        "size": 12 * GB, "read": 13 * MB, "write": 13 * MB,
        "seek_ms": 12, "buffer": 256 * KB, "label": "Quantum Bigfoot 12GB ATA",
        "family": "hdd-vintage", "recordable": True, "rewritable": True,
        "theatrics": True,
    },

    # ----
    # Modern magnetic hard disks (spinning SATA)
    # ----
    "hdd-sata-1t": {
        "size": 1000 * GB, "read": 160 * MB, "write": 160 * MB,
        "seek_ms": 8, "buffer": 32 * MB, "label": "SATA HDD 1TB 7200RPM",
        "family": "hdd-modern", "recordable": True, "rewritable": True,
        "theatrics": True,
    },
    "hdd-sata-4t": {
        "size": 4000 * GB, "read": 190 * MB, "write": 190 * MB,
        "seek_ms": 8, "buffer": 64 * MB, "label": "SATA HDD 4TB 7200RPM",
        "family": "hdd-modern", "recordable": True, "rewritable": True,
        "theatrics": True,
    },
    "hdd-sata-8t": {
        "size": 8000 * GB, "read": 220 * MB, "write": 200 * MB,
        "seek_ms": 8, "buffer": 256 * MB, "label": "SATA HDD 8TB 7200RPM",
        "family": "hdd-modern", "recordable": True, "rewritable": True,
        "theatrics": True,
    },

    # ----
    # SATA SSD (no mechanical delay)
    # ----
    "ssd-sata-250": {
        "size": 250 * GB, "read": 550 * MB, "write": 520 * MB,
        "seek_ms": 0, "buffer": 0, "label": "SATA SSD 250GB",
        "family": "ssd", "recordable": True, "rewritable": True,
        "theatrics": False,
    },
    "ssd-sata-1t": {
        "size": 1000 * GB, "read": 560 * MB, "write": 530 * MB,
        "seek_ms": 0, "buffer": 0, "label": "SATA SSD 1TB",
        "family": "ssd", "recordable": True, "rewritable": True,
        "theatrics": False,
    },
    "ssd-sata-4t": {
        "size": 4000 * GB, "read": 560 * MB, "write": 540 * MB,
        "seek_ms": 0, "buffer": 0, "label": "SATA SSD 4TB",
        "family": "ssd", "recordable": True, "rewritable": True,
        "theatrics": False,
    },

    # ----
    # NVMe (no mechanical delay)
    # ----
    "nvme-m2-500": {
        "size": 500 * GB, "read": 3_500 * MB, "write": 3_000 * MB,
        "seek_ms": 0, "buffer": 0, "label": "NVMe M.2 500GB Gen3",
        "family": "nvme", "recordable": True, "rewritable": True,
        "theatrics": False,
    },
    "nvme-m2-1t": {
        "size": 1000 * GB, "read": 3_500 * MB, "write": 3_000 * MB,
        "seek_ms": 0, "buffer": 0, "label": "NVMe M.2 1TB Gen3",
        "family": "nvme", "recordable": True, "rewritable": True,
        "theatrics": False,
    },
    "nvme-m2-2t": {
        "size": 2000 * GB, "read": 7_000 * MB, "write": 6_500 * MB,
        "seek_ms": 0, "buffer": 0, "label": "NVMe M.2 2TB Gen4",
        "family": "nvme", "recordable": True, "rewritable": True,
        "theatrics": False,
    },
    "nvme-m2-4t": {
        "size": 4000 * GB, "read": 7_400 * MB, "write": 7_000 * MB,
        "seek_ms": 0, "buffer": 0, "label": "NVMe M.2 4TB Gen4",
        "family": "nvme", "recordable": True, "rewritable": True,
        "theatrics": False,
    },
}


# Order in which media families are displayed / grouped.
FAMILY_ORDER = [
    "floppy",
    "magnetic",
    "optical",
    "minidisc",
    "hdd-vintage",
    "hdd-modern",
    "ssd",
    "nvme",
]

FAMILY_TITLES = {
    "floppy": "FLOPPY",
    "magnetic": "MAGNETIC (ZIP)",
    "optical": "OPTICAL (CD / DVD / HD DVD / BLU-RAY)",
    "minidisc": "MINIDISC / HI-MD",
    "hdd-vintage": "VINTAGE HARD DISKS (MFM / RLL / IDE)",
    "hdd-modern": "MODERN HARD DISKS (SATA)",
    "ssd": "SOLID STATE DRIVES (SATA SSD)",
    "nvme": "NVMe DRIVES",
}

# Families whose members show a spin-up/seek animation column in MEDIA.
THEATRICS_FAMILIES = ("hdd-vintage", "hdd-modern", "ssd", "nvme")

# Families that get mechanical load/eject theatrics.
MECHANICAL_FAMILIES = (
    "floppy", "optical", "minidisc", "hdd-vintage", "hdd-modern",
)


def spec_theatrics(spec: dict) -> bool:
    """Whether a media spec plays spin-up / seek theatrics.

    Legacy entries without the key default to True (safe for mechanical
    media).  SSD/NVMe explicitly set theatrics=False.
    """
    return spec.get("theatrics", True)



# ====
# Container format
# ====
# Header:
#   8 bytes: magic
#   2 bytes: version
#   2 bytes: header_len
#   N bytes: JSON header
#   4 bytes: TOC length
#   N bytes: TOC JSON
#   raw file data
#
# The container remains deliberately simple and backwards-compatible
# with the original RetroMedia format.  Fixed-storage media (HDD/SSD/NVMe)
# use exactly the same container: the data blob starts empty and grows only
# as files are written, so the host file stays sparse and is never
# pre-allocated to the full virtual capacity.
# ====

MAGIC = b"RETROFD\x01"
VERSION = 1


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
        self.created: str = ""
        self.write_protect: bool = False
        self.finalized: bool = False
        self.toc: Dict[str, dict] = {}
        self.data_blob: bytearray = bytearray()
        self.loaded = False

    # --- Creation ----
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
        d.finalized = False
        d.toc = {}
        # Sparse allocation: the data blob starts empty and only grows as
        # files are written.  Nothing is pre-allocated to full capacity,
        # even for multi-terabyte HDD/SSD/NVMe media.
        d.data_blob = bytearray()
        d.loaded = True
        d.save()

        return d

    # --- Persistence ----
    def save(self):
        header_obj = {
            "media": self.media,
            "size": self.size,
            "label": self.label,
            "created": self.created,
            "write_protect": self.write_protect,
            "finalized": self.finalized,
        }

        header_json = json.dumps(header_obj).encode("utf-8")
        toc_json = json.dumps(self.toc).encode("utf-8")

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

            if magic != MAGIC:
                raise MediaError("Not a RetroMedia disk file")

            version = struct.unpack("<H", f.read(2))[0]

            if version > VERSION:
                raise MediaError(f"Unsupported disk version {version}")

            hdr_len = struct.unpack("<H", f.read(2))[0]
            header = json.loads(f.read(hdr_len).decode("utf-8"))

            self.media = header["media"]
            self.size = header["size"]
            self.label = header["label"]
            self.created = header["created"]
            self.write_protect = header.get("write_protect", False)

            # Backwards compatibility:
            # Old RetroMedia containers do not contain this field.
            self.finalized = header.get("finalized", False)

            toc_len = struct.unpack("<I", f.read(4))[0]
            self.toc = json.loads(f.read(toc_len).decode("utf-8"))
            self.data_blob = bytearray(f.read())

        if self.media not in MEDIA_SPECS:
            raise MediaError(
                f"Media type '{self.media}' is not supported by this version"
            )

        self.loaded = True

    # --- Capacity ----
    @property
    def used(self) -> int:
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

    # --- File ops ----
    def list_files(self) -> List[Tuple[str, int, str]]:
        return [
            (name, e["size"], e["added"])
            for name, e in sorted(self.toc.items())
        ]

    def has_file(self, name: str) -> bool:
        return name in self.toc

    def read_file_bytes(self, name: str) -> bytes:
        """Return the raw stored bytes for a file (no throttling)."""
        if name not in self.toc:
            raise MediaError(f"FILE NOT FOUND: {name}")

        entry = self.toc[name]
        offset = entry["offset"]
        size = entry["size"]
        return bytes(self.data_blob[offset:offset + size])

    def add_file(
        self,
        src_path: str,
        dest_name: Optional[str] = None,
        progress_cb=None,
        protection: Optional[str] = None,
        host_rate: Optional[int] = None,
    ) -> None:
        if self.write_protect:
            raise MediaError("DISK IS WRITE-PROTECTED")

        if self.finalized:
            raise MediaError("MEDIUM IS FINALIZED")

        if not os.path.isfile(src_path):
            raise MediaError(f"Source file not found: {src_path}")

        size = os.path.getsize(src_path)

        if size > self.free:
            raise MediaError(
                f"NOT ENOUGH SPACE: need {size:,} bytes, "
                f"have {self.free:,} free"
            )

        name = dest_name or os.path.basename(src_path)

        if name in self.toc:
            raise MediaError(f"FILE EXISTS: {name}")

        spec = self.spec
        offset = len(self.data_blob)
        original_blob_len = len(self.data_blob)

        try:
            self._throttled_copy(
                src_path,
                size,
                spec["write"],
                spec["seek_ms"],
                write_mode=True,
                progress_cb=progress_cb,
                buffer_size=spec.get("buffer", 0),
                protection=protection,
                host_rate=host_rate,
            )
        except Exception:
            # A failed write must not leave orphaned bytes in the
            # virtual medium. This is especially important for
            # buffer underruns.
            del self.data_blob[original_blob_len:]
            raise

        self.toc[name] = {
            "size": size,
            "offset": offset,
            "added": datetime.now().isoformat(timespec="seconds"),
        }

        self.save()

    def extract_file(
        self,
        name: str,
        dest_path: str,
        progress_cb=None,
        host_rate: Optional[int] = None,
    ) -> None:
        if name not in self.toc:
            raise MediaError(f"FILE NOT FOUND: {name}")

        entry = self.toc[name]
        size = entry["size"]
        offset = entry["offset"]
        spec = self.spec

        data = bytes(
            self.data_blob[offset:offset + size]
        )

        self._throttled_copy(
            None,
            size,
            spec["read"],
            spec["seek_ms"],
            write_mode=False,
            progress_cb=progress_cb,
            data=data,
            dest_path=dest_path,
            host_rate=host_rate,
        )

    def delete_file(self, name: str) -> None:
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

            chunk = bytes(
                self.data_blob[
                    entry["offset"]:
                    entry["offset"] + entry["size"]
                ]
            )

            new_toc[fname] = {
                "size": entry["size"],
                "offset": len(new_blob),
                "added": entry["added"],
            }

            new_blob.extend(chunk)

        self.data_blob = new_blob
        self.toc = new_toc
        self.save()

    def format(self) -> None:
        if self.write_protect:
            raise MediaError("DISK IS WRITE-PROTECTED")

        if self.finalized and not self.spec["rewritable"]:
            raise MediaError(
                "WRITE-ONCE MEDIUM IS FINALIZED AND CANNOT BE FORMATTED"
            )

        self.toc = {}
        self.data_blob = bytearray()

        # Rewritable media can be reused after formatting.
        if self.spec["rewritable"]:
            self.finalized = False

        self.save()

    def finalize(self) -> None:
        if self.write_protect:
            raise MediaError("DISK IS WRITE-PROTECTED")

        if self.finalized:
            raise MediaError("MEDIUM IS ALREADY FINALIZED")

        if self.spec["family"] != "optical":
            raise MediaError(
                "FINALIZE is only available for "
                "CD, DVD, HD DVD, and Blu-ray media"
            )

        if not self.toc:
            raise MediaError("CANNOT FINALIZE: MEDIUM IS EMPTY")

        self.finalized = True
        self.save()

    def set_write_protect(self, on: bool) -> None:
        self.write_protect = on
        self.save()

    # --- Speed / buffer engine ----
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
    ) -> None:
        """
        Simulate media I/O.

        For optical and MiniDisc media, writes use a real bounded bytearray
        as a drive buffer. Source data is read into that buffer in chunks and
        drained into the virtual medium at the simulated media write rate.

        seek_ms:
          The mechanical seek / spin-up delay.  When it is 0 (SSD / NVMe)
          there is no mechanical delay and no SEEK/SPIN-UP animation.

        host_rate:
          Optional host-throughput cap in bytes/sec.  When set, the effective
          transfer rate is min(media_rate, host_rate).

        protection:
          None          - normal buffering, underrun aborts the write
          "burn-proof"  - recover from an underrun by pausing the write
          "justlink"    - same recovery model, named after JustLink
        """
        # Effective rate is capped by the host throughput when configured.
        effective_bps = bytes_per_sec

        if host_rate:
            effective_bps = min(bytes_per_sec, host_rate)

        effective_bps = max(1, effective_bps)

        # Mechanical seek / spin-up.  SSD/NVMe have seek_ms == 0 and skip
        # this block entirely (no sleep, no SEEK/SPIN-UP progress call).
        if seek_ms > 0:
            if progress_cb:
                progress_cb(
                    0,
                    total,
                    "SEEK" if seek_ms < 1000 else "SPIN-UP",
                    0,
                    buffer_size,
                    buffer_size,
                )

            time.sleep(seek_ms / 1000.0)

        if write_mode and buffer_size > 0:
            self._buffered_write(
                src_path=src_path,
                total=total,
                bytes_per_sec=effective_bps,
                buffer_size=buffer_size,
                progress_cb=progress_cb,
                protection=protection,
            )
            return

        chunk = max(512, effective_bps // 10)
        copied = 0
        start = time.monotonic()

        if write_mode:
            # Non-optical media retain the original simple throttled model,
            # but data is now appended as it is "written".
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
                        progress_cb(
                            copied,
                            total,
                            "WRITING",
                            0,
                            0,
                            0,
                        )
        else:
            with open(dest_path, "wb") as out:
                while copied < total:
                    this = min(chunk, total - copied)

                    out.write(
                        data[copied:copied + this]
                    )

                    copied += this

                    target = copied / effective_bps
                    elapsed = time.monotonic() - start

                    if elapsed < target:
                        time.sleep(target - elapsed)

                    if progress_cb:
                        progress_cb(
                            copied,
                            total,
                            "READING",
                            0,
                            0,
                            0,
                        )

    def _buffered_write(
        self,
        src_path: str,
        total: int,
        bytes_per_sec: int,
        buffer_size: int,
        progress_cb=None,
        protection: Optional[str] = None,
    ) -> None:
        """
        Actual bounded write buffer.

        The buffer never contains more than buffer_size bytes. Data is
        appended to the virtual medium only as the simulated recorder drains
        the buffer. This is deliberately small, so the buffer displayed by
        RetroMedia is the same buffer used by the write engine.
        """
        buffer = bytearray()
        copied = 0
        written = 0
        start = time.monotonic()
        last_tick = time.monotonic()

        # Use reasonably small producer chunks. The buffer itself remains
        # the hard upper bound.
        producer_chunk = max(
            32 * KB,
            min(buffer_size, 256 * KB)
        )

        with open(src_path, "rb") as src:
            while written < total:

                # Fill the physical-model buffer until full or until
                # source data is exhausted.
                if copied < total and len(buffer) < buffer_size:
                    want = min(
                        producer_chunk,
                        buffer_size - len(buffer),
                        total - copied,
                    )

                    block = src.read(want)

                    if not block:
                        raise MediaError("SOURCE READ FAILED")

                    buffer.extend(block)
                    copied += len(block)

                # If there is nothing to write, we have reached EOF.
                if not buffer:
                    if copied >= total:
                        break

                    # The producer failed to supply data before the recorder
                    # ran dry. This is a real buffer underrun condition.
                    if protection:
                        if progress_cb:
                            progress_cb(
                                written,
                                total,
                                "BUFFER-RECOVERY",
                                0,
                                buffer_size,
                                copied,
                            )

                        time.sleep(0.25)
                        continue

                    raise BufferUnderrun(
                        "BUFFER UNDERRUN: recording stopped "
                        "(enable BURN-PROOF or JUSTLINK)"
                    )

                # Drain one recorder chunk at the media's actual write rate.
                drain = min(
                    len(buffer),
                    max(1, bytes_per_sec // 20),
                    total - written,
                )

                block = bytes(buffer[:drain])
                del buffer[:drain]

                self.data_blob.extend(block)
                written += drain

                # This sleep represents the physical write time.
                time.sleep(drain / bytes_per_sec)

                now = time.monotonic()

                if progress_cb and (
                    now - last_tick >= 0.05 or written >= total
                ):
                    progress_cb(
                        written,
                        total,
                        "WRITING",
                        len(buffer),
                        buffer_size,
                        copied,
                    )

                    last_tick = now

        if written != total:
            raise MediaError(
                f"WRITE FAILED: expected {total} bytes, "
                f"wrote {written}"
            )



# ====
# CLI / Shell
# ====
class Shell:
    def __init__(self):
        # Multi-drive "rig": a set of named slots, each holding a VirtualDisk.
        self.drives: Dict[str, VirtualDisk] = {}
        self.active: Optional[str] = None
        self.burn_proof = False
        self.justlink = False
        # Optional host-throughput cap in bytes/sec (None == unlimited).
        self.host_rate: Optional[int] = None

    # ---- backward-compatible single-disk accessors ----
    @property
    def disk(self) -> Optional[VirtualDisk]:
        return self.drives.get(self.active) if self.active else None

    @property
    def disk_path(self) -> Optional[str]:
        d = self.drives.get(self.active) if self.active else None
        return d.path if d else None

    # ---- helpers ----
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

    def _select_new_active(self) -> None:
        """Pick a new active slot after the current one disappears."""
        if self.active in self.drives:
            return

        self.active = next(iter(self.drives), None)

    def _play_spinup(self, spec: dict, verb: str = "Spinning up") -> None:
        """Mechanical spin-up / load animation, only for theatrical media."""
        if not spec_theatrics(spec):
            return

        if spec["family"] in ("hdd-vintage", "hdd-modern"):
            label = "Spinning up"
        elif spec["family"] == "floppy":
            label = "Reading disk"
        else:
            label = "Inserting disk"

        print(label, end="", flush=True)

        for _ in range(3):
            time.sleep(0.3)
            print(".", end="", flush=True)

        time.sleep(spec["seek_ms"] / 1000.0)

    def _play_eject(self, spec: dict) -> None:
        """Mechanical eject animation based on the media family."""
        if spec["family"] in ("optical", "minidisc"):
            print("Ejecting", end="", flush=True)

            for _ in range(4):
                time.sleep(0.25)
                print(".", end="", flush=True)

            print(" *clunk*\n")

        elif spec["family"] in ("hdd-vintage", "hdd-modern"):
            print("Spinning down", end="", flush=True)

            for _ in range(3):
                time.sleep(0.25)
                print(".", end="", flush=True)

            print(" *whirr* stopped.\n")

        else:
            print("*click* Ejected.\n")

    # ---- progress ----
    def progress(
        self,
        done: int,
        total: int,
        phase: str,
        buffer_used: int = 0,
        buffer_total: int = 0,
        source_done: int = 0,
    ):
        bar_w = 30

        if phase in ("SEEK", "SPIN-UP"):
            sys.stdout.write(
                f"[{phase:<15}] " + "." * bar_w + " "
            )
            sys.stdout.flush()
            return

        pct = done / total if total else 1
        filled = int(bar_w * pct)

        bar = (
            "█" * filled +
            "░" * (bar_w - filled)
        )

        elapsed = time.monotonic() - getattr(
            self,
            "_t0",
            time.monotonic()
        )

        rate = done / max(0.001, elapsed)

        if phase == "BUFFER-RECOVERY":
            sys.stdout.write(
                f"\r[BUFFER RECOVERY] {bar} {pct*100:5.1f}%  "
                f"Buffer: EMPTY  "
            )

            sys.stdout.flush()
            return

        if buffer_total:
            bpct = (
                buffer_used / buffer_total
                if buffer_total else 0
            )

            bfilled = int(bar_w * bpct)

            bbar = (
                "█" * bfilled +
                "░" * (bar_w - bfilled)
            )

            btext = (
                f"BUFFER [{bbar}] {bpct*100:5.1f}% "
                f"{self.fmt_size(buffer_used)}/"
                f"{self.fmt_size(buffer_total)}"
            )
        else:
            btext = ""

        protection = ""

        if self.burn_proof:
            protection = "  Burn-Proof: ON"
        elif self.justlink:
            protection = "  JustLink: ON"

        sys.stdout.write(
            f"\r[{phase:<10}] {bar} {pct*100:5.1f}%  "
            f"{self.fmt_size(done):>9}/"
            f"{self.fmt_size(total):<9}  "
            f"{self.fmt_size(int(rate))}/s  "
            f"{btext}{protection}"
        )

        sys.stdout.flush()

        if done >= total:
            sys.stdout.write("\n")

    def progress_start(self):
        self._t0 = time.monotonic()

    # ---- commands ----
    def cmd_help(self, *args):
        print("""
RETROMEDIA COMMANDS:

  CREATE <file> <media> [label]   Create a new virtual medium
  LOAD <file>                     Insert (load) a medium
  EJECT                           Eject the current medium
  INFO                            Show medium information
  DIR / LS                        List files on medium
  COPY <src> [name]               Write host file → medium
  EXTRACT <name> [dest]           Read medium file → host
  DELETE / RM <name>              Delete file from medium
  FORMAT                          Erase all files on medium
  FINALIZE                        Close/finalize optical media
  PROTECT ON|OFF                  Toggle write protection
  MEDIA                           List supported media types

  BURN-PROOF ON|OFF               Enable/disable Burn-Proof protection
  JUSTLINK ON|OFF                 Enable/disable JustLink protection
  BUFFER                          Show current recorder settings
  HOSTRATE <KBps>|OFF             Cap host throughput (min with media rate)

DRIVE RIG COMMANDS:
  ATTACH <slot> <file>            Load a drive into the rig
  DETACH <slot>                   Remove a drive from the rig
  DRIVES                          List all attached drives
  USE <slot>                      Switch active drive

CROSS-DRIVE TRANSFER:
  XFER <slot>:<file> <slot>:<file>  Copy file between drives
  XMOVE <slot>:<file> <slot>:<file> Move file between drives

HOST COMMANDS:
  HOSTLS [path]                   List host directory files
  CD <path>                       Change host directory
  PWD                             Show current host directory
  HELP                            Show this help
  QUIT / EXIT                     Leave program

FINALIZE:
  FINALIZE closes a CD, DVD, HD DVD, or Blu-ray medium.
  Finalized media cannot accept further writes.

  Write-once media remain permanently finalized.
  Rewritable optical media can be reformatted and reused.

EXAMPLES:
  CREATE backup.vfd 3.5-1.44m "MY DISK"
  CREATE linux.dvd dvd+r "LINUX INSTALL"
  CREATE archive.bd bd-r-dl "ARCHIVE"
  CREATE music.md minidisc-80 "MIXTAPE"
  CREATE system.hdd st-225 "SYSTEM DISK"
  CREATE fast.nvme nvme-m2-1t "FAST STORE"

  BURN-PROOF ON
  COPY ~/linux.iso
  FINALIZE
  EJECT

  ATTACH floppy0 disk1.vfd
  ATTACH hdd0 system.hdd
  DRIVES
  XFER floppy0:README.TXT hdd0:README.TXT
""")

    def cmd_media(self, *args):
        # Group entries by family in the canonical display order.
        by_family: Dict[str, List[Tuple[str, dict]]] = {}

        for key, spec in MEDIA_SPECS.items():
            by_family.setdefault(spec["family"], []).append((key, spec))

        line_w = 105

        for family in FAMILY_ORDER:
            entries = by_family.get(family)

            if not entries:
                continue

            title = FAMILY_TITLES.get(family, family.upper())
            show_theatrics = family in THEATRICS_FAMILIES

            print()
            dashes = line_w - len(title) - 4

            if dashes < 0:
                dashes = 0

            print(f"── {title} " + "─" * dashes)

            if show_theatrics:
                print(
                    f"{'KEY':<17}{'CAPACITY':>12}{'READ':>13}"
                    f"{'WRITE':>13}{'BUFFER':>10}{'SPIN':>6}  LABEL"
                )
            else:
                print(
                    f"{'KEY':<17}{'CAPACITY':>12}{'READ':>13}"
                    f"{'WRITE':>13}{'BUFFER':>10}  LABEL"
                )

            for key, spec in entries:
                buffer_text = (
                    self.fmt_size(spec["buffer"])
                    if spec["buffer"] else "-"
                )

                if show_theatrics:
                    spin = "YES" if spec_theatrics(spec) else "NO"

                    print(
                        f"{key:<17}"
                        f"{self.fmt_size(spec['size']):>12}"
                        f"{self.fmt_size(spec['read'])+'/s':>13}"
                        f"{self.fmt_size(spec['write'])+'/s':>13}"
                        f"{buffer_text:>10}"
                        f"{spin:>6}  "
                        f"{spec['label']}"
                    )
                else:
                    print(
                        f"{key:<17}"
                        f"{self.fmt_size(spec['size']):>12}"
                        f"{self.fmt_size(spec['read'])+'/s':>13}"
                        f"{self.fmt_size(spec['write'])+'/s':>13}"
                        f"{buffer_text:>10}  "
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
            print(
                f"?UNKNOWN MEDIA: {media}  "
                f"(use MEDIA to list)"
            )
            return

        if os.path.exists(path):
            ans = input(
                f"'{path}' exists. Overwrite? [y/N] "
            ).strip().lower()

            if ans != "y":
                print("Cancelled.")
                return

        try:
            disk = VirtualDisk.create(
                path,
                media,
                label
            )

            spec = MEDIA_SPECS[media]

            print(f"\n✓ CREATED: {path}")
            print(f"  Media:    {spec['label']}")
            print(f"  Capacity: {self.fmt_size(spec['size'])}")
            print(f"  Label:    {disk.label}")
            print(f"  Read:     {self.fmt_size(spec['read'])}/s")
            print(f"  Write:    {self.fmt_size(spec['write'])}/s")

            print(
                f"  Buffer:   {self.fmt_size(spec['buffer'])}"
                if spec["buffer"]
                else "  Buffer:   none"
            )

            print(
                f"  Type:     "
                f"{'REWRITABLE' if spec['rewritable'] else 'WRITE-ONCE'}"
            )

            if spec["family"] in THEATRICS_FAMILIES:
                print(
                    f"  Seek/Spin-up: "
                    f"{'YES' if spec_theatrics(spec) else 'NO'}"
                )

            print("  Finalized: NO")
            print()

        except Exception as e:
            print(f"?CREATE FAILED: {e}")

    def _show_disk_summary(self, d: VirtualDisk, path: str, slot: Optional[str] = None):
        spec = d.spec

        if slot:
            print(f"\n✓ ATTACHED: {path}  →  slot [{slot}]")
        else:
            print(f"\n✓ LOADED: {path}")

        print(f"  Label:     {d.label}")
        print(f"  Media:     {spec['label']}")
        print(f"  Capacity:  {self.fmt_size(d.size)}")
        print(
            f"  Used:      {self.fmt_size(d.used)} "
            f"({d.used/d.size*100:.1f}%)"
        )
        print(f"  Free:      {self.fmt_size(d.free)}")
        print(f"  Files:     {len(d.toc)}")
        print(
            f"  Write-Protected: "
            f"{'YES' if d.write_protect else 'NO'}"
        )
        print(
            f"  Finalized: "
            f"{'YES' if d.finalized else 'NO'}"
        )
        print(
            f"  Buffer:    "
            f"{self.fmt_size(spec['buffer']) if spec['buffer'] else 'none'}"
        )

        if spec["family"] in THEATRICS_FAMILIES:
            print(
                f"  Seek/Spin-up: "
                f"{'YES' if spec_theatrics(spec) else 'NO'}"
            )

        print(f"  Created:   {d.created}\n")

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

            spec = d.spec

            # Legacy single-disk LOAD uses the default "disk0" slot.
            slot = "disk0"

            self.drives[slot] = d
            self.active = slot

            self._play_spinup(spec)

            print()
            self._show_disk_summary(d, path)

        except Exception as e:
            print(f"?LOAD FAILED: {e}")

    def cmd_attach(self, *args):
        if len(args) < 2:
            print("Usage: ATTACH <slot> <file>")
            return

        slot = args[0]
        path = args[1]

        if slot in self.drives:
            print(f"?SLOT OCCUPIED: '{slot}' already has a drive (DETACH first)")
            return

        if not os.path.exists(path):
            print(f"?FILE NOT FOUND: {path}")
            return

        try:
            d = VirtualDisk(path)
            d.load()

            spec = d.spec

            self.drives[slot] = d

            if self.active is None:
                self.active = slot

            self._play_spinup(spec)

            print()
            self._show_disk_summary(d, path, slot=slot)

        except Exception as e:
            print(f"?ATTACH FAILED: {e}")

    def cmd_detach(self, *args):
        if not args:
            print("Usage: DETACH <slot>")
            return

        slot = args[0]

        if slot not in self.drives:
            print(f"?NO SUCH SLOT: {slot}")
            return

        d = self.drives[slot]
        spec = d.spec

        self._play_eject(spec)

        del self.drives[slot]

        if self.active == slot:
            self.active = None
            self._select_new_active()

        print(f"✓ Detached slot [{slot}]")

        if self.active:
            print(f"  Active drive is now [{self.active}]\n")
        else:
            print("  No active drive.\n")

    def cmd_use(self, *args):
        if not args:
            print("Usage: USE <slot>")
            return

        slot = args[0]

        if slot not in self.drives:
            print(f"?NO SUCH SLOT: {slot}")
            return

        self.active = slot
        d = self.drives[slot]

        print(
            f"✓ Active drive: [{slot}]  {d.label}  ({d.spec['label']})\n"
        )

    def cmd_drives(self, *args):
        if not self.drives:
            print("\n  (none attached)\n")
            return

        print(
            f"\n{'SLOT':<10}{'MEDIA':<14}{'LABEL':<16}"
            f"{'CAPACITY':>11}{'USED':>11}{'FREE':>11}"
            f"{'FILES':>7}  ACTIVE"
        )
        print("-" * 92)

        for slot, d in self.drives.items():
            spec = d.spec
            active = "*" if slot == self.active else ""

            print(
                f"{slot:<10}"
                f"{d.media:<14}"
                f"{d.label[:15]:<16}"
                f"{self.fmt_size(d.size):>11}"
                f"{self.fmt_size(d.used):>11}"
                f"{self.fmt_size(d.free):>11}"
                f"{len(d.toc):>7}  {active}"
            )

        print()

    def cmd_eject(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return

        slot = self.active
        spec = self.disk.spec

        self._play_eject(spec)

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

        print(f"\n  Slot:      {self.active}")
        print(f"  Path:      {self.disk_path}")
        print(f"  Label:     {d.label}")
        print(f"  Media:     {spec['label']}")
        print(f"  Capacity:  {self.fmt_size(d.size)}")
        print(
            f"  Used:      {self.fmt_size(d.used)} "
            f"({d.used/d.size*100:.1f}%)"
        )
        print(f"  Free:      {self.fmt_size(d.free)}")
        print(f"  Files:     {len(d.toc)}")
        print(f"  Read:      {self.fmt_size(spec['read'])}/s")
        print(f"  Write:     {self.fmt_size(spec['write'])}/s")
        print(f"  Seek:      {spec['seek_ms']} ms")
        print(
            f"  Buffer:    "
            f"{self.fmt_size(spec['buffer']) if spec['buffer'] else 'none'}"
        )
        print(
            f"  Rewritable:"
            f"{' YES' if spec['rewritable'] else ' NO'}"
        )

        if spec["family"] in THEATRICS_FAMILIES:
            print(
                f"  Seek/Spin-up: "
                f"{'YES' if spec_theatrics(spec) else 'NO'}"
            )

        print(
            f"  Write-Protected: "
            f"{'YES' if d.write_protect else 'NO'}"
        )
        print(
            f"  Finalized: "
            f"{'YES' if d.finalized else 'NO'}"
        )
        print(f"  Created:   {d.created}\n")

    def cmd_buffer(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return

        spec = self.disk.spec

        print("\nRECORDER BUFFER")
        print(f"  Media:       {spec['label']}")
        print(
            f"  Buffer size: "
            f"{self.fmt_size(spec['buffer']) if spec['buffer'] else 'none'}"
        )
        print(
            f"  Burn-Proof:  "
            f"{'ON' if self.burn_proof else 'OFF'}"
        )
        print(
            f"  JustLink:    "
            f"{'ON' if self.justlink else 'OFF'}"
        )
        print(
            f"  Host rate:   "
            f"{self.fmt_size(self.host_rate) + '/s' if self.host_rate else 'unlimited'}"
        )
        print()

    def cmd_hostrate(self, *args):
        if not args:
            cur = (
                f"{self.fmt_size(self.host_rate)}/s"
                if self.host_rate else "unlimited"
            )
            print(f"Host rate: {cur}  (usage: HOSTRATE <KBps>|OFF)")
            return

        val = args[0].upper()

        if val in ("OFF", "NONE", "0", "UNLIMITED"):
            self.host_rate = None
            print("Host rate: unlimited\n")
            return

        try:
            kbps = float(val)

            if kbps <= 0:
                raise ValueError

        except ValueError:
            print("Usage: HOSTRATE <KBps>|OFF")
            return

        self.host_rate = int(kbps * KB)

        print(
            f"Host rate: {self.fmt_size(self.host_rate)}/s "
            f"({kbps:g} KB/s)\n"
        )

    def cmd_dir(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return

        files = self.disk.list_files()
        d = self.disk

        print(f"\n VOLUME: {d.label}")
        print(f" {'NAME':<30}{'SIZE':>14}  ADDED")
        print(" " + "-" * 64)

        if not files:
            print("  <empty medium>")
        else:
            for name, size, added in files:
                print(
                    f"  {name:<30}"
                    f"{self.fmt_size(size):>13}  "
                    f"{added}"
                )

        print(
            f"\n {len(files)} FILE(S)   "
            f"{self.fmt_size(d.used)} USED   "
            f"{self.fmt_size(d.free)} FREE\n"
        )

    def cmd_copy(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return

        if not args:
            print("Usage: COPY <src> [dest_name]")
            return

        src = os.path.expanduser(args[0])
        dest = args[1] if len(args) > 1 else None

        try:
            self.progress_start()

            protection = self.optical_protection()

            self.disk.add_file(
                src,
                dest,
                progress_cb=self.progress,
                protection=protection,
                host_rate=self.host_rate,
            )

            print(
                f"✓ Wrote "
                f"{os.path.basename(dest or src)} "
                f"to disk\n"
            )

        except Exception as e:
            print(f"\n?COPY FAILED: {e}")

    def cmd_extract(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return

        if not args:
            print("Usage: EXTRACT <name> [dest_path]")
            return

        name = args[0]
        dest = (
            os.path.expanduser(args[1])
            if len(args) > 1
            else name
        )

        try:
            self.progress_start()

            self.disk.extract_file(
                name,
                dest,
                progress_cb=self.progress,
                host_rate=self.host_rate,
            )

            print(
                f"✓ Extracted {name} → {dest}\n"
            )

        except Exception as e:
            print(f"\n?EXTRACT FAILED: {e}")

    def _parse_slot_ref(self, ref: str) -> Tuple[str, str]:
        """Parse a 'slot:filename' reference into (slot, filename)."""
        if ":" not in ref:
            raise MediaError(
                f"Invalid reference '{ref}' (expected slot:filename)"
            )

        slot, _, name = ref.partition(":")

        if not slot or not name:
            raise MediaError(
                f"Invalid reference '{ref}' (expected slot:filename)"
            )

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

        if size > dst.free:
            print(
                f"?{verb} FAILED: NOT ENOUGH SPACE on [{dst_slot}]: "
                f"need {size:,} bytes, have {dst.free:,} free"
            )
            return

        if move and (not src.spec["rewritable"] or src.finalized):
            print(
                f"?{verb} FAILED: source is write-once/finalized "
                f"(cannot remove source file)"
            )
            return

        tmp_path = None

        try:
            # --- Read phase: pull the source file off the source drive. ---
            src_spec = src.spec
            dst_spec = dst.spec

            eff = min(src_spec["read"], dst_spec["write"])

            if self.host_rate:
                eff = min(eff, self.host_rate)

            print(
                f"\nTransfer [{src_slot}] → [{dst_slot}]  {src_name}"
            )
            print(
                f"  Source read:  {self.fmt_size(src_spec['read'])}/s"
            )
            print(
                f"  Dest write:   {self.fmt_size(dst_spec['write'])}/s"
            )
            print(
                f"  Effective:    {self.fmt_size(eff)}/s"
                + (
                    f"  (host cap {self.fmt_size(self.host_rate)}/s)"
                    if self.host_rate else ""
                )
            )

            with tempfile.NamedTemporaryFile(delete=False) as tf:
                tmp_path = tf.name

            # READ phase: extract source blob to the temp file at src speed.
            self.progress_start()
            src.extract_file(
                src_name,
                tmp_path,
                progress_cb=lambda *a: self.progress(
                    a[0], a[1],
                    "XFER-READ" if a[2] in ("READING", "WRITING") else a[2],
                    *a[3:]
                ),
                host_rate=self.host_rate,
            )

            # WRITE phase: add the temp file to the destination at dst speed.
            self.progress_start()
            dst.add_file(
                tmp_path,
                dst_name,
                progress_cb=lambda *a: self.progress(
                    a[0], a[1],
                    "XFER-WRITE" if a[2] in ("READING", "WRITING") else a[2],
                    *a[3:]
                ),
                protection=self.optical_protection(),
                host_rate=self.host_rate,
            )

            if move:
                src.delete_file(src_name)
                print(
                    f"✓ Moved {src_name} "
                    f"[{src_slot}] → [{dst_slot}]:{dst_name}\n"
                )
            else:
                print(
                    f"✓ Copied {src_name} "
                    f"[{src_slot}] → [{dst_slot}]:{dst_name}\n"
                )

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

    def cmd_delete(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return

        if not args:
            print("Usage: DELETE <name>")
            return

        try:
            self.disk.delete_file(args[0])
            print(f"✓ Deleted {args[0]}\n")

        except Exception as e:
            print(f"?DELETE FAILED: {e}")

    def cmd_format(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return

        if (
            self.disk.finalized
            and not self.disk.spec["rewritable"]
        ):
            print(
                "?FORMAT FAILED: WRITE-ONCE MEDIUM IS "
                "FINALIZED AND CANNOT BE FORMATTED"
            )
            return

        ans = input(
            f"Format '{self.disk.label}'? "
            f"All files will be erased! [y/N] "
        ).strip().lower()

        if ans != "y":
            print("Cancelled.")
            return

        spec = self.disk.spec

        fmt_time = max(
            2.0,
            self.disk.size / max(1, spec["write"]) / 4
        )

        # Bound formatting theatrics so huge fixed drives do not hang.
        fmt_time = min(fmt_time, 8.0)

        print(
            "Formatting",
            end="",
            flush=True
        )

        steps = min(
            30,
            max(4, int(fmt_time * 2))
        )

        for _ in range(steps):
            time.sleep(
                min(0.5, fmt_time / steps)
            )
            print(".", end="", flush=True)

        try:
            was_finalized = self.disk.finalized

            self.disk.format()

            print("\n✓ Disk formatted.")

            if was_finalized:
                print(
                    "  Finalization cleared; "
                    "medium is writable again."
                )

            print()

        except Exception as e:
            print(f"\n?FORMAT FAILED: {e}")

    def cmd_finalize(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return

        spec = self.disk.spec

        if spec["family"] != "optical":
            print(
                "?FINALIZE is only available for "
                "CD, DVD, HD DVD, and Blu-ray media"
            )
            return

        if self.disk.finalized:
            print("?MEDIUM IS ALREADY FINALIZED")
            return

        if not self.disk.toc:
            print("?CANNOT FINALIZE: MEDIUM IS EMPTY")
            return

        print(f"\nFinalizing '{self.disk.label}'")
        print(f"  Media: {spec['label']}")
        print(
            f"  Data:  {self.fmt_size(self.disk.used)}"
        )
        print(
            "  Writing lead-out",
            end="",
            flush=True
        )

        # Simulate the finalization / lead-out operation.
        #
        # This is intentionally bounded so even very large virtual
        # media do not result in an unreasonable wait.
        finalize_time = max(
            1.0,
            min(
                8.0,
                self.disk.used /
                max(1, spec["write"]) /
                10
            )
        )

        steps = max(
            4,
            min(20, int(finalize_time * 4))
        )

        for _ in range(steps):
            time.sleep(
                finalize_time / steps
            )
            print(".", end="", flush=True)

        try:
            self.disk.finalize()

            print("\n✓ MEDIUM FINALIZED")
            print(
                "  Lead-out written; "
                "medium is now closed."
            )
            print(
                "  No further files can be written."
            )

            if spec["rewritable"]:
                print(
                    "  FORMAT can be used later to "
                    "reuse this rewritable medium."
                )

            print()

        except Exception as e:
            print(f"\n?FINALIZE FAILED: {e}")

    def cmd_protect(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return

        if (
            not args
            or args[0].upper() not in ("ON", "OFF")
        ):
            print("Usage: PROTECT ON|OFF")
            return

        on = args[0].upper() == "ON"

        self.disk.set_write_protect(on)

        print(
            f"Write protection: "
            f"{'ON' if on else 'OFF'}\n"
        )

    def cmd_burnproof(self, *args):
        if (
            not args
            or args[0].upper() not in ("ON", "OFF")
        ):
            print("Usage: BURN-PROOF ON|OFF")
            return

        self.burn_proof = (
            args[0].upper() == "ON"
        )

        if self.burn_proof:
            self.justlink = False

        print(
            f"Burn-Proof: "
            f"{'ON' if self.burn_proof else 'OFF'}\n"
        )

    def cmd_justlink(self, *args):
        if (
            not args
            or args[0].upper() not in ("ON", "OFF")
        ):
            print("Usage: JUSTLINK ON|OFF")
            return

        self.justlink = (
            args[0].upper() == "ON"
        )

        if self.justlink:
            self.burn_proof = False

        print(
            f"JustLink: "
            f"{'ON' if self.justlink else 'OFF'}\n"
        )

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

                    print(
                        f"  {e:<40} "
                        f"{self.fmt_size(sz):>10}"
                    )

        except Exception as e:
            print(f"?ERROR: {e}")

    def cmd_cd(self, *args):
        if not args:
            print(os.getcwd())
            return

        try:
            os.chdir(
                os.path.expanduser(args[0])
            )

            print(os.getcwd())

        except Exception as e:
            print(f"?ERROR: {e}")

    def cmd_pwd(self, *args):
        print(os.getcwd())

    # ---- prompt ----
    def prompt(self) -> str:
        if self.active and self.disk:
            label = self.disk.label[:12]
            return f"[{self.active}:{label}] > "

        return "(no drive) > "

    def run(self):
        print("""
╔══════════════════════════════════════════════════════╗
║            RETROMEDIA - VIRTUAL MEDIA                ║
║     Authentic vintage media & write-buffer model     ║
╚══════════════════════════════════════════════════════╝
Type HELP for commands, MEDIA for media types.
""")

        commands = {
            "HELP": self.cmd_help,
            "?": self.cmd_help,
            "MEDIA": self.cmd_media,
            "CREATE": self.cmd_create,
            "LOAD": self.cmd_load,
            "INSERT": self.cmd_load,
            "MOUNT": self.cmd_load,
            "EJECT": self.cmd_eject,
            "UMOUNT": self.cmd_eject,
            "INFO": self.cmd_info,
            "STAT": self.cmd_info,
            "BUFFER": self.cmd_buffer,
            "HOSTRATE": self.cmd_hostrate,
            "DIR": self.cmd_dir,
            "LS": self.cmd_dir,
            "COPY": self.cmd_copy,
            "WRITE": self.cmd_copy,
            "PUT": self.cmd_copy,
            "EXTRACT": self.cmd_extract,
            "READ": self.cmd_extract,
            "GET": self.cmd_extract,
            "DELETE": self.cmd_delete,
            "DEL": self.cmd_delete,
            "RM": self.cmd_delete,
            "FORMAT": self.cmd_format,
            "FINALIZE": self.cmd_finalize,
            "PROTECT": self.cmd_protect,
            "BURN-PROOF": self.cmd_burnproof,
            "BURNPROOF": self.cmd_burnproof,
            "JUSTLINK": self.cmd_justlink,
            "ATTACH": self.cmd_attach,
            "DETACH": self.cmd_detach,
            "USE": self.cmd_use,
            "DRIVES": self.cmd_drives,
            "XFER": self.cmd_xfer,
            "XMOVE": self.cmd_xmove,
            "HOSTLS": self.cmd_hostls,
            "CD": self.cmd_cd,
            "PWD": self.cmd_pwd,
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

            cmd = parts[0].upper()
            args = parts[1:]

            # Support "LIST DRIVES" as an alias for DRIVES.
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
                print(
                    f"?UNKNOWN COMMAND: {cmd} "
                    f"(type HELP)"
                )


# ====
# Main
# ====
def main():
    parser = argparse.ArgumentParser(
        description="RetroMedia - virtual removable media emulator"
    )

    parser.add_argument(
        "disk",
        nargs="?",
        help="Medium file to auto-load on startup"
    )

    args = parser.parse_args()

    shell = Shell()

    if args.disk:
        shell.cmd_load(args.disk)

    shell.run()


if __name__ == "__main__":
    main()
