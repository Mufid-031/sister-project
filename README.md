# Proyek UTS Sistem Terdistribusi (Kelas E)
## Sistem Presensi Terdistribusi Berbasis Multi-Kernel LXC & Tailscale WireGuard Mesh

Proyek ini dibangun untuk memenuhi kualifikasi Ujian Tengah Semester (UTS) mata kuliah **Sistem Terdistribusi**, mengimplementasikan arsitektur Microservices multi-tier yang terisolasi di dalam platform virtualisasi **Proxmox VE** dan terhubung aman menggunakan jaringan mesh **Tailscale**.

---

## 1. Topologi & Arsitektur Sistem

```
                                  [ User Browser ]
                                          |
                +-------------------------+-------------------------+
                |                                                   |
      (Akses LAN WiFi Lokal)                               (Akses Tailscale Mesh)
     http://192.168.100.57:3000                             http://100.91.242.11
                |                                                   |
                +-------------------------+-------------------------+
                                          |
                                          v Port 80
        +-------------------------------------------------------------------+
        |  LXC 100: FRONTEND SERVER                                         |
        |  - OS: Alpine Linux 3.20 (musl libc runtime)                      |
        |  - IP Tailscale: 100.91.242.11 | IP Lokal: 10.10.10.100           |
        |  - Service: Nginx 1.26 + Modern Tailwind SPA Dashboard            |
        |  - Role: Web UI & Reverse Proxy /api/ -> Backend                  |
        +-------------------------------------------------------------------+
                                          |
                                          | HTTP /api/ via Tailscale Mesh
                                          v Port 8000
        +-------------------------------------------------------------------+
        |  LXC 101: BACKEND API WORKER                                      |
        |  - OS: Ubuntu 24.04 LTS (GNU glibc runtime)                       |
        |  - IP Tailscale: 100.118.230.58 | IP Lokal: 10.10.10.101         |
        |  - Service: Python FastAPI + Uvicorn (Systemd Auto-Restart)       |
        |  - Role: Validasi Presensi, Idempotency Check, Cluster Telemetry  |
        +-------------------------------------------------------------------+
                                          |
                                          | PostgreSQL TCP via Tailscale Mesh
                                          v Port 5432
        +-------------------------------------------------------------------+
        |  LXC 102: DATABASE SERVER                                         |
        |  - OS: Debian 12 Bookworm (GNU glibc runtime)                     |
        |  - IP Tailscale: 100.122.119.32 | IP Lokal: 10.10.10.102         |
        |  - Service: PostgreSQL 15 RDBMS                                   |
        |  - Security: Whitelist connection khusus dari IP Backend Tailscale|
        +-------------------------------------------------------------------+
```

---

## 2. Rincian Node Kontainer

| Kontainer | VMID | Distro OS | Userland Lib | Alokasi RAM | IP Lokal (`vmbr1`) | IP Tailscale Mesh | Service Utama |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`frontend`** | `100` | Alpine Linux | `musl libc` | 512 MB (~35 MB used) | `10.10.10.100` | **`100.91.242.11`** | Nginx Web Server (Port 80) |
| **`backend`** | `101` | Ubuntu 24.04 | `glibc` | 512 MB (~78 MB used) | `10.10.10.101` | **`100.118.230.58`** | FastAPI REST API (Port 8000) |
| **`db-server`** | `102` | Debian 12 | `glibc` | 512 MB (~110 MB used) | `10.10.10.102` | **`100.122.119.32`** | PostgreSQL 15 (Port 5432) |

---

## 3. Fitur Utama Sistem

### A. Fitur Fungsional Presensi
1. **Presensi Mandiri Mahasiswa:**
   - Input NIM, Nama, dan Token Sesi yang valid.
   - Pilihan status: *HADIR*, *IZIN*, atau *SAKIT*.
2. **Pencegahan Double-Submission (*Idempotency*):**
   - Mencegah kecurangan mahasiswa absen dua kali pada sesi yang sama via constraint basis data (`unique_session_nim`).
3. **Manajemen Sesi Dosen / Admin:**
   - Membuat sesi perkuliahan baru dengan batas durasi menit dan token acak.
   - Buka/tutup sesi absensi secara *real-time*.
4. **Rekapitulasi Kehadiran & Audit Trail:**
   - Riwayat presensi lengkap dengan timestamp presisi, Client IP, dan penanda node pemroses.
   - Fitur ekspor cetak langsung dari browser.

### B. Fitur Observabilitas Sistem Terdistribusi (Khusus Pengujian UTS)
1. **Live Cluster Latency Monitor:**
   - Panel atas dashboard menampilkan status real-time ketiga node dan RTT latency (Round-Trip Time) via Tailscale (rata-rata latency < 1ms).
2. **Network Isolation Security:**
   - Database PostgreSQL (port 5432) dikonfigurasi melalui `pg_hba.conf` sehingga **hanya menerima koneksi dari IP Tailscale Backend (`100.118.230.58/32`)**, menolak koneksi dari jaringan luar yang tidak terotorisasi.
3. **Multi-Userland LXC Exploration:**
   - Kombinasi Alpine (musl libc), Ubuntu, dan Debian menunjukkan bagaimana LXC mengisolasi userland yang berbeda di atas satu kernel host Proxmox secara efisien pada RAM 512 MB.

---

## 4. Cara Mengakses Web Aplikasi

### Opsi 1: Melalui Jaringan WiFi / LAN Lokal
Buka browser di laptop atau HP yang berada di jaringan WiFi yang sama dengan Proxmox:
```
http://192.168.100.57:3000
```

### Opsi 2: Melalui Jaringan Mesh Tailscale
Buka browser dari perangkat mana saja yang login ke akun Tailscale:
```
http://100.91.242.11
```

### Opsi 3: Dokumentasi API Interaktif (Swagger UI)
```
http://192.168.100.57:3000/docs
```
atau via Tailscale:
```
http://100.118.230.58:8000/docs
```

---

## 5. Panduan Pengujian & Demo Saat Ujian (UTS)

1. **Uji Presensi Normal:**
   - Buka menu **Form Presensi**.
   - Klik salah satu akun uji coba (misal: NIM `22002` - Ahmad Farhan).
   - Masukkan token aktif: `SISTER24`.
   - Klik **Kirim Presensi** -> Muncul alert hijau sukses dengan info node pemroses `backend-ubuntu-101`.

2. **Uji Idempotency (Anti-Double Submit):**
   - Klik kembali **Kirim Presensi** dengan NIM yang sama.
   - Sistem akan menolak dengan pesan HTTP 409: *"NIM 22002 sudah tercatat hadir pada sesi ini sebelumnya!"*.

3. **Uji Kelola Sesi Dosen:**
   - Masuk ke tab **Kelola Sesi Kuliah**.
   - Buat sesi baru (klik *Acak Token* -> *Buka Sesi Presensi*).
   - Buka/Tutup sesi untuk melihat perubahan status secara real-time.

4. **Uji Arsitektur Terdistribusi:**
   - Masuk ke tab **Topologi & Demo Sister**.
   - Klik **Test Latency Cluster** untuk melihat RTT latency antar kontainer secara langsung.
   - Periksa tabel **Audit Log Transaksi Terdistribusi** untuk membuktikan bahwa setiap request dicatat secara persisten ke database PostgreSQL di node Debian.
