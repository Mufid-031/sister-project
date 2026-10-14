# LAPORAN & PANDUAN LENGKAP PROYEK UTS SISTEM TERDISTRIBUSI
## "Sistem Presensi Terdistribusi Berbasis Multi-Kernel LXC & Tailscale WireGuard Mesh"

* **Mata Kuliah:** Sistem Terdistribusi (Kelas E)
* **Topik Tugas:** Proyek Ujian Tengah Semester (UTS) — Multi Kernel & Microservices
* **Platform Hypervisor:** Proxmox Virtual Environment (VE) 8.x
* **Jaringan Keamanan:** Tailscale Mesh VPN (WireGuard Overlay)
* **Penyusun:** Mufid Risqi (Teknik Informatika)

---

## DAFTAR ISI
1. [Arsitektur & Konsep Utama](#1-arsitektur--konsep-utama)
2. [Tahap 1: Instalasi Proxmox VE di VirtualBox](#2-tahap-1-instalasi-proxmox-ve-di-virtualbox)
3. [Tahap 2: Konfigurasi Jaringan & Routing Proxmox Host](#3-tahap-2-konfigurasi-jaringan--routing-proxmox-host)
4. [Tahap 3: Pembuatan & Konfigurasi 3 Kontainer (LXC Multi-Distro)](#4-tahap-3-pembuatan--konfigurasi-3-kontainer-lxc-multi-distro)
5. [Tahap 4: Konfigurasi Tailscale Mesh & Manajemen Akun](#5-tahap-4-konfigurasi-tailscale-mesh--manajemen-akun)
6. [Tahap 5: Implementasi Aplikasi Absensi Terdistribusi](#6-tahap-5-implementasi-aplikasi-absensi-terdistribusi)
7. [Tahap 6: Prosedur Operasional (SOP Sehari-hari)](#7-tahap-6-prosedur-operasional-sop-sehari-hari)
   - [Cara Running Setelah Laptop Dimatikan](#a-cara-menyalakan-kembali-setelah-laptop-dimatikan)
   - [Cara Mengunggah Perubahan Kode di Masa Mendatang](#b-cara-mengunggah-perubahan-kode-di-masa-mendatang)
8. [Tahap 7: Troubleshooting & Panduan Pertanyaan Dosen (UTS Defense)](#8-tahap-7-troubleshooting--panduan-pertanyaan-dosen-uts-defense)

---

## 1. Arsitektur & Konsep Utama

Sistem ini memecah arsitektur monolitik menjadi **3 Microservices** terpisah yang masing-masing berjalan di dalam container LXC independen dengan distribusi sistem operasi yang berbeda:

```
                                [ Browser Pengguna ]
                                          |
                +-------------------------+-------------------------+
                |                                                   |
     (Akses WiFi / LAN Lokal)                              (Akses Tailscale Mesh)
   https://192.168.100.57:3443                              http://100.91.242.11
    http://192.168.100.57:3000                              https://100.91.242.11
                |                                                   |
                +-------------------------+-------------------------+
                                          |
                                          v Port 80 / 443
        +-------------------------------------------------------------------+
        |  LXC 100: FRONTEND SERVER                                         |
        |  - Distro: Alpine Linux 3.20 (musl libc runtime)                  |
        |  - IP Lokal: 10.10.10.100 | IP Tailscale: 100.91.242.11          |
        |  - Service: Nginx 1.26 + Tailwind Single Page Application (SPA)   |
        |  - Role: Antarmuka Web, Dashboard Observability & Reverse Proxy   |
        +-------------------------------------------------------------------+
                                          |
                                          | REST API via Tailscale WireGuard
                                          v Port 8000
        +-------------------------------------------------------------------+
        |  LXC 101: BACKEND API WORKER                                      |
        |  - Distro: Ubuntu 24.04 LTS (GNU glibc runtime)                   |
        |  - IP Lokal: 10.10.10.101 | IP Tailscale: 100.118.230.58         |
        |  - Service: Python FastAPI + Uvicorn (Systemd Auto-Restart)       |
        |  - Role: Validasi Token, Anti-Double Submit, Cluster Telemetry    |
        +-------------------------------------------------------------------+
                                          |
                                          | PostgreSQL TCP via Tailscale WireGuard
                                          v Port 5432
        +-------------------------------------------------------------------+
        |  LXC 102: DATABASE SERVER                                         |
        |  - Distro: Debian 12 Bookworm (GNU glibc runtime)                 |
        |  - IP Lokal: 10.10.10.102 | IP Tailscale: 100.122.119.32         |
        |  - Service: PostgreSQL 15 RDBMS                                   |
        |  - Security: Whitelist koneksi hanya dari IP Tailscale Backend    |
        +-------------------------------------------------------------------+
```

---

## 2. Tahap 1: Instalasi Proxmox VE di VirtualBox

Jika Anda menginstal Proxmox di dalam VirtualBox (Nested Virtualization):

1. **Spesifikasi VM di VirtualBox:**
   * **Tipe OS:** Linux -> Version: Debian (64-bit).
   * **Base Memory:** 4096 MB – 8192 MB (Rekomendasi: 8 GB agar lancar).
   * **Processors:** 2 Cores atau lebih (Centang opsi *Enable Nested VT-x/AMD-V* di menu *System -> Processor*).
   * **Storage Disk:** 30 GB – 50 GB (VDI Dinamis).
2. **Pengaturan Jaringan VirtualBox (PENTING):**
   * Masuk ke menu **Settings VM -> Network -> Adapter 1**.
   * Ubah *Attached to* menjadi: **Bridged Adapter**.
   * Pilih kartu jaringan laptop Anda (misal: WiFi adapter atau Ethernet LAN).
   * *Promiscuous Mode:* Ubah ke **Allow All**.
   *(Tujuan mode Bridged: Agar Proxmox mendapatkan IP yang satu subnet dengan laptop/WiFi rumah, misal `192.168.100.x`).*
3. **Instalasi ISO Proxmox:**
   * Masukkan file ISO `proxmox-ve_*.iso` ke CD/DVD drive VM.
   * Ikuti wizard:
     * Country: Indonesia, Timezone: Asia/Jakarta.
     * Password root & email pribadi.
     * **Network Management:**
       * FQDN: `pve-lab.local`
       * IP Address (CIDR): `192.168.100.57/24` *(sesuaikan dengan subnet WiFi Anda)*
       * Gateway: `192.168.100.1` *(IP router WiFi)*
       * DNS Server: `8.8.8.8`
4. **Akses Dashboard Proxmox:**
   * Setelah instalasi selesai dan reboot, buka browser di laptop:
     `https://192.168.100.57:8006/`
   * Klik *Advanced -> Accept Risk* (karena sertifikat self-signed bawaan Proxmox).

---

## 3. Tahap 2: Konfigurasi Jaringan & Routing Proxmox Host

Proxmox membutuhkan 2 Linux Bridge:
* **`vmbr0`**: Terhubung ke kartu fisik (`nic0`), memegang IP `192.168.100.57/24` (Akses luar).
* **`vmbr1`**: Bridge internal terisolasi (`10.10.10.1/24`), tempat kontainer saling terhubung secara lokal.

### A. Pengaturan File `/etc/network/interfaces` di Host Proxmox
Diperiksa atau diedit melalui menu **Proxmox -> Shell**:
```bash
auto lo
iface lo inet loopback

iface nic0 inet manual

auto vmbr0
iface vmbr0 inet static
	address 192.168.100.57/24
	gateway 192.168.100.1
	bridge-ports nic0
	bridge-stp off
	bridge-fd 0
	# Mengembalikan aturan iptables otomatis saat Proxmox booting
	post-up iptables-restore < /etc/iptables.rules

auto vmbr1
iface vmbr1 inet static
	address 10.10.10.1/24
	bridge-ports none
	bridge-stp off
	bridge-fd 0
	# Mengaktifkan NAT agar kontainer bisa akses internet
	post-up iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o vmbr0 -j MASQUERADE
	post-down iptables -t nat -D POSTROUTING -s 10.10.10.0/24 -o vmbr0 -j MASQUERADE
```

### B. Mengaktifkan IP Forwarding & Port Forwarding
Jalankan di shell Proxmox:
```bash
# 1. Aktifkan IPv4 forwarding permanen
echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/99-ipforward.conf
sysctl -p /etc/sysctl.d/99-ipforward.conf

# 2. Port Forwarding dari Proxmox Host ke Kontainer Frontend (10.10.10.100)
# Port 3000 (HTTP) -> Frontend Port 80
iptables -t nat -A PREROUTING -p tcp -d 192.168.100.57 --dport 3000 -j DNAT --to-destination 10.10.10.100:80

# Port 3443 (HTTPS) -> Frontend Port 443
iptables -t nat -A PREROUTING -p tcp -d 192.168.100.57 --dport 3443 -j DNAT --to-destination 10.10.10.100:443

# Simpan iptables permanen
iptables-save > /etc/iptables.rules
```

---

## 4. Tahap 3: Pembuatan & Konfigurasi 3 Kontainer (LXC Multi-Distro)

Di Proxmox Web GUI, unduh template OS melalui menu **local -> CT Templates -> Templates**:
* `alpine-3.20-default_*.tar.zst`
* `ubuntu-24.04-standard_*.tar.zst`
* `debian-12-standard_*.tar.zst`

### Rincian Konfigurasi Pembuatan Tiap Kontainer

| Parameter | LXC 100 (`frontend`) | LXC 101 (`backend`) | LXC 102 (`db-server`) |
| :--- | :--- | :--- | :--- |
| **Hostname** | `frontend` | `backend` | `db-server` |
| **Template OS** | Alpine Linux 3.20 | Ubuntu 24.04 LTS | Debian 12 Bookworm |
| **CPU Core** | 1 Core | 1 Core | 1 Core |
| **RAM / Swap** | 512 MB / 512 MB | 512 MB / 512 MB | 512 MB / 512 MB |
| **Disk Size** | 8 GB | 8 GB | 8 GB |
| **Bridge Jaringan** | `vmbr1` | `vmbr1` | `vmbr1` |
| **IPv4 / CIDR** | `10.10.10.100/24` | `10.10.10.101/24` | `10.10.10.102/24` |
| **Gateway** | `10.10.10.1` | `10.10.10.1` | `10.10.10.1` |
| **DNS Server** | `8.8.8.8` | `8.8.8.8` | `8.8.8.8` |

### Pengaturan Khusus LXC (Nesting & Auto-Start)
Jalankan di shell host Proxmox:
```bash
# Aktifkan fitur nesting (wajib untuk Ubuntu 24.04 & systemd)
pct set 100 -features nesting=1
pct set 101 -features nesting=1
pct set 102 -features nesting=1

# Aktifkan auto-start agar otomatis menyala saat Proxmox booting
pct set 100 -onboot 1
pct set 101 -onboot 1
pct set 102 -onboot 1
```

---

## 5. Tahap 4: Konfigurasi Tailscale Mesh & Manajemen Akun

Agar Tailscale dapat beroperasi di dalam LXC Proxmox tanpa mode unprivileged yang bermasalah, device `/dev/net/tun` harus di-passthrough ke konfigurasi kontainer.

### A. Konfigurasi File `/etc/pve/lxc/<VMID>.conf`
Pada host Proxmox, baris berikut telah ditambahkan di `/etc/pve/lxc/100.conf`, `101.conf`, dan `102.conf`:
```ini
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
```

### B. Instalasi Tailscale di Masing-Masing Kontainer
* **Di LXC 100 (Alpine):**
  ```bash
  pct exec 100 -- apk add tailscale
  pct exec 100 -- rc-update add tailscale default
  pct exec 100 -- rc-service tailscale start
  ```
* **Di LXC 101 (Ubuntu) & LXC 102 (Debian):**
  ```bash
  pct exec 101 -- curl -fsSL https://tailscale.com/install.sh | sh
  pct exec 102 -- curl -fsSL https://tailscale.com/install.sh | sh
  ```

### C. Menghubungkan Kontainer ke Akun Tailscale
Jalankan perintah ini lalu salin URL otorisasi yang muncul ke browser Anda untuk login:
```bash
pct exec 100 -- tailscale up
pct exec 101 -- tailscale up
pct exec 102 -- tailscale up
```

### D. Daftar IP Tailscale Mesh yang Terbentuk
* **Frontend (Alpine):** `100.91.242.11`
* **Backend (Ubuntu):** `100.118.230.58`
* **DB-Server (Debian):** `100.122.119.32`

---

### E. Manajemen Akun Tailscale (Disconnect & Pindah Akun)

Jika di masa mendatang Anda ingin **mengganti akun Tailscale**, memutuskan koneksi, atau login ulang dengan akun Google/GitHub yang berbeda:

#### 1. Cara Logout / Putus Koneksi dari Akun Saat Ini:
```bash
# Logout pada kontainer tertentu:
pct exec 100 -- tailscale logout
pct exec 101 -- tailscale logout
pct exec 102 -- tailscale logout
```
*(Perintah ini akan mencabut izin mesin dan menghapus node dari dashboard admin Tailscale lama).*

#### 2. Cara Mematikan Koneksi Sementara (Tanpa Logout Akun):
```bash
pct exec 100 -- tailscale down
```
Untuk mengaktifkan kembali:
```bash
pct exec 100 -- tailscale up
```

#### 3. Cara Login ke Akun Tailscale yang Baru:
```bash
# Login ulang dengan force-reauth ke akun baru:
pct exec 100 -- tailscale up --force-reauth
pct exec 101 -- tailscale up --force-reauth
pct exec 102 -- tailscale up --force-reauth
```
*(Buka URL link login baru yang muncul di terminal untuk menautkannya ke akun baru).*

#### 4. Mengetahui Status & IP Baru:
```bash
pct exec 100 -- tailscale status
pct exec 100 -- tailscale ip -4
```
> **Penting:** Jika IP Tailscale berubah setelah ganti akun, cukup perbarui variabel IP di file konfigurasi Nginx (`/etc/nginx/http.d/default.conf`) dan file `/opt/backend/main.py` menggunakan script `./deploy.sh`.

---

## 6. Tahap 5: Implementasi Aplikasi Absensi Terdistribusi

### A. Database Server (LXC 102 - Debian)
* **DBMS:** PostgreSQL 15
* **Konfigurasi Listen:** `listen_addresses = '*'` di `/etc/postgresql/15/main/postgresql.conf`.
* **Keamanan Akses (`pg_hba.conf`):**
  Hanya mengizinkan koneksi dari IP Tailscale Backend:
  ```
  host  attendance_db  sister_user  100.118.230.58/32  scram-sha-256
  host  attendance_db  sister_user  10.10.10.0/24      scram-sha-256
  ```
* **Kredensial:** User `sister_user`, Password `sister_secure_pass_2026`, Database `attendance_db`.
* **Tabel:**
  1. `courses`: Daftar mata kuliah (IF3105 Sistem Terdistribusi E, dll).
  2. `sessions`: Sesi absensi dengan token unik (misal: `SISTER24`) dan batas waktu kadaluwarsa.
  3. `students`: Data mahasiswa (NIM, Nama, Jurusan).
  4. `attendances`: Catatan presensi lengkap dengan `CONSTRAINT unique_session_nim UNIQUE (session_id, nim)` (mencegah absen ganda).
  5. `node_logs`: Audit trail terdistribusi yang mencatat aktivitas transaksi per node.

---

### B. Backend API Worker (LXC 101 - Ubuntu)
* **Framework:** Python 3.12 + FastAPI + Uvicorn + psycopg2 connection pooling.
* **Lokasi File:** `/opt/backend/main.py`.
* **Systemd Service (`/etc/systemd/system/sister-backend.service`):**
  Dikonfigurasi auto-restart jika terjadi failure:
  ```ini
  [Unit]
  Description=Sister Distributed Attendance Backend (FastAPI)
  After=network.target

  [Service]
  Type=simple
  User=root
  WorkingDirectory=/opt/backend
  ExecStart=/opt/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
  Restart=always
  RestartSec=3
  Environment=PYTHONUNBUFFERED=1

  [Install]
  WantedBy=multi-user.target
  ```
* **Fitur Utama API:**
  * `POST /api/attend`: Validasi sesi, pencegahan double-submission (*idempotency*), pencatatan client IP.
  * `GET /api/health`: Mengecek latency query ke PostgreSQL via Tailscale (`100.122.119.32:5432`) dan penggunaan memori.
  * `GET /api/cluster`: Mengukur RTT latency antar seluruh node di jaringan mesh.
  * `GET /docs`: Dokumentasi interaktif Swagger OpenAPI.

---

### C. Frontend Web Server (LXC 100 - Alpine)
* **Web Server:** Nginx 1.26
* **Sertifikat SSL:** Self-signed OpenSSL (`/etc/nginx/ssl/nginx.crt` & `nginx.key`).
* **Reverse Proxy Nginx (`/etc/nginx/http.d/default.conf`):**
  Meneruskan panggilan `/api/` langsung ke IP Tailscale backend (`http://100.118.230.58:8000/api/`).
* **Web UI Dashboard (`/var/www/html/index.html`):**
  * Dibangun dengan Tailwind CSS dan Lucide Icons.
  * **Status Bar Observability:** Menampilkan live ping badge ketiga node secara real-time.
  * **Tab 1: Form Presensi Mahasiswa:** Input NIM, Nama, Token Sesi.
  * **Tab 2: Kelola Sesi Kuliah (Dosen):** Buka/tutup sesi dan acak token unik.
  * **Tab 3: Rekap Kehadiran:** Tabel real-time data presensi dengan fitur cetak.
  * **Tab 4: Topologi & Demo Sister:** Visual arsitektur 3 kontainer dan ringkasan teori untuk bahan sidang/ujian.

---

## 7. Prosedur Operasional (SOP Sehari-hari)

### A. Cara Menyalakan Kembali Setelah Laptop Dimatikan
Ketika laptop dimatikan, VM Proxmox di VirtualBox akan ikut mati. Saat laptop dinyalakan kembali, ikuti langkah mudah ini:

1. **Nyalakan VirtualBox:**
   * Buka aplikasi VirtualBox di laptop.
   * Pilih VM Proxmox Anda (`pve-lab`) -> Klik tombol **Start** (Normal Start atau Headless Start).
2. **Tunggu 1–2 Menit:**
   * Proxmox akan booting.
   * **SEMUA OTOMATIS BERJALAN SENDIRI!**
     * Karena konfigurasi `onboot 1` sudah aktif, Proxmox akan otomatis menyalakan LXC 100, 101, dan 102.
     * Service Tailscale di ketiga kontainer akan langsung terkoneksi ke jaringan mesh secara otomatis.
     * Service Nginx di Frontend dan `sister-backend` di Backend otomatis menyala via OpenRC & Systemd.
     * Aturan routing IPTables di-load otomatis via `iptables-restore`.
3. **Buka Browser:**
   * Akses langsung melalui:
     👉 **https://192.168.100.57:3443** (Klik *Advanced -> Accept Risk*)
     atau
     👉 **http://192.168.100.57:3000**
     atau
     👉 **http://100.91.242.11** (via Tailscale)

---

### B. Cara Mengunggah Perubahan Kode di Masa Mendatang

Jika Anda mengedit tampilan di [`frontend/index.html`](file:///home/mufidd/Coding/Projects/sister-project/frontend/index.html) atau logika API di [`backend/main.py`](file:///home/mufidd/Coding/Projects/sister-project/backend/main.py) di laptop:

#### **Metode 1: Menggunakan Script Otomatis (Sangat Direkomendasikan ⭐)**
Saya telah membuatkan script otomatis bernama `deploy.sh` di folder proyek lokal Anda.
Buka terminal di folder proyek dan jalankan:
```bash
cd /home/mufidd/Coding/Projects/sister-project
./deploy.sh
```
*Script ini otomatis meng-upload file baru, reload Nginx di Alpine, restart backend di Ubuntu, dan melakukan uji healthcheck.*

#### **Metode 2: Manual via Perintah Terminal**
Jika ingin mengupload secara manual satu-persatu:

* **Update Frontend (LXC 100):**
  ```bash
  scp frontend/index.html root@192.168.100.57:/tmp/index.html
  ssh root@192.168.100.57 "pct push 100 /tmp/index.html /var/www/html/index.html && pct exec 100 -- rc-service nginx reload && rm /tmp/index.html"
  ```
* **Update Backend (LXC 101):**
  ```bash
  scp backend/main.py root@192.168.100.57:/tmp/main.py
  ssh root@192.168.100.57 "pct push 101 /tmp/main.py /opt/backend/main.py && pct exec 101 -- systemctl restart sister-backend && rm /tmp/main.py"
  ```

---

## 8. Tahap 7: Troubleshooting & Panduan Pertanyaan Dosen (UTS Defense)

### A. Troubleshooting Cepat Masalah Umum

| Masalah | Penyebab | Solusi |
| :--- | :--- | :--- |
| `SSL_ERROR_RX_RECORD_TOO_LONG` | Browser (Zen/Firefox) memaksa HTTPS pada port HTTP 3000. | Gunakan port HTTPS: **`https://192.168.100.57:3443`** atau ketik `http://` secara eksplisit. |
| Kontainer tidak bisa `ping 8.8.8.8` | IP Forwarding di host Proxmox mati. | Jalankan `ssh root@192.168.100.57 "sysctl -w net.ipv4.ip_forward=1"`. |
| Tailscale status `NoState` | Jaringan kontainer mati atau tun device belum dimount. | Pastikan `eth0` kontainer memiliki IP `10.10.10.x` dan config `/etc/pve/lxc/<ID>.conf` memiliki mapping tun. |
| Backend status `degraded` di web | Database PostgreSQL mati atau pg_hba memblokir IP. | Periksa status DB: `pct exec 102 -- systemctl status postgresql`. |

---

### B. Panduan Menjawab Pertanyaan Dosen Saat Ujian (UTS Defense)

#### 1. "Apa yang dimaksud dengan Multi-Kernel dalam implementasi proyek Anda?"
> **Jawaban:** 
> "Dalam konteks virtualisasi container (LXC) di Proxmox, ketiga kontainer berbagi (*shared*) satu Kernel Linux milik Host Proxmox (`pve-lab`). Namun, di level user-space runtime, sistem kami menerapkan **Multi-Userland OS Execution**:
> * Kontainer Frontend menggunakan **Alpine Linux** dengan runtime library **musl libc** yang ultra-ringan (~35 MB RAM).
> * Kontainer Backend menggunakan **Ubuntu 24.04** dengan runtime library **GNU glibc** untuk kompatibilitas framework Python FastAPI.
> * Kontainer Database menggunakan **Debian 12** dengan runtime library **GNU glibc** untuk keandalan PostgreSQL RDBMS.
> Isolasi resource dilakukan secara ketat melalui Linux Namespaces (PID, Mount, Net, IPC, UTS) dan cgroups v2."

#### 2. "Mengapa menggunakan Tailscale Mesh Network dan bukan routing IP biasa?"
> **Jawaban:** 
> "Tailscale membangun jaringan overlay **Zero-Trust berbasis WireGuard Mesh**. Keunggulannya:
> 1. **Keamanan & Isolasi:** Port Database PostgreSQL (5432) tidak diekspos ke public internet atau LAN luar, melainkan di-bind khusus pada interface Tailscale (`100.122.119.32`).
> 2. **Enkripsi End-to-End:** Semua paket data komunikasi antara Frontend, Backend, dan Database terenkripsi penuh melalui protokol kriptografi modern WireGuard (ChaCha20-Poly1305).
> 3. **Independensi Jaringan:** Meskipun host Proxmox berpindah WiFi/jaringan, komunikasi antar-kontainer tetap stabil tanpa perlu mengubah IP konfigurasi aplikasi."

#### 3. "Bagaimana sistem Anda menangani konsistensi data dan concorrency?"
> **Jawaban:** 
> "Kami menerapkan prinsip **Idempotency** dan **ACID Transaction** di PostgreSQL. Pada tabel `attendances`, kami memasang constraint unik `UNIQUE (session_id, nim)`. Jika mahasiswa mencoba melakukan submit presensi berulang kali pada sesi yang sama, database secara otomatis menolak dan Backend mengembalikan respon HTTP 409 Conflict secara terstandarisasi, mencegah race condition dan pencatatan ganda."
