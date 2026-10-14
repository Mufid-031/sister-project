# Proyek UTS Sistem Terdistribusi (Kelas E)
## Sistem Presensi Terdistribusi Berbasis Multi-Kernel LXC & Tailscale WireGuard Mesh
**Disusun oleh: Kelompok 5 (Teknik Informatika)**

Proyek ini dibangun untuk memenuhi kualifikasi Ujian Tengah Semester (UTS) mata kuliah **Sistem Terdistribusi**, mengimplementasikan arsitektur Microservices multi-tier yang terisolasi di dalam platform virtualisasi **Proxmox VE** dan terhubung aman menggunakan jaringan mesh **Tailscale**.

---

## 1. Topologi & Arsitektur Sistem

```
                                  [ User Browser ]
                                          |
                +-------------------------+-------------------------+
                |                                                   |
      (Akses LAN WiFi Lokal)                               (Akses Tailscale Mesh)
     https://<IP_PROXMOX>:3443                              http://100.119.108.66
      http://<IP_PROXMOX>:3000                             https://100.119.108.66
                |                                                   |
                +-------------------------+-------------------------+
                                          |
                                          v Port 80 / 443
        +-------------------------------------------------------------------+
        |  LXC 100: FRONTEND SERVER                                         |
        |  - OS: Alpine Linux 3.20 (musl libc runtime)                      |
        |  - IP Tailscale: 100.119.108.66 | IP Lokal: 10.10.10.100          |
        |  - Service: Nginx 1.26 + Modern Tailwind SPA Dashboard            |
        |  - Role: Web UI, Role Auth (Murid vs Dosen), Reverse Proxy        |
        +-------------------------------------------------------------------+
                                          |
                                          | HTTP /api/ via Tailscale Mesh
                                          v Port 8000
        +-------------------------------------------------------------------+
        |  LXC 101: BACKEND API WORKER                                      |
        |  - OS: Ubuntu 24.04 LTS (GNU glibc runtime)                       |
        |  - IP Tailscale: 100.119.201.56 | IP Lokal: 10.10.10.101         |
        |  - Service: Python FastAPI + Uvicorn (Systemd Auto-Restart)       |
        |  - Role: Validasi Presensi, Idempotency Check, Cluster Telemetry  |
        +-------------------------------------------------------------------+
                                          |
                                          | PostgreSQL TCP via Tailscale Mesh
                                          v Port 5432
        +-------------------------------------------------------------------+
        |  LXC 102: DATABASE SERVER                                         |
        |  - OS: Debian 12 Bookworm (GNU glibc runtime)                     |
        |  - IP Tailscale: 100.115.151.38 | IP Lokal: 10.10.10.102         |
        |  - Service: PostgreSQL 15 RDBMS                                   |
        |  - Security: Whitelist connection khusus dari IP Backend Tailscale|
        +-------------------------------------------------------------------+
```

---

## 2. Rincian Node Kontainer

| Kontainer | VMID | Distro OS | Userland Lib | Alokasi RAM | IP Lokal (`vmbr1`) | IP Tailscale Mesh | Service Utama |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`frontend`** | `100` | Alpine Linux | `musl libc` | 512 MB (~35 MB used) | `10.10.10.100` | **`100.119.108.66`** | Nginx Web Server (Port 80/443) |
| **`backend`** | `101` | Ubuntu 24.04 | `glibc` | 512 MB (~78 MB used) | `10.10.10.101` | **`100.119.201.56`** | FastAPI REST API (Port 8000) |
| **`db-server`** | `102` | Debian 12 | `glibc` | 512 MB (~110 MB used) | `10.10.10.102` | **`100.115.151.38`** | PostgreSQL 15 (Port 5432) |

---

## 3. Fitur Utama & Pemisahan Role (Murid vs Dosen)

### A. Pemisahan Hak Akses Role
1. **Mode Murid / Mahasiswa (Default):**
   - Tampilan bersih terfokus pada **Form Presensi Kehadiran**.
   - Tab pengelolaan dosen (Kelola Sesi, Rekap, Topologi) terkunci dengan ikon gembok 🔒.
   - Mahasiswa hanya bisa mengisi NIM, Nama, dan Token Sesi untuk mencatatkan kehadiran.
2. **Mode Guru / Dosen (Kelompok 5 Admin):**
   - Tombol **"Login Dosen"** di pojok kanan atas dengan form autentikasi.
   - Kredensial Default: Username `dosen`, Password `kelompok5` (atau `dosen123`).
   - Membuka seluruh tab:
     - **Kelola Sesi Kuliah:** Membuat sesi baru, generator token acak, buka/tutup sesi.
     - **Rekap Kehadiran:** Audit trail real-time siapa saja yang sudah hadir dengan fitur cetak/export PDF.
     - **Topologi Sistem & Audit Log:** Pemantau latency RTT cluster antar-node secara live.

### B. Fitur Presensi & Ketahanan Sistem Terdistribusi
1. **Pencegahan Double-Submission (*Idempotency*):**
   - Mahasiswa tidak bisa melakukan submit presensi dua kali pada sesi yang sama via constraint basis data unik `UNIQUE (session_id, nim)`. Sistem mengembalikan status `HTTP 409 Conflict`.
2. **Zero-Trust Network Isolation:**
   - PostgreSQL (port 5432) hanya menerima koneksi dari IP Tailscale Backend (`100.119.201.56/32`), memblokir akses tidak terotorisasi.
3. **Observabilitas RTT Latency Cluster:**
   - Endpoint `/api/cluster` dan `/api/health` mengukur latency jaringan WireGuard antar-node secara live.

---

## 4. Cara Mengakses Web Aplikasi

### Melalui Jaringan WiFi / LAN:
* Jalur HTTPS: `https://<IP_PROXMOX>:3443` *(Klik Advanced -> Accept Risk)*
* Jalur HTTP: `http://<IP_PROXMOX>:3000`

### Melalui Jaringan Mesh Tailscale:
* Web Presensi: `http://100.119.108.66` atau `https://100.119.108.66`
* Dokumentasi API Swagger: `http://100.119.108.66/docs`
