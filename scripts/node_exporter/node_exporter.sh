#!/bin/bash
set -e

NODE_EXPORTER_VERSION="1.8.2"
ARCH="linux-amd64"
USER="node_exporter"

echo "Installing Node Exporter v${NODE_EXPORTER_VERSION}"

# Create user if not exists
if ! id "$USER" &>/dev/null; then
  useradd --no-create-home --shell /bin/false $USER
fi

# Download Node Exporter
cd /tmp
wget -q https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.${ARCH}.tar.gz

# Extract and install
tar xzf node_exporter-${NODE_EXPORTER_VERSION}.${ARCH}.tar.gz
cp node_exporter-${NODE_EXPORTER_VERSION}.${ARCH}/node_exporter /usr/local/bin/
chown $USER:$USER /usr/local/bin/node_exporter

# Create systemd service
cat <<EOF >/etc/systemd/system/node_exporter.service
[Unit]
Description=Prometheus Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=$USER
Group=$USER
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

echo "Node Exporter installed and running on port 9100"
