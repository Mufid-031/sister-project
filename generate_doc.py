#!/usr/bin/env python3
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_code_block(doc, code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F3F4F6")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(code_text.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def create_document(output_path):
    doc = docx.Document()
    
    # Page Margins (1 inch all sides)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(51, 65, 85)

    # ==================== COVER / JUDUL ====================
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(24)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("LAPORAN LENGKAP & ALUR PEMBUATAN\nSISTEM PRESENSI TERDISTRIBUSI")
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(30, 58, 138) # Navy Blue

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(18)
    r_sub = p_sub.add_run("Implementasi Multi-Kernel LXC (Alpine, Ubuntu, Debian), Hypervisor Proxmox VE 8.x,\ndan Jaringan Mesh VPN Tailscale (WireGuard)")
    r_sub.font.size = Pt(13)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(71, 85, 105)

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_after = Pt(24)
    r_meta = p_meta.add_run("Mata Kuliah: Sistem Terdistribusi (Kelas E) — Proyek Ujian Tengah Semester (UTS)\nPenyusun: KELOMPOK 5 (Teknik Informatika)")
    r_meta.font.bold = True
    r_meta.font.size = Pt(11)
    r_meta.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Helper for Headings
    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(16)
        r.font.bold = True
        r.font.color.rgb = RGBColor(30, 58, 138)
        return h

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = RGBColor(14, 116, 144) # Cyan/Dark Teal
        return h

    def add_h3(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(2)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(11.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(51, 65, 85)
        return h

    # ==================== BAB I ====================
    add_h1("BAB I: GAMBARAN UMUM & ARSITEKTUR SISTEM")
    
    p = doc.add_paragraph()
    p.add_run(
        "Proyek Sistem Presensi Terdistribusi ini dirancang untuk menggantikan arsitektur monolitik konvensional dengan membagi sistem ke dalam tiga lapisan terisolasi (Three-Tier Microservices). Setiap lapisan berjalan pada sistem operasi Linux yang berbeda (Multi-Distro Userland) di dalam kontainer Linux (LXC) pada platform hypervisor Proxmox Virtual Environment 8.x, serta dihubungkan menggunakan jaringan mesh terenkripsi Tailscale WireGuard."
    )

    doc.add_paragraph(
        "Tiga simpul (node) utama dalam klaster terdistribusi ini adalah:\n"
        "1. LXC 100 (Frontend Server): Berjalan di atas Alpine Linux 3.20 (musl libc runtime) melayani antarmuka web mahasiswa dan dosen via Nginx.\n"
        "2. LXC 101 (Backend API): Berjalan di atas Ubuntu 24.04 LTS (glibc runtime) menjalankan REST API berbasis FastAPI dan Uvicorn.\n"
        "3. LXC 102 (Database Server): Berjalan di atas Debian 12 Bookworm menjalankan sistem manajemen basis data relasional PostgreSQL 15."
    )

    # ==================== BAB II ====================
    add_h1("BAB II: ALUR LENGKAP PEMBUATAN PROYEK (DARI AWAL HINGGA AKHIR)")
    
    add_h2("2.1 Tahap 1: Instalasi & Konfigurasi Hypervisor Proxmox di VirtualBox")
    doc.add_paragraph(
        "Proxmox VE berperan sebagai Bare-Metal Hypervisor Type-1 yang diinstalasikan di dalam Oracle VirtualBox laptop Arch Linux menggunakan teknik Nested Virtualization. Langkah pembuatannya:"
    )
    doc.add_paragraph(
        "1. Membuat VM Baru di VirtualBox:\n"
        "   - Tipe Sistem Operasi: Linux -> Version: Debian (64-bit).\n"
        "   - Alokasi Memori: 8192 MB (8 GB RAM) agar seluruh kontainer berjalan responsif.\n"
        "   - Alokasi Prosesor: 2 Cores. Wajib mencentang opsi 'Enable Nested VT-x/AMD-V' pada menu Settings -> System -> Processor.\n"
        "   - Alokasi Penyimpanan: 40 GB VDI Dinamis."
    )
    doc.add_paragraph(
        "2. Konfigurasi Adapter Jaringan VirtualBox (Solusi Permanen Bebas Ganti Wi-Fi):\n"
        "   - Pengaturan adapter VM diset ke mode NAT.\n"
        "   - Dibuat Port Forwarding langsung dari Host Laptop ke Guest Proxmox VM:\n"
        "     * Host Port 8006 -> Guest Port 8006 (Akses Web GUI Proxmox: https://localhost:8006)\n"
        "     * Host Port 2222 -> Guest Port 22 (Akses SSH Proxmox: ssh -p 2222 root@localhost)\n"
        "     * Host Port 3000 -> Guest Port 3000 (Akses Web Presensi: http://localhost:3000)\n"
        "   - Manfaat: Laptop bebas berpindah Wi-Fi kampus, kafe, hotspot smartphone, atau tanpa koneksi internet sama sekali tanpa pernah kehilangan IP Proxmox."
    )
    doc.add_paragraph(
        "3. Instalasi ISO Proxmox:\n"
        "   - Pasang file ISO 'proxmox-ve_8.x.iso' ke CD drive virtual.\n"
        "   - Jalankan wizard instalasi grafis: pilih target disk, negara Indonesia, zona waktu Asia/Jakarta, email, serta password root 'mufid123'.\n"
        "   - Reboot VM dan verifikasi Proxmox telah siap menerima koneksi."
    )

    add_h2("2.2 Tahap 2: Konfigurasi Jaringan & Routing Internal Proxmox Host")
    doc.add_paragraph(
        "Di dalam Proxmox dibuat dua virtual bridge Linux pada file /etc/network/interfaces:"
    )
    doc.add_paragraph(
        "- vmbr0: Menghubungkan antarmuka virtual mesin (nic0) ke VirtualBox NAT untuk akses luar dan internet.\n"
        "- vmbr1: Bridge virtual lokal terisolasi (subnet 10.10.10.1/24) sebagai switch lokal antar ketiga kontainer LXC."
    )
    doc.add_paragraph("Konfigurasi /etc/network/interfaces:")
    add_code_block(doc, """auto lo
iface lo inet loopback

iface nic0 inet manual

auto vmbr0
iface vmbr0 inet dhcp
    bridge-ports nic0
    bridge-stp off
    bridge-fd 0
    post-up iptables-restore < /etc/iptables.rules

auto vmbr1
iface vmbr1 inet static
    address 10.10.10.1/24
    bridge-ports none
    bridge-stp off
    bridge-fd 0
    post-up iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o vmbr0 -j MASQUERADE
    post-down iptables -t nat -D POSTROUTING -s 10.10.10.0/24 -o vmbr0 -j MASQUERADE""")

    doc.add_paragraph(
        "Pengaturan Routing & Port Forwarding iptables:\n"
        "1. Mengaktifkan IP forwarding permanen: net.ipv4.ip_forward = 1 di /etc/sysctl.d/99-ipforward.conf.\n"
        "2. Port Forwarding DNAT: Port 3000 pada Proxmox otomatis diteruskan ke IP lokal Frontend (10.10.10.100:80):\n"
        "   iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 3000 -j DNAT --to-destination 10.10.10.100:80\n"
        "3. Aturan disimpan permanen dengan perintah: iptables-save > /etc/iptables.rules."
    )

    add_h2("2.3 Tahap 3: Pembuatan & Konfigurasi Tiga Kontainer LXC Multi-Distro")
    doc.add_paragraph(
        "Pada Web GUI Proxmox (menu local -> CT Templates), diunduh tiga template sistem operasi kontainer:\n"
        "- alpine-3.20-default\n"
        "- ubuntu-24.04-standard\n"
        "- debian-12-standard"
    )
    doc.add_paragraph("Pembuatan dan spesifikasi tiap kontainer:")
    
    # Table of LXC
    tbl_lxc = doc.add_table(rows=1, cols=4)
    tbl_lxc.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = tbl_lxc.rows[0].cells
    hdr[0].text = "Parameter"
    hdr[1].text = "LXC 100 (Frontend)"
    hdr[2].text = "LXC 101 (Backend)"
    hdr[3].text = "LXC 102 (Database)"
    for cell in hdr:
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(10)

    rows_data = [
        ("Distribusi OS", "Alpine Linux 3.20", "Ubuntu 24.04 LTS", "Debian 12 Bookworm"),
        ("C Library Runtime", "musl libc", "GNU glibc", "GNU glibc"),
        ("Alokasi CPU / RAM", "1 Core / 512 MB", "1 Core / 512 MB", "1 Core / 512 MB"),
        ("Ukuran Disk", "8 GB", "8 GB", "8 GB"),
        ("Jaringan Bridge", "vmbr1", "vmbr1", "vmbr1"),
        ("IP Internal", "10.10.10.100/24", "10.10.10.101/24", "10.10.10.102/24"),
        ("IP Gateway / DNS", "10.10.10.1 / 8.8.8.8", "10.10.10.1 / 8.8.8.8", "10.10.10.1 / 8.8.8.8"),
        ("Layanan Utama", "Nginx Web Server", "FastAPI + Uvicorn", "PostgreSQL 15 RDBMS")
    ]
    for rdata in rows_data:
        row = tbl_lxc.add_row().cells
        for idx, val in enumerate(rdata):
            row[idx].text = val
            set_cell_margins(row[idx], top=80, bottom=80, left=100, right=100)
            if idx == 0:
                row[idx].paragraphs[0].runs[0].font.bold = True
            for r in row[idx].paragraphs[0].runs:
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(51, 65, 85)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    doc.add_paragraph(
        "Aktivasi Fitur Esensial di Proxmox Shell:\n"
        "pct set 100 -features nesting=1 -onboot 1\n"
        "pct set 101 -features nesting=1 -onboot 1\n"
        "pct set 102 -features nesting=1 -onboot 1\n"
        "(Fitur nesting=1 wajib agar systemd di Ubuntu dan Debian dapat berjalan normal, sedangkan onboot=1 memastikan ketiga kontainer otomatis hidup saat Proxmox booting)."
    )

    add_h2("2.4 Tahap 4: Konfigurasi TUN Passthrough & Tailscale Mesh WireGuard")
    doc.add_paragraph(
        "Kontainer LXC secara default tidak memiliki izin membuat interface jaringan virtual (TUN/TAP). Agar Tailscale dapat membuat interface wireguard 'tailscale0', dilakukan device passthrough pada konfigurasi host Proxmox (/etc/pve/lxc/{100,101,102}.conf):"
    )
    add_code_block(doc, """lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file""")

    doc.add_paragraph(
        "Instalasi dan Autentikasi Tailscale:\n"
        "1. Di Alpine (LXC 100): apk add tailscale && rc-service tailscale start\n"
        "2. Di Ubuntu (LXC 101) & Debian (LXC 102): curl -fsSL https://tailscale.com/install.sh | sh\n"
        "3. Login Mesh: Menjalankan 'tailscale up' di masing-masing kontainer dan mengotorisasi perangkat ke akun Tailscale (ailiraliraiza@).\n"
        "4. Alamat IP Statis Tailscale Mesh yang Terbentuk:\n"
        "   - Frontend: 100.119.108.66\n"
        "   - Backend: 100.119.201.56\n"
        "   - DB-Server: 100.115.151.38\n"
        "   - Laptop Client: 100.97.41.41"
    )

    add_h2("2.5 Tahap 5: Setup & Pengamanan Database PostgreSQL 15 (LXC 102 Debian)")
    doc.add_paragraph(
        "1. Instalasi DBMS: Menginstal package postgresql-15 di Debian 12.\n"
        "2. Pengaturan Remote Listen: Mengubah listen_addresses = '*' pada /etc/postgresql/15/main/postgresql.conf.\n"
        "3. Keamanan Tingkat Lanjut (/etc/postgresql/15/main/pg_hba.conf):\n"
        "   Membatasi hak akses login basis data hanya dari IP Tailscale Backend (100.119.201.56/32) dan IP lokal (10.10.10.0/24) dengan enkripsi password scram-sha-256:\n"
        "   host  attendance_db  sister_user  100.119.201.56/32  scram-sha-256\n"
        "   host  attendance_db  sister_user  10.10.10.0/24      scram-sha-256\n"
        "4. Pembuatan Database & Skema Relasional:\n"
        "   - User: sister_user | Password: sister_secure_pass_2026 | Database: attendance_db.\n"
        "   - Tabel courses: Menyimpan kode mata kuliah, nama kelas, dan dosen pengampu.\n"
        "   - Tabel sessions: Menyimpan sesi presensi aktif dengan token acak dan waktu kadaluwarsa.\n"
        "   - Tabel students: Menyimpan profil mahasiswa (NIM, Nama, Program Studi).\n"
        "   - Tabel attendances: Menyimpan catatan presensi dengan konstrain unik UNIQUE(session_id, nim) untuk mencegah kecurangan double submit.\n"
        "   - Tabel node_logs: Menyimpan jejak audit terdistribusi per simpul."
    )

    add_h2("2.6 Tahap 6: Setup & Pengembangan Backend Microservice (LXC 101 Ubuntu)")
    doc.add_paragraph(
        "1. Lingkungan Kerja: Membuat virtual environment Python 3.12 di /opt/backend/venv serta menginstal pustaka fastapi, uvicorn, psycopg2-binary, dan pydantic.\n"
        "2. Pengembangan File main.py:\n"
        "   - Multi-Host Connection Pool: Terhubung ke PostgreSQL via Tailscale (100.115.151.38:5432) dan cadangan IP lokal (10.10.10.102:5432).\n"
        "   - Endpoint POST /api/attend: Memvalidasi keaktifan sesi, token perkuliahan, dan mencatat presensi mahasiswa secara ACID.\n"
        "   - Endpoint POST /api/auth/login: Otentikasi dosen pengampu (Kredensial: dosen / kelompok5).\n"
        "   - Endpoint Manajemen Sesi: POST /api/sessions (buat sesi), PUT /api/sessions/{id}/toggle (buka/tutup sesi real-time).\n"
        "   - Endpoint Telemetri: GET /api/health dan GET /api/cluster mengukur latensi round-trip (RTT) antar node klaster secara periodik.\n"
        "3. Systemd Service (/etc/systemd/system/sister-backend.service):\n"
        "   Dikonfigurasi auto-restart (Restart=always, RestartSec=3) sehingga backend otomatis aktif kembali jika terjadi gangguan."
    )

    add_h2("2.7 Tahap 7: Setup Frontend & Nginx Reverse Proxy (LXC 100 Alpine)")
    doc.add_paragraph(
        "1. Instalasi Nginx: Nginx diinstal di Alpine Linux untuk efisiensi memori yang ekstrem.\n"
        "2. Konfigurasi Reverse Proxy (/etc/nginx/http.d/default.conf):\n"
        "   - Menyajikan file statis dari direktori /var/www/html.\n"
        "   - Mem-proxy seluruh request rute /api/ langsung melalui jaringan Tailscale ke Backend (http://100.119.201.56:8000/api/).\n"
        "3. Arsitektur Multi-Page Terpisah:\n"
        "   - /index.html: Portal Mahasiswa untuk mengisi absensi berdasar token sesi.\n"
        "   - /login.html: Halaman Otentikasi Dosen Pengampu.\n"
        "   - /dosen/index.html: Dashboard Konsol Dosen dengan navigasi sidebar: Ringkasan Eksekutif, Manajemen Sesi Buka/Tutup, Rekapitulasi Presensi (pencarian & ekspor CSV), serta Pemantau Spek Hardware & Latensi WireGuard 3 Node Klaster."
    )

    add_h2("2.8 Tahap 8: Otomasi Deployment & Konfigurasi Bebas Ganti Wi-Fi")
    doc.add_paragraph(
        "1. Script Otomasi deploy.sh:\n"
        "   Dibuat script bash di laptop yang secara otomatis mengunggah seluruh perubahan file frontend dan backend langsung menembus port 2222 Proxmox via SSH, lalu mendorongnya ke kontainer LXC terkait menggunakan perintah 'pct push' dan me-reload layanan Nginx / systemd.\n"
        "2. Script cari-ip.sh:\n"
        "   Script cepat untuk memvalidasi kesiapan port localhost:8006 dan localhost:3000 pada laptop.\n"
        "3. Update Banner /etc/issue di Proxmox:\n"
        "   Tampilan layar hitam konsol Proxmox diperbarui agar menampilkan panduan akses permanen 'https://localhost:8006' dan 'http://localhost:3000'."
    )

    # ==================== BAB III ====================
    add_h1("BAB III: TOPOLOGI JARINGAN & TABEL PENGALAMATAN IP")
    
    tbl_net = doc.add_table(rows=1, cols=5)
    tbl_net.alignment = WD_TABLE_ALIGNMENT.CENTER
    nhdr = tbl_net.rows[0].cells
    nhdr[0].text = "Simpul / Perangkat"
    nhdr[1].text = "Hostname"
    nhdr[2].text = "IP Internal (vmbr1)"
    nhdr[3].text = "IP Tailscale Mesh"
    nhdr[4].text = "Port & Layanan Terbuka"
    for cell in nhdr:
        set_cell_background(cell, "0E7490")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(10)

    net_data = [
        ("Host Laptop (Arch Linux)", "archlinux", "192.168.0.142 (WiFi)", "100.97.41.41", "Browser Client & SSH Terminal"),
        ("Hypervisor Proxmox Host", "pve-lab", "10.10.10.1 (Gateway)", "Statis Host", "8006 (GUI), 22 (SSH), 3000 (App)"),
        ("Tier 1: Frontend (Alpine)", "frontend", "10.10.10.100", "100.119.108.66", "80 (HTTP / Nginx Reverse Proxy)"),
        ("Tier 2: Backend (Ubuntu)", "backend", "10.10.10.101", "100.119.201.56", "8000 (FastAPI Uvicorn REST API)"),
        ("Tier 3: Database (Debian)", "db-server", "10.10.10.102", "100.115.151.38", "5432 (PostgreSQL 15 RDBMS)")
    ]
    for nd in net_data:
        row = tbl_net.add_row().cells
        for idx, val in enumerate(nd):
            row[idx].text = val
            set_cell_margins(row[idx], top=80, bottom=80, left=100, right=100)
            if idx == 0:
                row[idx].paragraphs[0].runs[0].font.bold = True
            for r in row[idx].paragraphs[0].runs:
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(51, 65, 85)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ==================== BAB IV ====================
    add_h1("BAB IV: HASIL PENGUJIAN SISTEM (VERIFIKASI FITUR)")
    doc.add_paragraph("Seluruh pengujian sistem dilakukan secara otomatis dan menghasilkan 100% lulus (PASS):")
    
    test_cases = [
        ("Uji 1: Healthcheck Klaster", "Memanggil GET /api/health melalui Nginx. Respon 'status': 'healthy', RTT WireGuard PostgreSQL 0.74 ms."),
        ("Uji 2: Validasi Presensi Mahasiswa", "Mahasiswa submit NIM 230005 dengan token SISTER24. Data berhasil tersimpan di PostgreSQL."),
        ("Uji 3: Idempotensi & Anti-Double Submit", "Mahasiswa submit ulang dengan NIM yang sama. Sistem menolak dengan HTTP 409 Conflict ('NIM sudah tercatat hadir')."),
        ("Uji 4: Penolakan Sesi Ditutup", "Sesi dinonaktifkan via dashboard dosen. Mahasiswa yang mencoba absen ditolak dengan pesan sesi telah ditutup."),
        ("Uji 5: Otentikasi Peran Dosen", "Login di /login.html dengan kredensial dosen/kelompok5 berhasil dan mengembalikan token sesi serta hak akses konsol."),
        ("Uji 6: Port Forwarding Bebas Wi-Fi", "Akses Proxmox via https://localhost:8006 dan Web App via http://localhost:3000 terbukti berhasil dibuka lancar tanpa bergantung pada subnet router Wi-Fi.")
    ]
    for tc, desc in test_cases:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r_tc = p.add_run(f"• {tc}: ")
        r_tc.bold = True
        r_tc.font.color.rgb = RGBColor(30, 58, 138)
        p.add_run(desc)

    # ==================== BAB V ====================
    add_h1("BAB V: PANDUAN OPERASIONAL SEHARI-HARI")
    doc.add_paragraph(
        "1. Menyalakan Sistem Setelah Laptop Dimatikan:\n"
        "   - Buka Oracle VirtualBox di laptop.\n"
        "   - Pilih VM 'Proxmox-Lab' dan klik Start (atau jalankan: VBoxManage startvm Proxmox-Lab --type headless).\n"
        "   - Tunggu sekitar 30 detik agar Proxmox dan 3 kontainer selesai booting otomatis.\n"
        "   - Buka browser Anda:\n"
        "     * Proxmox GUI: https://localhost:8006\n"
        "     * Web Presensi: http://localhost:3000\n"
        "     * Dashboard Dosen: http://localhost:3000/dosen/\n\n"
        "2. Mengunggah Perubahan Kode di Masa Depan:\n"
        "   - Edit kode HTML/CSS di folder 'frontend/' atau Python di folder 'backend/'.\n"
        "   - Buka terminal di direktori proyek dan jalankan script otomatis:\n"
        "     ./deploy.sh\n"
        "   - Script akan otomatis mengunggah dan me-reload aplikasi dalam hitungan 3 detik."
    )

    doc.save(output_path)
    print(f"✅ Dokumen berhasil dibuat di: {output_path}")

if __name__ == "__main__":
    create_document("/home/mufidd/Coding/Projects/sister-project/LAPORAN_LENGKAP_DAN_ALUR_PEMBUATAN_PROYEK_UTS.docx")
