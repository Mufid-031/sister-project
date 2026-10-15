#!/usr/bin/env bash
# ==============================================================================
# SCRIPT DEPLOY OTOMATIS: SISTEM PRESENSI TERDISTRIBUSI (KELOMPOK 5)
# ==============================================================================

set -e

PROXMOX_HOST="${PROXMOX_HOST:-127.0.0.1}"
PROXMOX_PORT="${PROXMOX_PORT:-2222}"
PROXMOX_USER="root"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Target Host Proxmox: $PROXMOX_HOST:$PROXMOX_PORT"

echo "📦 [1/3] Mengunggah seluruh halaman Frontend (LXC 100 - Alpine)..."
ssh -p "$PROXMOX_PORT" -o StrictHostKeyChecking=no "${PROXMOX_USER}@${PROXMOX_HOST}" "mkdir -p /tmp/frontend_build/dosen"
scp -P "$PROXMOX_PORT" -o StrictHostKeyChecking=no "${BASE_DIR}/frontend/index.html" "${PROXMOX_USER}@${PROXMOX_HOST}:/tmp/frontend_build/index.html"
scp -P "$PROXMOX_PORT" -o StrictHostKeyChecking=no "${BASE_DIR}/frontend/login.html" "${PROXMOX_USER}@${PROXMOX_HOST}:/tmp/frontend_build/login.html"
scp -P "$PROXMOX_PORT" -o StrictHostKeyChecking=no "${BASE_DIR}/frontend/dosen/index.html" "${PROXMOX_USER}@${PROXMOX_HOST}:/tmp/frontend_build/dosen/index.html"
scp -P "$PROXMOX_PORT" -o StrictHostKeyChecking=no "${BASE_DIR}/frontend/nginx.conf" "${PROXMOX_USER}@${PROXMOX_HOST}:/tmp/frontend_build/nginx.conf"

ssh -p "$PROXMOX_PORT" -o StrictHostKeyChecking=no "${PROXMOX_USER}@${PROXMOX_HOST}" "
    pct exec 100 -- mkdir -p /var/www/html/dosen /etc/nginx/http.d
    pct push 100 /tmp/frontend_build/index.html /var/www/html/index.html
    pct push 100 /tmp/frontend_build/login.html /var/www/html/login.html
    pct push 100 /tmp/frontend_build/dosen/index.html /var/www/html/dosen/index.html
    pct push 100 /tmp/frontend_build/nginx.conf /etc/nginx/http.d/default.conf
    pct exec 100 -- chmod -R 755 /var/www/html
    pct exec 100 -- rc-service nginx reload
    rm -rf /tmp/frontend_build
"
echo "✅ Seluruh halaman Frontend & Nginx berhasil diperbarui!"

echo "📦 [2/3] Mengunggah perubahan Backend (LXC 101 - Ubuntu)..."
scp -P "$PROXMOX_PORT" -o StrictHostKeyChecking=no "${BASE_DIR}/backend/main.py" "${PROXMOX_USER}@${PROXMOX_HOST}:/tmp/main.py"
ssh -p "$PROXMOX_PORT" -o StrictHostKeyChecking=no "${PROXMOX_USER}@${PROXMOX_HOST}" "
    pct push 101 /tmp/main.py /opt/backend/main.py
    pct exec 101 -- chown root:root /opt/backend/main.py
    pct exec 101 -- systemctl restart sister-backend
    rm /tmp/main.py
"
echo "✅ Backend API berhasil diperbarui dan direstart!"

echo "📦 [3/3] Menguji status kesehatan sistem..."
sleep 2
HEALTH_RES=$(curl -s --connect-timeout 3 http://localhost:3000/api/health || true)

if echo "$HEALTH_RES" | grep -q '"status":"healthy"'; then
    echo "🎉 SISTEM ONLINE & SEHAT (100% WORKING)!"
    echo "   - Portal Mahasiswa : http://localhost:3000"
    echo "   - Login Dosen      : http://localhost:3000/login.html"
    echo "   - Dashboard Dosen  : http://localhost:3000/dosen/"
    echo "   - Proxmox Web GUI  : https://localhost:8006"
    echo "   - Tailscale Mesh   : http://100.119.108.66"
else
    echo "⚠️ Respon healthcheck:"
    echo "$HEALTH_RES"
fi
echo "=============================================================================="
