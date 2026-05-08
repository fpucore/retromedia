#!/usr/bin/env python3
"""
RetroMedia - Virtual floppy disk and CD-R/CD-ROM emulator
Authentic speeds, capacities, and behavior of vintage storage media.

Usage:
  python3 retromedia.py
"""

import os
import sys
import json
import time
import struct
import hashlib
import argparse
import shlex
import shutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ============================================================
# Media specifications (capacity bytes, read/write B/s, seek ms)
# ============================================================
MEDIA_SPECS = {
    # Floppies
    "5.25-360k":    {"size":   360 * 1024,        "read":  25_600,    "write":  22_500,    "seek_ms": 200, "label": "5.25\" DD 360K"},
    "5.25-1.2m":    {"size":  1200 * 1024,        "read":  51_200,    "write":  46_000,    "seek_ms": 100, "label": "5.25\" HD 1.2M"},
    "3.5-720k":     {"size":   720 * 1024,        "read":  30_720,    "write":  25_600,    "seek_ms": 150, "label": "3.5\" DD 720K"},
    "3.5-1.44m":    {"size":  1440 * 1024,        "read":  63_488,    "write":  56_320,    "seek_ms":  90, "label": "3.5\" HD 1.44M"},
    "3.5-2.88m":    {"size":  2880 * 1024,        "read": 102_400,    "write":  92_160,    "seek_ms":  80, "label": "3.5\" ED 2.88M"},
    "zip-100":      {"size":   100 * 1024 * 1024, "read": 1_400_000,  "write": 1_000_000,  "seek_ms":  29, "label": "Zip 100"},
    "zip-250":      {"size":   250 * 1024 * 1024, "read": 2_400_000,  "write": 1_500_000,  "seek_ms":  29, "label": "Zip 250"},
    # CD media
    "cd-1x":        {"size":   650 * 1024 * 1024, "read": 153_600,    "write": 153_600,    "seek_ms": 2000, "label": "CD-R 1× (650MB)"},
    "cd-2x":        {"size":   650 * 1024 * 1024, "read": 307_200,    "write": 307_200,    "seek_ms": 2000, "label": "CD-R 2× (650MB)"},
    "cd-4x":        {"size":   650 * 1024 * 1024, "read": 614_400,    "write": 614_400,    "seek_ms": 1500, "label": "CD-R 4× (650MB)"},
    "cd-8x":        {"size":   700 * 1024 * 1024, "read": 1_228_800,  "write": 1_228_800,  "seek_ms": 1500, "label": "CD-R 8× (700MB)"},
    "cd-16x":       {"size":   700 * 1024 * 1024, "read": 2_457_600,  "write": 2_457_600,  "seek_ms": 1000, "label": "CD-R 16× (700MB)"},
    "cd-32x":       {"size":   700 * 1024 * 1024, "read": 4_915_200,  "write": 4_915_200,  "seek_ms": 1000, "label": "CD-R 32× (700MB)"},
    "cd-52x":       {"size":   700 * 1024 * 1024, "read": 7_987_200,  "write": 7_987_200,  "seek_ms": 1000, "label": "CD-R 52× (700MB)"},
}


# ============================================================
# Container format
# ============================================================
# Header layout (binary, little-endian):
#   8 bytes:  magic        b"RETROFD\x01"
#   2 bytes:  version      uint16 (currently 1)
#   2 bytes:  header_len   uint16 (length of JSON header)
#   N bytes:  JSON header  {media, size, label, created, write_protect}
#   ----  followed by raw container data ----
#   Container data is itself: [TOC_LEN:u32][TOC_JSON][FILE_DATA...]
#   Files are stored back-to-back; TOC contains {name,size,offset,added}

MAGIC = b"RETROFD\x01"
VERSION = 1


class MediaError(Exception):
    pass


class VirtualDisk:
    def __init__(self, path: str):
        self.path = path
        self.media: Optional[str] = None
        self.size: int = 0
        self.label: str = ""
        self.created: str = ""
        self.write_protect: bool = False
        self.toc: Dict[str, dict] = {}     # filename -> {size, offset, added}
        self.data_blob: bytearray = bytearray()  # in-memory file data
        self.loaded = False

    # --- Creation -----------------------------------------------------
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
        d.toc = {}
        d.data_blob = bytearray()
        d.loaded = True
        d.save()
        return d

    # --- Persistence -------------------------------------------------
    def save(self):
        header_obj = {
            "media": self.media,
            "size": self.size,
            "label": self.label,
            "created": self.created,
            "write_protect": self.write_protect,
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
            toc_len = struct.unpack("<I", f.read(4))[0]
            self.toc = json.loads(f.read(toc_len).decode("utf-8"))
            self.data_blob = bytearray(f.read())
        self.loaded = True

    # --- Capacity ----------------------------------------------------
    @property
    def used(self) -> int:
        return sum(e["size"] for e in self.toc.values())

    @property
    def free(self) -> int:
        return self.size - self.used

    @property
    def spec(self) -> dict:
        return MEDIA_SPECS[self.media]

    # --- File ops ----------------------------------------------------
    def list_files(self) -> List[Tuple[str, int, str]]:
        return [(name, e["size"], e["added"]) for name, e in sorted(self.toc.items())]

    def has_file(self, name: str) -> bool:
        return name in self.toc

    def add_file(self, src_path: str, dest_name: Optional[str] = None,
                 progress_cb=None) -> None:
        if self.write_protect:
            raise MediaError("DISK IS WRITE-PROTECTED")
        if not os.path.isfile(src_path):
            raise MediaError(f"Source file not found: {src_path}")
        size = os.path.getsize(src_path)
        if size > self.free:
            raise MediaError(
                f"NOT ENOUGH SPACE: need {size:,} bytes, have {self.free:,} free"
            )
        name = dest_name or os.path.basename(src_path)
        if name in self.toc:
            raise MediaError(f"FILE EXISTS: {name}")

        # Throttled write
        spec = self.spec
        offset = len(self.data_blob)
        self._throttled_copy(src_path, size, spec["write"], spec["seek_ms"],
                             write_mode=True, progress_cb=progress_cb)

        # Re-read file into our blob (already throttled the visible copy)
        with open(src_path, "rb") as f:
            self.data_blob.extend(f.read())

        self.toc[name] = {
            "size": size,
            "offset": offset,
            "added": datetime.now().isoformat(timespec="seconds"),
        }
        self.save()

    def extract_file(self, name: str, dest_path: str, progress_cb=None) -> None:
        if name not in self.toc:
            raise MediaError(f"FILE NOT FOUND: {name}")
        entry = self.toc[name]
        size = entry["size"]
        offset = entry["offset"]
        spec = self.spec

        # Throttled read with progress
        data = bytes(self.data_blob[offset:offset + size])
        self._throttled_copy(None, size, spec["read"], spec["seek_ms"],
                             write_mode=False, progress_cb=progress_cb,
                             data=data, dest_path=dest_path)

    def delete_file(self, name: str) -> None:
        if self.write_protect:
            raise MediaError("DISK IS WRITE-PROTECTED")
        if name not in self.toc:
            raise MediaError(f"FILE NOT FOUND: {name}")
        # Compact the blob: rebuild data and TOC offsets
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

    def format(self) -> None:
        if self.write_protect:
            raise MediaError("DISK IS WRITE-PROTECTED")
        self.toc = {}
        self.data_blob = bytearray()
        self.save()

    def set_write_protect(self, on: bool) -> None:
        self.write_protect = on
        self.save()

    # --- Speed throttling -------------------------------------------
    def _throttled_copy(self, src_path: Optional[str], total: int,
                        bytes_per_sec: int, seek_ms: int,
                        write_mode: bool, progress_cb=None,
                        data: Optional[bytes] = None,
                        dest_path: Optional[str] = None) -> None:
        """Simulate the medium's speed while showing a progress bar."""
        # Initial seek/spin-up
        if seek_ms > 0:
            if progress_cb:
                progress_cb(0, total, "SEEK" if seek_ms < 500 else "SPIN-UP")
            time.sleep(seek_ms / 1000.0)

        # Chunk size: aim for ~10 updates/sec
        chunk = max(512, bytes_per_sec // 10)
        copied = 0
        start = time.monotonic()

        if write_mode:
            # Just simulate timing — actual data merge happens after
            while copied < total:
                this = min(chunk, total - copied)
                # how long this chunk SHOULD take
                target = (copied + this) / bytes_per_sec
                copied += this
                elapsed = time.monotonic() - start
                if elapsed < target:
                    time.sleep(target - elapsed)
                if progress_cb:
                    progress_cb(copied, total, "WRITING")
        else:
            # Reading: write to dest_path as we go, throttled
            with open(dest_path, "wb") as out:
                while copied < total:
                    this = min(chunk, total - copied)
                    out.write(data[copied:copied + this])
                    copied += this
                    target = copied / bytes_per_sec
                    elapsed = time.monotonic() - start
                    if elapsed < target:
                        time.sleep(target - elapsed)
                    if progress_cb:
                        progress_cb(copied, total, "READING")


# ============================================================
# CLI / Shell
# ============================================================
class Shell:
    def __init__(self):
        self.disk: Optional[VirtualDisk] = None
        self.disk_path: Optional[str] = None

    # ---- helpers ---------------------------------------------------
    @staticmethod
    def fmt_bytes(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024 or unit == "GB":
                if unit == "B":
                    return f"{n} {unit}"
                return f"{n/1024**['B','KB','MB','GB'].index(unit):.2f} {unit}"
            n /= 1024
        return f"{n:.2f} GB"

    @staticmethod
    def fmt_size(n: int) -> str:
        if n < 1024:
            return f"{n} B"
        if n < 1024 * 1024:
            return f"{n/1024:.1f} KB"
        if n < 1024 * 1024 * 1024:
            return f"{n/(1024*1024):.2f} MB"
        return f"{n/(1024*1024*1024):.2f} GB"

    def progress(self, done: int, total: int, phase: str):
        bar_w = 30
        if phase in ("SEEK", "SPIN-UP"):
            sys.stdout.write(f"\r[{phase:<8}] " + "." * bar_w + " ")
            sys.stdout.flush()
            return
        pct = done / total if total else 1
        filled = int(bar_w * pct)
        bar = "█" * filled + "░" * (bar_w - filled)
        rate = done / max(0.001, time.monotonic() - self._t0) if hasattr(self, "_t0") else 0
        sys.stdout.write(
            f"\r[{phase:<8}] {bar} {pct*100:5.1f}%  "
            f"{self.fmt_size(done):>9}/{self.fmt_size(total):<9}  "
            f"{self.fmt_size(int(rate))}/s   "
        )
        sys.stdout.flush()
        if done >= total:
            sys.stdout.write("\n")

    def progress_start(self):
        self._t0 = time.monotonic()

    # ---- commands --------------------------------------------------
    def cmd_help(self, *args):
        print("""
RETROMEDIA COMMANDS:

  CREATE <file> <media> [label]   Create a new virtual disk
  LOAD <file>                     Insert (load) a disk
  EJECT                           Eject the current disk
  INFO                            Show disk info
  DIR / LS                        List files on disk
  COPY <src> [name]               Copy host file → disk (write speed)
  EXTRACT <name> [dest]           Copy disk file → host (read speed)
  DELETE / RM <name>              Delete file from disk
  FORMAT                          Erase all files on disk
  PROTECT ON|OFF                  Toggle write protection
  MEDIA                           List supported media types
  HOSTLS [path]                   List host directory files
  CD <path>                       Change host directory
  PWD                             Show current host directory
  HELP                            Show this help
  QUIT / EXIT                     Leave program

EXAMPLES:
  CREATE backup.vfd 3.5-1.44m "MY DISK"
  LOAD backup.vfd
  COPY ~/notes.txt
  COPY photo.jpg PIC1.JPG
  EXTRACT PIC1.JPG ~/restored.jpg
""")

    def cmd_media(self, *args):
        print(f"\n{'KEY':<14}{'CAPACITY':>12}{'READ':>14}{'WRITE':>14}{'SEEK':>8}  LABEL")
        print("-" * 80)
        for key, spec in MEDIA_SPECS.items():
            print(f"{key:<14}"
                  f"{self.fmt_size(spec['size']):>12}"
                  f"{self.fmt_size(spec['read'])+'/s':>14}"
                  f"{self.fmt_size(spec['write'])+'/s':>14}"
                  f"{spec['seek_ms']:>5} ms  "
                  f"{spec['label']}")
        print()

    def cmd_create(self, *args):
        if len(args) < 2:
            print("Usage: CREATE <file> <media> [label]")
            return
        path, media = args[0], args[1]
        label = " ".join(args[2:]) if len(args) > 2 else ""
        if media not in MEDIA_SPECS:
            print(f"?UNKNOWN MEDIA: {media}  (use MEDIA to list)")
            return
        if os.path.exists(path):
            ans = input(f"'{path}' exists. Overwrite? [y/N] ").strip().lower()
            if ans != "y":
                print("Cancelled.")
                return
        try:
            disk = VirtualDisk.create(path, media, label)
            spec = MEDIA_SPECS[media]
            print(f"\n✓ CREATED: {path}")
            print(f"  Media:    {spec['label']}")
            print(f"  Capacity: {self.fmt_size(spec['size'])}")
            print(f"  Label:    {disk.label}")
            print(f"  Read:     {self.fmt_size(spec['read'])}/s")
            print(f"  Write:    {self.fmt_size(spec['write'])}/s")
            print(f"  Seek:     {spec['seek_ms']} ms\n")
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
            self.disk = d
            self.disk_path = path
            spec = d.spec
            # Simulate insertion delay
            print(f"Inserting disk", end="", flush=True)
            for _ in range(3):
                time.sleep(0.3)
                print(".", end="", flush=True)
            time.sleep(spec["seek_ms"] / 1000.0)
            print(f"\n\n✓ LOADED: {path}")
            print(f"  Label:     {d.label}")
            print(f"  Media:     {spec['label']}")
            print(f"  Capacity:  {self.fmt_size(d.size)}")
            print(f"  Used:      {self.fmt_size(d.used)} ({d.used/d.size*100:.1f}%)")
            print(f"  Free:      {self.fmt_size(d.free)}")
            print(f"  Files:     {len(d.toc)}")
            print(f"  Write-Pro: {'YES' if d.write_protect else 'NO'}")
            print(f"  Created:   {d.created}\n")
        except Exception as e:
            print(f"?LOAD FAILED: {e}")

    def cmd_eject(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        # Simulate ejection (CDs are slower than floppies)
        spec = self.disk.spec
        if "cd" in self.disk.media:
            print("Ejecting", end="", flush=True)
            for _ in range(4):
                time.sleep(0.4); print(".", end="", flush=True)
            print(" *clunk*\n")
        else:
            print("*click* Ejected.\n")
        self.disk = None
        self.disk_path = None

    def cmd_info(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        d = self.disk; spec = d.spec
        print(f"\n  Path:      {self.disk_path}")
        print(f"  Label:     {d.label}")
        print(f"  Media:     {spec['label']}")
        print(f"  Capacity:  {self.fmt_size(d.size)}")
        print(f"  Used:      {self.fmt_size(d.used)} ({d.used/d.size*100:.1f}%)")
        print(f"  Free:      {self.fmt_size(d.free)}")
        print(f"  Files:     {len(d.toc)}")
        print(f"  Read:      {self.fmt_size(spec['read'])}/s")
        print(f"  Write:     {self.fmt_size(spec['write'])}/s")
        print(f"  Seek:      {spec['seek_ms']} ms")
        print(f"  Write-Pro: {'YES' if d.write_protect else 'NO'}")
        print(f"  Created:   {d.created}\n")

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
            print("  <empty disk>")
        else:
            for name, size, added in files:
                print(f"  {name:<30}{self.fmt_size(size):>13}  {added}")
        print(f"\n {len(files)} FILE(S)   "
              f"{self.fmt_size(d.used)} USED   "
              f"{self.fmt_size(d.free)} FREE\n")

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
            self.disk.add_file(src, dest, progress_cb=self.progress)
            print(f"✓ Wrote {os.path.basename(dest or src)} to disk\n")
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
        dest = os.path.expanduser(args[1]) if len(args) > 1 else name
        try:
            self.progress_start()
            self.disk.extract_file(name, dest, progress_cb=self.progress)
            print(f"✓ Extracted {name} → {dest}\n")
        except Exception as e:
            print(f"\n?EXTRACT FAILED: {e}")

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
        ans = input(f"Format '{self.disk.label}'? All files will be erased! [y/N] ").strip().lower()
        if ans != "y":
            print("Cancelled.")
            return
        # Format takes time on real media
        spec = self.disk.spec
        fmt_time = max(2.0, self.disk.size / spec["write"] / 4)  # quick format ~ 1/4 capacity time
        print("Formatting", end="", flush=True)
        steps = int(fmt_time * 2)
        for _ in range(steps):
            time.sleep(0.5); print(".", end="", flush=True)
        try:
            self.disk.format()
            print("\n✓ Disk formatted.\n")
        except Exception as e:
            print(f"\n?FORMAT FAILED: {e}")

    def cmd_protect(self, *args):
        if not self.disk:
            print("?NO DISK INSERTED")
            return
        if not args or args[0].upper() not in ("ON", "OFF"):
            print("Usage: PROTECT ON|OFF")
            return
        on = args[0].upper() == "ON"
        self.disk.set_write_protect(on)
        print(f"Write protection: {'ON' if on else 'OFF'}\n")

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

    # ---- prompt ----------------------------------------------------
    def prompt(self) -> str:
        if self.disk:
            label = self.disk.label[:12]
            return f"[{label}] > "
        return "(no disk) > "

    def run(self):
        print("""
╔══════════════════════════════════════════════╗
║      RETROMEDIA - VIRTUAL FLOPPY/CD-R        ║
║         Authentic vintage save speeds        ║
╚══════════════════════════════════════════════╝
Type HELP for commands, MEDIA for media types.
""")
        commands = {
            "HELP": self.cmd_help, "?": self.cmd_help,
            "MEDIA": self.cmd_media,
            "CREATE": self.cmd_create,
            "LOAD": self.cmd_load, "INSERT": self.cmd_load, "MOUNT": self.cmd_load,
            "EJECT": self.cmd_eject, "UMOUNT": self.cmd_eject,
            "INFO": self.cmd_info, "STAT": self.cmd_info,
            "DIR": self.cmd_dir, "LS": self.cmd_dir,
            "COPY": self.cmd_copy, "WRITE": self.cmd_copy, "PUT": self.cmd_copy,
            "EXTRACT": self.cmd_extract, "READ": self.cmd_extract, "GET": self.cmd_extract,
            "DELETE": self.cmd_delete, "DEL": self.cmd_delete, "RM": self.cmd_delete,
            "FORMAT": self.cmd_format,
            "PROTECT": self.cmd_protect,
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


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="RetroMedia - virtual floppy/CD emulator")
    parser.add_argument("disk", nargs="?", help="Disk file to auto-load on startup")
    args = parser.parse_args()

    shell = Shell()
    if args.disk:
        shell.cmd_load(args.disk)
    shell.run()


if __name__ == "__main__":
    main()
