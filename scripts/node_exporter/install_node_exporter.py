import subprocess
import sys
import requests
import time
from pathlib import Path

SSH_USER = "ubuntu"
REMOTE_SCRIPT = "/tmp/node_exporter.sh"

def run(cmd, capture_output=False):
    print("▶", " ".join(cmd))
    try:
        if capture_output:
            res = subprocess.run(cmd, check=True, text=True, capture_output=True)
            print(res.stdout, res.stderr)
            return res
        else:
            subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if hasattr(e, 'stdout') and e.stdout:
            print("stdout:", e.stdout)
        if hasattr(e, 'stderr') and e.stderr:
            print("stderr:", e.stderr)
        sys.exit(e.returncode)

def check_node_exporter_http(vm_dns, port=9100, timeout=5):
    url = f"http://{vm_dns}:{port}/metrics"
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ Node Exporter is running on {vm_dns}")
            return True
        else:
            print(f"⚠️ Node Exporter returned status {response.status_code} on {vm_dns}")
            return False
    except requests.RequestException as e:
        print(f"❌ Node Exporter check failed on {vm_dns}: {e}")
        sys.exit(1)

def install_node_exporter(private_key_path,vm_dns):

    private_key = private_key_path
    vm_dns = vm_dns

    # Resolve local script path relative to this Python file
    local_script = Path(__file__).resolve().parent / "node_exporter.sh"
    if not local_script.exists():
        print(f"❌ Local script not found: {local_script}")
        sys.exit(1)

    print(f"🚀 Installing Node Exporter on {vm_dns}")

    # SCP the script to the remote host
    scp_cmd = [
        "scp",
        "-i", private_key,
        "-o", "StrictHostKeyChecking=no",
        str(local_script),
        f"{SSH_USER}@{vm_dns}:{REMOTE_SCRIPT}",
    ]
    run(scp_cmd)

    # Run the script remotely (chmod +x && sudo run)
    ssh_cmd = [
        "ssh",
        "-i", private_key,
        "-o", "StrictHostKeyChecking=no",
        f"{SSH_USER}@{vm_dns}",
        f"chmod +x {REMOTE_SCRIPT} && sudo {REMOTE_SCRIPT}",
    ]
    run(ssh_cmd)
    time.sleep(10)
    check_node_exporter_http(vm_dns=vm_dns)
