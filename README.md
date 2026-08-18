# RetroMedia 💾

**A virtual removable media emulator with authentic vintage behavior**

RetroMedia simulates the experience of working with classic storage media — from 5.25" floppy disks to modern NVMe drives — complete with accurate transfer speeds, seek delays, buffer mechanics, and even the satisfying _clunk_ of an optical drive.

Perfect for retro computing enthusiasts, educators, or anyone who wants to experience (or re-experience) the constraints and characteristics of vintage storage media without the physical hardware.

```
╔════════════════════════════════════════════════════════════════╗
║            RETROMEDIA - VIRTUAL MEDIA                          ║
║     Authentic vintage media & write-buffer model               ║
╚════════════════════════════════════════════════════════════════╝
```

## ✨ Features

### 🎛️ Multi-Drive Virtual Rig

* **Attach multiple drives simultaneously** — mix and match floppy, optical, HDD, SSD, and NVMe

* **Cross-drive file transfers** with physics-accurate speed simulation

* **Switch between drives** with the `USE` command

* Manage your virtual hardware array just like a real retro workstation

### 📀 Authentic Media Simulation

* **50+ media types** spanning 4 decades of storage technology

* **Real-world transfer rates** — experience the crawl of a 5.25" floppy or the speed of Gen4 NVMe

* **Mechanical theatrics** — spin-up delays, seek times, and eject animations for vintage drives

* **Zero latency** for solid-state media (SSD/NVMe) — no artificial delays

### 💿 Optical Media Engine

* **Bounded write buffer** simulation for CD/DVD/Blu-ray burning

* **Burn-Proof & JustLink** protection modes to prevent buffer underruns

* **Finalization** support for closing sessions on write-once media

* **Rewritable optical** (CD-RW, DVD±RW, BD-RE) with format/reuse capability

### 🚀 Performance Controls

* **HOSTRATE limiting** — simulate slower host systems or network transfers

* **Sparse file allocation** — HDD/SSD containers grow on-demand, not pre-allocated

* **Real-time progress bars** with buffer fill monitoring

* **SHA-256 checksums** for data integrity (optional)

### 🎯 Physics-Accurate Transfers

* **Cross-medium operations respect real constraints** — copying a 700MB ISO from a floppy? The tool won't stop you, but physics will

* **Two-phase transfers** — watch data read from source at source speed, then write to destination at destination speed

* **Host-capped throughput** — even a fast NVMe is limited if your host feed is slow

---

## 📦 Installation

RetroMedia is a single Python script with no external dependencies.

```bash
# Clone the repository
git clone https://github.com/fpucore/retromedia.git
cd retromedia

# Make it executable (optional)
chmod +x retromedia.py

# Run it
python3 retromedia.py
```

**Requirements:**

* Python 3.7 or later

* No additional packages needed — uses only standard library

---

## 🚀 Quick Start

```bash
# Start the interactive shell
python3 retromedia.py

# Create a 1.44MB floppy disk
CREATE backup.vfd 3.5-1.44m "MY BACKUP"

# Load it
LOAD backup.vfd

# Copy a file to the disk
COPY myfile.txt

# Check what's on it
DIR

# Eject
EJECT
```

### Multi-Drive Example

```bash
# Create a virtual rig with multiple drives
CREATE floppy.vfd 3.5-1.44m "BOOT DISK"
CREATE archive.cdr cd-r-700 "DATA ARCHIVE"
CREATE system.hdd wd-caviar "SYSTEM"
CREATE fast.nvme nvme-m2-1t "WORKSPACE"

# Attach them all
ATTACH floppy0 floppy.vfd
ATTACH optical0 archive.cdr
ATTACH hdd0 system.hdd
ATTACH nvme0 fast.nvme

# List your virtual hardware
DRIVES

# Transfer a file from NVMe to CD-R
USE nvme0
DIR
XFER nvme0:document.pdf optical0:document.pdf

# Finalize the CD so it's readable anywhere
USE optical0
FINALIZE
```

---

## 📚 Supported Media Types

### 💾 Floppy Disks

* 5.25" DD 360K (25 KB/s)

* 5.25" HD 1.2M (51 KB/s)

* 3.5" DD 720K (30 KB/s)

* 3.5" HD 1.44M (63 KB/s)

* 3.5" ED 2.88M (102 KB/s)

### 🔷 Removable Magnetic

* Zip 100 (1.4 MB/s)

* Zip 250 (2.4 MB/s)

### 💿 Optical Media

**CD Family:**

* CD-R (650/700MB, 1x–52x speeds)

* CD-RW (700MB, 4x)

**DVD Family:**

* DVD±R (4.7GB, single/dual-layer)

* DVD±RW (rewritable)

* DVD-RAM (2.6GB–9.4GB)

**HD Formats:**

* HD DVD-R/RW (15GB/30GB)

* HD DVD-RAM (20GB)

**Blu-ray:**

* BD-R/RE (25GB, 50GB, 100GB, 128GB)

* Supports XL and QL variants

### 🎵 MiniDisc

* MiniDisc 60/74/80 min

* Hi-MD 305MB/1GB

### 🖴 Hard Disk Drives (Vintage)

* **ST-506** (5MB, MFM, 625 KB/s)

* **ST-225** (20MB, MFM, 625 KB/s)

* **ST-251** (40MB, MFM, 937 KB/s)

* **WD 93028** (20MB, RLL, 1.25 MB/s)

* **WD Caviar** (170MB, IDE, 5 MB/s)

* **IBM Deskstar** (16GB, ATA-33, 14 MB/s)

* **Quantum Bigfoot** (12GB, ATA, 13 MB/s)

### 🖴 Hard Disk Drives (Modern)

* SATA HDD 1TB/4TB/8TB (160–220 MB/s, 7200 RPM)

### ⚡ Solid State Drives

* SATA SSD 250GB/1TB/4TB (520–560 MB/s)

* NVMe M.2 Gen3/Gen4 (500GB–4TB, 3.5–7.4 GB/s)

---

## 🎮 Command Reference

### Basic Operations

```
CREATE <file> <media> [label]    Create a new virtual medium
LOAD <file>                      Insert a medium
EJECT                            Eject the current medium
INFO                             Show medium information
DIR / LS                         List files on medium
COPY <src> [name]                Write host file → medium
EXTRACT <name> [dest]            Read medium file → host
DELETE / RM <name>               Delete file from medium
FORMAT                           Erase all files on medium
MEDIA                            List supported media types
```

### Multi-Drive Rig

```
ATTACH <slot> <file>             Load a drive into the rig
DETACH <slot>                    Remove a drive from the rig
DRIVES                           List all attached drives
USE <slot>                       Switch active drive
```

### Cross-Drive Operations

```
XFER <slot>:<file> <slot>:<file>   Copy file between drives
XMOVE <slot>:<file> <slot>:<file>  Move file between drives
```

### Optical Media

```
FINALIZE                         Close/finalize optical media
BURN-PROOF ON|OFF                Enable/disable Burn-Proof
JUSTLINK ON|OFF                  Enable/disable JustLink
BUFFER                           Show recorder settings
```

### Advanced

```
PROTECT ON|OFF                   Toggle write protection
HOSTRATE <KBps>|OFF              Set host throughput cap
HOSTLS [path]                    List host directory files
CD <path>                        Change host directory
PWD                              Show current host directory
```

---

## 💡 Usage Examples

### Example 1: Burn a CD with Burn-Proof

```bash
CREATE linux.cdr cd-r-700 "LINUX INSTALL"
LOAD linux.cdr
BURN-PROOF ON
COPY ~/Downloads/linux.iso
FINALIZE
EJECT
```

### Example 2: Create a Vintage IDE System

```bash
# Create a 170MB IDE drive like it's 1995
CREATE system.hdd wd-caviar "SYSTEM"
ATTACH hdd0 system.hdd
USE hdd0

# Experience authentic 5 MB/s transfer speeds
COPY ~/retro_os/msdos622.zip
COPY ~/retro_os/win31.zip
DIR
```

### Example 3: Multi-Drive Workflow

```bash
# Set up a complete retro workstation
ATTACH floppy0 boot.vfd
ATTACH optical0 backup.cdr
ATTACH hdd0 storage.hdd
ATTACH nvme0 workspace.nvme

# Set a 10 MB/s host rate to simulate a slow network
HOSTRATE 10000

# Copy from fast NVMe to slow optical
XFER nvme0:largefile.bin optical0:largefile.bin

# Watch the two-phase transfer:
# [XFER-READ] at NVMe speed
# [XFER-WRITE] at CD-R speed with buffer monitoring
```

### Example 4: Test Your Patience (or Don't)

```bash
# Create a 5MB MFM drive from 1980
CREATE ancient.hdd st-506 "MUSEUM PIECE"
LOAD ancient.hdd

# Try to copy a modern file
# Watch it transfer at a glacial 625 KB/s with 150ms seeks
# This is historically accurate — appreciate your modern hardware!
COPY largefile.dat
```

---

## 🔧 Technical Details

### Container Format

* **Magic:** `RETROFD\x01`

* **Version:** 1 (forward-compatible design)

* **Structure:** JSON header + JSON TOC + raw data blob

* **Features:** SHA-256 checksums per file, finalization flag, write-protect flag

### Media Families

Media are organized into families that share behavioral characteristics:

* `floppy` — Floppy disks with mechanical seeks

* `magnetic` — Removable magnetic (Zip)

* `optical` — CD/DVD/HD DVD/Blu-ray with write buffers

* `minidisc` — MiniDisc and Hi-MD

* `hdd-vintage` — MFM/RLL/early IDE disks

* `hdd-modern` — Modern magnetic spinning disks

* `ssd` — SATA solid-state 

* `nvme` — NVMe M.2 drives

### Write Buffer Simulation

Optical media use a **real bounded buffer** model:

* Data is read from the host into a fixed-size buffer

* The virtual recorder drains the buffer at the medium's write speed

* If the buffer empties before writing completes: **BUFFER UNDERRUN**

* Burn-Proof/JustLink modes allow recovery by pausing the write

This is the same mechanism real CD/DVD burners use.

### Sparse Allocation

HDD/SSD/NVMe containers use **sparse file allocation**:

* A 1TB virtual drive doesn't consume 1TB on your host filesystem

* The container grows dynamically as you add files

* Host filesystem must support sparse files (ext4, NTFS, APFS do)

### Physics-Accurate Transfers

Cross-drive transfers simulate real hardware behavior:

1. **Read phase:** Extract data from source at source read speed

2. **Write phase:** Write data to destination at destination write speed

3. **Host rate cap:** If set, both phases are limited by `HOSTRATE`

4. **Mechanical delays:** Spin-up and seek times are honored

5. **Buffer mechanics:** Optical destination shows buffer fill in real-time

---

## 🎨 Theatrics & Immersion

RetroMedia doesn't just simulate speeds — it simulates the _experience_:

* **Spin-up delays** for mechanical media (floppy, HDD, optical)

* **"Inserting disk..."** animation with dots

* **"Ejecting... _clunk_"** for optical drives

* **"_click_ Ejected."** for floppy/magnetic

* **Real-time progress bars** with transfer rates and buffer monitoring

* **No artificial delays** for SSD/NVMe — instant response

The `theatrics` flag in media specs controls this behavior. Solid-state media have `theatrics=False` for immediate access.

---

## 🤝 Contributing

Contributions are welcome! Here are some ideas:

* Add more vintage media types (Jaz, LS-120, SyQuest, etc.)

* Implement defragmentation simulation for HDDs

* Add bad sector simulation

* Create a TUI (text UI) with rich/textual

* Port to other platforms

* Add network transfer simulation (FTP, SMB speeds)

**How to contribute:**

1. Fork the repository

2. Create a feature branch (`git checkout -b feature/amazing-feature`)

3. Commit your changes (`git commit -m 'Add amazing feature'`)

4. Push to the branch (`git push origin feature/amazing-feature`)

5. Open a Pull Request

---

## 📜 License

MIT License

Copyright (c) 2026 Chris McGimpsey-Jones

Permission is hereby granted, free of charge, to any person obtaining a copy\
of this software and associated documentation files (the "Software"), to deal\
in the Software without restriction, including without limitation the rights\
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\
copies of the Software, and to permit persons to whom the Software is\
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all\
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\
SOFTWARE.

---

## 🙏 Acknowledgments

* Inspired by the golden age of personal computing (1980s–2000s)

* Built for retrocomputing enthusiasts, educators, and the curious

* No physical media were harmed in the making of this software

---

## 📞 Support & Contact

* **Issues:** [GitHub Issues](https://github.com/fpucore/retromedia/issues)

* **Author:** Chris McGimpsey-Jones

* **Email:** chrisjones.unixmen@gmail.com

---

**Remember:** In a world of infinite cloud storage, sometimes it's fun to pretend you only have 1.44MB. 💾
