# retromedia

Virtual floppy disk and CD-R/CD-ROM emulator with authentic vintage save speeds, capacities, and behaviour.

`retromedia` drops you into a BASIC-style interactive shell where you can `CREATE` a virtual disk, `LOAD` it into the drive, `COPY` files onto it at the genuinely glacial speed of a 5.25" double-density floppy, listen to a 1× CD-R seek for two seconds, and then `EJECT` it with a satisfying *click*.

## Features

- Interactive shell prompt with a single-character `?ERROR` style straight out of the 1980s.
- 13 media presets covering the entire floppy + CD-R era.
- Honest, throttled read/write timing — copying a 1.4 MB file to a 1.44M floppy really does take a minute.
- Per-medium seek / spin-up delays.
- Per-disk Table-Of-Contents with file timestamps and write protection.
- Live progress bar with current phase (SEEK, SPIN-UP, READING, WRITING) and rate.
- Format, delete, and write-protect operations.
- Pure Python 3 — no third-party dependencies.

## Supported media

| Key            | Capacity | Read       | Write      | Seek    | Description           |
|----------------|---------:|-----------:|-----------:|--------:|-----------------------|
| `5.25-360k`    | 360 KB   | 25 KB/s    | 22 KB/s    | 200 ms  | 5.25" DD              |
| `5.25-1.2m`    | 1.2 MB   | 50 KB/s    | 45 KB/s    | 100 ms  | 5.25" HD              |
| `3.5-720k`     | 720 KB   | 30 KB/s    | 25 KB/s    | 150 ms  | 3.5" DD               |
| `3.5-1.44m`    | 1.44 MB  | 62 KB/s    | 55 KB/s    | 90 ms   | 3.5" HD               |
| `3.5-2.88m`    | 2.88 MB  | 100 KB/s   | 90 KB/s    | 80 ms   | 3.5" ED               |
| `zip-100`      | 100 MB   | 1.4 MB/s   | 1.0 MB/s   | 29 ms   | Iomega Zip 100        |
| `zip-250`      | 250 MB   | 2.4 MB/s   | 1.5 MB/s   | 29 ms   | Iomega Zip 250        |
| `cd-1x`        | 650 MB   | 150 KB/s   | 150 KB/s   | 2000 ms | CD-R 1×               |
| `cd-2x`        | 650 MB   | 300 KB/s   | 300 KB/s   | 2000 ms | CD-R 2×               |
| `cd-4x`        | 650 MB   | 600 KB/s   | 600 KB/s   | 1500 ms | CD-R 4×               |
| `cd-8x`        | 700 MB   | 1.2 MB/s   | 1.2 MB/s   | 1500 ms | CD-R 8×               |
| `cd-16x`       | 700 MB   | 2.4 MB/s   | 2.4 MB/s   | 1000 ms | CD-R 16×              |
| `cd-32x`       | 700 MB   | 4.8 MB/s   | 4.8 MB/s   | 1000 ms | CD-R 32×              |
| `cd-52x`       | 700 MB   | 7.8 MB/s   | 7.8 MB/s   | 1000 ms | CD-R 52×              |

## Requirements

- Python 3.8+
- A terminal that doesn't mind unicode block characters in its progress bar.

## Installation

```bash
git clone https://github.com/fpucore/retromedia.git
cd retromedia
chmod +x retromedia.py

# Optional: put it on your PATH
mkdir -p ~/.local/bin
ln -s "$PWD/retromedia.py" ~/.local/bin/retromedia
```

## Usage

Launch the interactive shell:

```bash
python3 retromedia.py
```

…or auto-load a disk on start-up:

```bash
python3 retromedia.py mydisk.vfd
```

### Example session

```
> CREATE backup.vfd 3.5-1.44m "MY DISK"

✓ CREATED: backup.vfd
  Media:    3.5" HD 1.44M
  Capacity: 1.41 MB
  Label:    MY DISK
  ...

> LOAD backup.vfd
Inserting disk...
✓ LOADED: backup.vfd

[MY DISK] > COPY ~/notes.txt
[WRITING ] ██████████████████████████████ 100.0%   18.3 KB/18.3 KB    55.1 KB/s
✓ Wrote notes.txt to disk

[MY DISK] > DIR

 VOLUME: MY DISK
 NAME                                   SIZE  ADDED
 ----------------------------------------------------------------
  notes.txt                          18.3 KB  2026-05-08T...

 1 FILE(S)   18.3 KB USED   1.41 MB FREE

[MY DISK] > EJECT
*click* Ejected.
```

## Commands

| Command                     | Purpose                                       |
|-----------------------------|-----------------------------------------------|
| `CREATE <file> <media> [label]` | Create a new virtual disk                 |
| `LOAD <file>`               | Insert (load) a disk                          |
| `EJECT`                     | Eject the current disk                        |
| `INFO`                      | Show disk info                                |
| `DIR` / `LS`                | List files on the disk                        |
| `COPY <src> [name]`         | Copy host file onto disk (write-throttled)    |
| `EXTRACT <name> [dest]`     | Copy disk file to host (read-throttled)       |
| `DELETE` / `RM <name>`      | Delete a file from disk                       |
| `FORMAT`                    | Erase all files on disk                       |
| `PROTECT ON` / `PROTECT OFF` | Toggle write protection                      |
| `MEDIA`                     | List supported media types                    |
| `HOSTLS [path]`             | List host directory contents                  |
| `CD <path>`                 | Change host directory                         |
| `PWD`                       | Show current host directory                   |
| `HELP` / `?`                | Show command help                             |
| `QUIT` / `EXIT`             | Leave the program                             |

Aliases: `LOAD` ≡ `INSERT` ≡ `MOUNT`, `EJECT` ≡ `UMOUNT`, `COPY` ≡ `WRITE` ≡ `PUT`, `EXTRACT` ≡ `READ` ≡ `GET`, `DELETE` ≡ `DEL` ≡ `RM`.

## File format

Each virtual disk is a single file beginning with the magic bytes `RETROFD\x01`, followed by a little-endian version (uint16), a header length (uint16), a JSON metadata header, a JSON Table-Of-Contents, and finally the concatenated raw file data.

## License

Released under the [MIT License](LICENSE).

## Author

Chris McGimpsey-Jones (2026)

chrisjones.unixmen@gmail.com
