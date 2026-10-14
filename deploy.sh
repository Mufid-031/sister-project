#!/usr/bin/env bash
# ==============================================================================
# SCRIPT DEPLOY OTOMATIS: SISTEM PRESENSI TERDISTRIBUSI
# Digunakan untuk mengunggah perubahan kode dari laptop ke kontainer Proxmox
# ==============================================================================

set -e

PROXMOX_HOST="192.168.100.57"
PROXMOX_USER="root"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 [1/4] Mengunggah perubahan Frontend (LXC 100 - Alpine)..."
scp "${BASE_DIR}/frontend/index.html" "${PROXMOX_USER}@${PROXMOX_HOST}:/tmp/index.html"
ssh "${PROXMOX_USER}@${PROXMOX_HOST}" "
    pct push 100 /tmp/index.html /var/www/html/index.html
    pct exec 100 -- chmod 644 /var/www/html/index.html
    pct exec 100 -- rc-service nginx reload
    rm /tmp/index.html
"
echo "✅ Frontend berhasil diperbarui!"

echo "🚀 [2/4] Mengunggah perubahan Backend (LXC 101 - Ubuntu)..."
scp "${BASE_DIR}/backend/main.py" "${PROXMOX_USER}@${PROXMOX_HOST}:/tmp/main.py"
ssh "${PROXMOX_USER}@${PROXMOX_HOST}" "
    pct push 101 /tmp/main.py /opt/backend/main.py
    pct exec 101 -- chown root:root /opt/backend/main.py
    pct exec 101 -- systemctl restart sister-backend
    rm /tmp/main.py
"
echo "✅ Backend berhasil diperbarui dan service di-restart!"

echo "🚀 [3/4] Menguji status kesehatan sistem (Healthcheck)..."
sleep 2
HEALTH_RES=$(curl -s --connect-timeout 3 http://${PROXMOX_HOST}:3000/api/health || true)

if echo "$HEALTH_RES" | grep -q '"status":"healthy"'; then
    echo "🎉 SISTEM ONLINE & SEHAT!"
    echo "   - Web HTTPS : https://${PROXMOX_HOST}:3443"
    echo "   - Web HTTP  : http://${PROXMOX_HOST}:3000"
    echo "   - Tailscale : http://100.91.242.11"
else
    echo "⚠️ Peringatan: Respon healthcheck tidak normal. Output:"
    echo "$HEALTH_RES"
fi
echo "=============================================================================="
