<h1>
  <img src="https://www.qanonsec.com/images/i.php?/upload/2026/09/25/20260925102623-bb1ef04b-2s.webp" alt="ag-img" />
  RetroMedia 💾
</h1>

```
╔══════════════════════════════════════════════════════════╗
║           RETROMEDIA ULTIMATE - VIRTUAL MEDIA            ║
║   Data Storage • Audio CDs • Hard Disks • H/W+OS Rigs    ║
╚══════════════════════════════════════════════════════════╝
```

**Virtual removable & fixed media and rig simulator**

Authentic capacities, transfer speeds, write buffering, Audio CD (CD-DA) creation, LightScribe 
physical etching, Multi-Era Copy Protection, Pirate/Hacker Overrides, Drive Rigs, Cross-transfers, 
Cloning, Batch Ripping, and Playback via FFmpeg.

Optional authentic virtual hardware profiling and operating system adaptations.

RetroMedia simulates the experience of working with classic storage media — from 5.25" floppy disks 
to modern NVMe drives — complete with accurate transfer speeds, seek delays, buffer mechanics, and 
even the satisfying _clunk_ of an optical drive.

Perfect for retro computing enthusiasts, educators, or anyone who wants to experience (or 
re-experience) the constraints and characteristics of vintage storage media without the physical hardware.

## ✨ Features

### 🎛️ Multi-Drive Virtual Workstation

* **Attach multiple drives simultaneously** — mix and match floppy, optical, USB, HDD, SSD, and NVMe

* **Cross-drive file transfers** with physics-accurate speed simulation

* **Switch between drives** with the `USE` command

* **Hardware profiling** to manage virtual hardware array, like a real workstation

### 📀 Authentic Media Simulation

* **50+ media types** spanning 4 decades of storage technology

* **Real-world transfer rates** — experience the crawl of a 5.25" floppy or the speed of Gen4 NVMe

* **Mechanical theatrics** — spin-up delays, seek times, and eject animations for vintage drives

* **Zero latency** for solid-state media (SSD/NVMe) — no artificial delays

### 💿 Optical Media Engine

* **Bounded write buffer** simulation for CD/DVD/Blu-ray burning

* **Burn-Proof & JustLink** protection modes to prevent buffer underruns

* **Finalization** support for closing sessions on write-once media

* **Rewritable optical** (CD-RW, DVD±RW, BD-RE) with real format/reuse capability

* **LightScribe** (Etch a unique LightScribe label onto a virtual disc with real graphic file output)

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

RetroMedia is a single source **Python** script.

Although you can run the Python script directly, it is not recommended and is firmly discouraged, due to its expansive size 
and increasing complexity of the source code as the project matures.

It is recommended you compile the source code to an executable binary, using Nuitka (Method 1), and install it to your system.

**Requirements:**

* Python 3.7 or later
* Nuitka

# Method 1 - Compile & Install

```bash
> gh repo clone fpucore/retromedia.git

> goto retromedia

> python -m nuitka \
          --onefile \
          --include-package=PIL \
          --enable-plugin=pyqt6 \
          --output-dir=build \
          retromedia.py

> elevate install -s -m 755 build/retromedia.bin /usr/bin/retromedia

> retromedia
```

# Method 2 (optional, not recommended) - Run the Python script

```bash
> make-executable retromedia.py

> python3 retromedia.py
```

---

## 🚀 Quick Start

```bash
# Start the interactive shell
> retromedia

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
# Create a simple virtual rig with multiple drives
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

## 📚 Supported Media

### 💾 Floppy Disks

* 5.25" DD 360K (25 KB/s)

* 5.25" HD 1.2M (51 KB/s)

* 3.5" DD 720K (30 KB/s)

* 3.5" HD 1.44M (63 KB/s)

* 3.5" ED 2.88M (102 KB/s)

### 🔷 Removable Magnetic

* Zip 100 (1.4 MB/s)

* Zip 250 (2.4 MB/s)

### 💿 Optical Media (Data+Audio)

**CD Family:**

* CD-R (650/700MB, 1x–52x speeds)

* CD-RW (700MB, 4x)

* Kodak Gold (650MB, 4x)

**DVD Family:**

* DVD±R (4.7GB, single/dual-layer)

* DVD±RW (rewritable)

* DVD-RAM (2.6GB–4.7GB)

**HD-DVD Formats:**

* HD DVD-R/RW (15GB)

**Blu-ray:**

* BD-R (25GB, 50GB, 100GB, 128GB)

* BD-RE (25GB)

* Supports DL, XL and QL variants

### 🎵 MiniDisc

* MiniDisc (80 min)

### ⚡ USB Flash & External SSDs

* usb-1.1-64m   -  Trek ThumbDrive 64MB (USB 1.1)
* usb-2.0-4g    -  Kingston DataTraveler 4GB (USB 2.0)
* usb-3.0-64g   -  Corsair Flash Voyager 64GB (USB 3.0)
* usb-3.2-256g  -  SanDisk Extreme PRO 256GB (USB 3.2)
* usb-3.2-1t    -  Samsung T7 Portable SSD 1TB (USB 3.2 Gen 2)

---

## 💻 Supported Hardware

* **COMMODORE-1541**           400 B/s     400 B/s  Commodore 1541 5.25" Floppy Drive

* **APPLE-DISK-II**         15.00 KB/s  15.00 KB/s  Apple Disk II 5.25" Floppy Drive

* **CHINON-FZ354**          31.00 KB/s  27.50 KB/s  Chinon FZ-354 Amiga 3.5" Floppy Drive

* **TEAC-FD-235HF**         62.00 KB/s  55.00 KB/s  TEAC FD-235HF 3.5" Floppy Drive

* **IBM-PS2-MODEL-30**      62.00 KB/s  55.00 KB/s  IBM PS2 Model 30 3.5" Floppy Drive

* **SONY-MPF920**           62.00 KB/s  55.00 KB/s  Sony MPF920 3.5" Floppy Drive

* **ZIP-100-PARALLEL**      50.00 KB/s  50.00 KB/s  Iomega Zip 100 (Parallel Port)

* **SONY-CDU31A**          300.00 KB/s   Read-Only  Sony CDU31A 1x/2x Caddy CD-ROM

* **PLEXTOR-4012A**          5.86 MB/s   1.76 MB/s  Plextor PlexWriter 40/12/40A

* **YAMAHA-CRWF1**           6.45 MB/s   3.52 MB/s  Yamaha CRW-F1 (DiscT@2)

* **HP-DVD1040**            21.48 MB/s  10.74 MB/s  HP dvd1040 LightScribe DVD Writer

* **PIONEER-DVR108**        21.48 MB/s  21.48 MB/s  Pioneer DVR-108 16x DVD±RW

* **TOSHIBA-SDH903A**       17.58 MB/s   Read-Only  Toshiba SD-H903A HD-DVD/DVD-ROM

* **TOSHIBA-SDH903A-V2**    17.58 MB/s  17.58 MB/s  Toshiba SD-H903A-V2 HD-DVD/DVD±RW

* **PIONEER-BDR207**        52.73 MB/s  52.73 MB/s  Pioneer BDR-207 Blu-ray Writer

* **LITEON-GENERIC-OEM**    23.44 MB/s  23.44 MB/s  Lite-On Generic CD/DVD-RW

### 🗄️ Mechanical Hard Disks

* **ST-225** (20MB, MFM, 610 KB/s)

* **WD Caviar** (170MB, IDE, 5 MB/s)

* **OEM** SATA HDD (1TB, 160 MB/s, 7200 RPM)

### ⚡ Solid-state Drives

* **OEM** SATA SSD (1TB, 560 MB/s)

* **OEM** NVMe M.2 Gen3 (1TB, 3.4 GB/s)

---

## 🏗️ Supported Rig Profiles

Rig Profiles are an optional, unique feature that lets users add more control and personality to their Rig.

Users can define hardware details like motherboard, CPU, RAM, and GPU — completely optional, and not 
required for RetroMedia's core operation or its use as a virtual storage medium tool.

### 🔌 Motherboard Profiles

* **INTEL-430FX**           1995     128MB        -          50/60/66  Intel 430FX Triton

* **INTEL-430TX**           1996     256MB        -          66/75/83  Intel 430TX Triton II

* **INTEL-440BX**           1998    1024MB      1.0        66/100/133  Intel 440BX

* **INTEL-815**             2000     512MB      2.0        66/100/133  Intel 815E

* **INTEL-850**             2000    2048MB      4.0               400  Intel 850

* **AMD-751**               1999     768MB      2.0       100/200/266  AMD 751 / Irongate

* **VIA-KT133**             2000    1536MB      4.0           200/266  VIA KT133

* **SIS-735**               2001    3072MB      4.0           200/266  SiS 735

* **INTEL-850E**            2002    2048MB      4.0           400/533  Intel 850E

### 🧩 CPU Profiles

* **PENTIUM-133**           1995     133MHz Socket 7                 128MB  Intel Pentium 133

* **PENTIUM-MMX-233**       1997     233MHz Socket 7                 256MB  Intel Pentium MMX 233

* **PENTIUM-II-450**        1999     450MHz Slot 1                   512MB  Intel Pentium II 450

* **PENTIUM-III-600**       1999     600MHz Slot 1/Socket 370       1024MB  Intel Pentium III 600

* **PENTIUM-III-1000**      2000    1000MHz Socket 370              1024MB  Intel Pentium III 1GHz

* **PENTIUM-4-1500**        2000    1500MHz Socket 423              2048MB  Intel Pentium 4 1.5GHz

* **PENTIUM-4-2400-478**    2002    2400MHz Socket 478              2048MB  Intel Pentium 4 2.4GHz

* **K6-2-400**              1999     400MHz Super Socket 7/Socket 7    1024MB  AMD K6-2 400 (400Mhz)

* **ATHLON-1000**           2000    1000MHz Socket A                1536MB  AMD Athlon 1GHz

* **DURON-800**             2000     800MHz Socket A                1536MB  AMD Duron 800 (800Mhz)

* **ATHLON-XP-1800**        2001    1533MHz Socket A                3072MB  AMD Athlon XP 1800+

* **CYRIX-MII-300**         1998     233MHz Socket 7                 256MB  Cyrix MII 300

* **VIA-C3-800**            2001     800MHz Socket 370              1024MB  VIA C3 800

### 📊 RAM Profiles

* **FPM-16**                  1994      FPM       16MB        70ns  16MB FPM DRAM

* **FPM-32**                  1995      FPM       32MB        70ns  32MB FPM DRAM

* **EDO-32**                  1996      EDO       32MB        60ns  32MB EDO DRAM

* **EDO-64**                  1997      EDO       64MB        60ns  64MB EDO DRAM

* **SDRAM-PC66-64**           1997    SDRAM       64MB        PC66  64MB SDRAM PC66

* **SDRAM-PC100-128**         1998    SDRAM      128MB       PC100  128MB SDRAM PC100

* **SDRAM-PC133-256**         1999    SDRAM      256MB       PC133  256MB SDRAM PC133

* **SDRAM-PC133-512**         2000    SDRAM      512MB       PC133  512MB SDRAM PC133

* **RDRAM-PC800-256**         2000    RDRAM      256MB       PC800  256MB RDRAM PC800

* **RDRAM-PC800-512**         2001    RDRAM      512MB       PC800  512MB RDRAM PC800

* **DDR-PC2100-512**          2001      DDR      512MB      PC2100  512MB DDR-266 PC2100

* **DDR-PC2700-1024**         2002      DDR     1024MB      PC2700  1GB DDR-333 PC2700

### 🤖 GPU Profiles

* **VOODOO1**               1996     4MBPCI                 38  3dfx Voodoo Graphics 4MB

* **VOODOO2**               1998    12MBPCI                 72  3dfx Voodoo2 12MB

* **VOODOO3-2000**          1999    16MBAGP/PCI            108  3dfx Voodoo3 2000 16MB

* **VOODOO3-3000**          1999    16MBAGP/PCI            126  3dfx Voodoo3 3000 16MB

* **VOODOO5-5500**          2000    64MBAGP/PCI            178  3dfx Voodoo5 5500 64MB

* **RIVA128**               1997     4MBPCI/AGP             42  NVIDIA RIVA 128 4MB

* **TNT2-ULTRA**            1999    32MBAGP                118  NVIDIA RIVA TNT2 Ultra 32MB

* **GEFORCE256**            1999    32MBAGP                162  NVIDIA GeForce 256 32MB DDR

* **GEFORCE2-GTS**          2000    32MBAGP                235  NVIDIA GeForce2 GTS 32MB

* **ATI-RAGE128PRO**        1999    32MBAGP/PCI            100  ATI Rage 128 Pro 32MB

* **MATROX-G400MAX**        1999    32MBAGP                132  Matrox Millennium G400 MAX 32MB

* **S3-SAVAGE4**            1999    32MBAGP/PCI             91  S3 Savage4 Pro 32MB

* **RADEON-256**            2000    64MBAGP                205  ATI Radeon DDR 64MB

* **RADEON-7500**           2001    64MBAGP/PCI            250  ATI Radeon 7500 64MB

---

## 🎮 Command Reference

### RETROMEDIA COMMANDS
```text

  CREATE <file> <media> [label]                     Create a new virtual medium (Data or Audio CD)
  LOAD <file>                                       Insert / load a medium
  EJECT                                             Eject the current medium
  INFO                                              Show medium information
  DIR / LS                                          List files (or audio tracks) on medium
  COPY <src> [dest]                                 Write host file → Data medium
  EXTRACT <name|num> [dest]                         Extract data file or Audio CD track → host
  DELETE / RM <name>                                Delete file from medium
  FORMAT                                            Erase medium
  FINALIZE                                          Close/finalize optical medium
  LITESCRIBE <image>                                Etch a LightScribe label onto the disc
  MEDIA                                             List supported media types

BUFFER, PROTECTION & COPY CONTROL:
  PROTECTION <NONE|SAFEDISC|SECUROM|CACTUS|TRACK0>  Set copy protection (Anti-Rip):
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
  PIRATE ON|OFF                                     Toggle Admin Mode to bypass copy protections
  CLONE [dest_file.iso]                             Export a raw sector-by-sector clone
  RIP                                               Batch extract all tracks from an Audio CD
  BURN-PROOF ON|OFF                                 Enable/disable Burn-Proof protection
  JUSTLINK ON|OFF                                   Enable/disable JustLink protection
  OVERBURN ON|OFF                                   Allow writing past logical disc capacity (+5%)
  ENGINE <name>                                     Set optical burning engine:
                                                        NERO     (Nero Burning ROM) [DEFAULT]
                                                        ASHAMPOO (Ashampoo Burning Studio)
                                                        ROXIO    (Roxio Easy CD Creator)
                                                        ALCOHOL  (Alcohol 120%)
                                                        CLONECD  (CloneCD)
                                                        IMGBURN  (ImgBurn)
  BUFFER                                            Show current recorder settings
  HOSTRATE <KBps>|OFF                               Cap host throughput (min with media rate)

AUDIO CD COMMANDS:
  ADD / BURN <audio> [title]                        Burn an audio track onto the Audio CD
  PLAY [track_number]                               Play the virtual Audio CD using ffplay
  ARTIST <name>                                     Set disc artist
  ALBUM <title>                                     Set disc album title

SYSTEM / HARDWARE RIG COMMANDS:
  ATTACHCPU <CPU_ID>                                Attach a historical CPU profile
  DETACHCPU                                         Remove the CPU profile
  CPU / CPUINFO                                     Show attached CPU profile
  CPUS                                              List historical CPU profiles
  CPUBENCH [LOAD]                                   Synthetic CPU workload model (0-100)
  ATTACHMB <MODEL_ID>                               Attach a historical motherboard profile
  DETACHMB                                          Remove the motherboard profile
  MB / MBINFO                                       Show attached motherboard
  MOTHERBOARDS                                      List historical motherboard profiles
  CHECKSYSTEM                                       Validate CPU / motherboard / GPU compatibility
  BENCH [WxH] [BPP] [GEOM] [TEX] [FX]               System GPU benchmark using attached platform
  RAM / RAMINFO                                     Show installed RAM and motherboard limit
  RAMPROFILES                                       List historical RAM module profiles
  ADDRAM <RAM_MODEL_ID>                             Add a RAM module up to the platform maximum

OPERATING SYSTEM / RIG ADAPTATION COMMANDS:
  DISKS                                             List hard-disk/SSD/NVMe installation targets
  ATTACHDISK <slot> <media> [label]                 Create and attach a virtual storage device
  OS [OS_ID]                                        List or inspect historical OS profiles
  INSTALL [OS_ID] [DISK_SLOT]                       Install an OS adaptation with authentic transfer constraints
  ADAPTATIONS [DISK_SLOT]                           Show installed OS adaptations

DRIVE RIG COMMANDS:
  ATTACH <slot> <file> [MODEL_ID]                   Load a drive into the rig (e.g. TEAC-FD235HF)
  DETACH <slot>                                     Remove a drive from the rig
  HARDWARE                                          List authentic historical drive models
  DRIVES                                            List all attached drives
  USE <slot>                                        Switch active drive
  XFER <slot>:<file> <slot>:<file>                  Copy file between drives
  XMOVE <slot>:<file> <slot>:<file>                 Move file between drives

GPU RIG COMMANDS:
  ATTACHGPU <MODEL_ID> [SLI_COUNT]                  Attach a historical GPU rig
  DETACHGPU                                         Remove the GPU rig
  GPU / GPUINFO                                     Show attached GPU
  GPUS                                              List historical GPU models
  GPUCAPS                                           Show GPU API/feature capabilities
  GPUHOST <CPU_ID> <RAM_MB> [BUS]                   Configure host bottlenecks
  GPUCPUS                                           List host CPU profiles
  GPUBENCH [WxH] [BPP] [GEOM] [TEX] [FX]            Run synthetic GPU performance model

HOST COMMANDS:
  HOSTLS [path]                                     List host directory files
  CD <path>                                         Change host directory
  PWD                                               Show current host directory
  QUIT / EXIT                                       Leave program

```

---

## 💡 Basic Usage Examples

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
COPY archive_1.zip
COPY archive_2.zip
...
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
```

### Example 4: Test Your Patience (or Don't)

```bash
# Create a 5MB MFM drive from the 1980s
CREATE ancient.hdd st-225 "MUSEUM PIECE"
LOAD ancient.hdd

# Try to copy a modern file
# Watch it transfer at a glacial 610 KB/s with 150ms seeks
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

* `minidisc` — MiniDisc

* `usb` — USB Flash & External SSD Drives

* `hdd-vintage` — Vintage magnetic spinning disks

* `hdd-modern` — Modern magnetic spinning disks

* `ssd` — Fast SATA solid-state 

* `nvme` — Fast NVMe M.2 drives

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
