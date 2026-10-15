#!/usr/bin/env bash
# ==============================================================================
# SCRIPT PENGECEK KONEKSI & IP PROXMOX (BEBAS GANTI WIFI)
# ==============================================================================

echo "🔍 Memeriksa status akses Proxmox & Sistem Terdistribusi..."

# 1. Cek Port Forwarding Localhost (Solusi Permanen Bebas Ganti WiFi)
if curl -k -s --connect-timeout 2 https://localhost:8006 >/dev/null 2>&1; then
    echo "=========================================================="
    echo "🎉 PROXMOX AKTIF & SIAP DIAKSES (PORT FORWARDING AKTIF)!"
    echo "=========================================================="
    echo "💡 Bebas ganti WiFi apa pun tanpa perlu cari-cari IP lagi:"
    echo "👉 Proxmox Web GUI  : https://localhost:8006  (atau https://127.0.0.1:8006)"
    echo "👉 Web Presensi     : http://localhost:3000"
    echo "👉 Login Dosen      : http://localhost:3000/login.html"
    echo "👉 Dashboard Dosen  : http://localhost:3000/dosen/"
    echo "👉 SSH Proxmox      : ssh -p 2222 root@localhost"
    echo "👉 Tailscale Mesh   : http://100.119.108.66"
    echo "=========================================================="
    exit 0
fi

# 2. Jika localhost belum terbuka, coba deteksi via IP LAN/WiFi
SUBNET=$(ip route | grep default | awk '{print $3}' | cut -d'.' -f1-3)
if [ -n "$SUBNET" ]; then
    PVE_MAC="08:00:27:1a:3f:fa"
    PVE_IP=$(ip neigh show | grep -i "$PVE_MAC" | awk '{print $1}' | head -n 1)

    if [ -z "$PVE_IP" ]; then
        echo "⚡ Melakukan scan cepat di subnet ${SUBNET}.0/24..."
        for i in $(seq 1 254); do
            (ping -c 1 -W 1 "${SUBNET}.$i" >/dev/null 2>&1 &)
        done
        wait
        PVE_IP=$(ip neigh show | grep -i "$PVE_MAC" | awk '{print $1}' | head -n 1)
    fi

    if [ -n "$PVE_IP" ]; then
        echo "=========================================================="
        echo "🎉 PROXMOX DITEMUKAN PADA IP JARINGAN: $PVE_IP"
        echo "=========================================================="
        echo "👉 Proxmox Web GUI  : https://${PVE_IP}:8006"
        echo "👉 Web Presensi     : http://${PVE_IP}:3000"
        echo "=========================================================="
        exit 0
    fi
fi

echo "⚠️ Proxmox belum terdeteksi aktif. Pastikan VM 'Proxmox-Lab' di VirtualBox sudah Running."
