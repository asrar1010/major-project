import subprocess
import sys
import yaml
from pathlib import Path

SSH_USER = "ubuntu"
REMOTE_PROVISIONING_SCRIPT_PATH = "/tmp"

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

def update_promentheus_config(side_vm_dns: list):
    local_script = Path(__file__).resolve().parent / "provisioning/prometheus.yml"
    if not local_script.exists():
        print(f"❌ Local script not found: {local_script}")
        sys.exit(1)
    # Step 1: Read the YAML
    with open(local_script, "r") as f:
        data = yaml.safe_load(f)

    # Step 2: Prepare targets
    targets = [f"{vm}:9100" for vm in side_vm_dns]
    print(targets)

    # Step 3: Update scrape_configs
    data['scrape_configs'][0]['static_configs'] = [{"targets": targets}]

    # Step 4: Write back to YAML
    with open(local_script, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

def install_observability(private_key_path, main_vm_dns, side_vm_dns):

    # Resolve local provisioning script path relative to this Python file
    provisioning_script_path = Path(__file__).resolve().parent / "provisioning"

    print(f"🚀 Installing Observability on {main_vm_dns}")
    update_promentheus_config(side_vm_dns=side_vm_dns)

    # SCP the script to the remote host
    scp_cmd = [
        "scp",
        "-r",
        "-i", private_key_path,
        "-o", "StrictHostKeyChecking=no",
        str(provisioning_script_path),
        f"{SSH_USER}@{main_vm_dns}:{REMOTE_PROVISIONING_SCRIPT_PATH}",
    ]
    run(scp_cmd)

    # Run the script remotely (chmod +x && sudo run)
    ssh_cmd = [
        "ssh",
        "-i", private_key_path,
        "-o", "StrictHostKeyChecking=no",
        f"{SSH_USER}@{main_vm_dns}",
        f"chmod -R a+x {REMOTE_PROVISIONING_SCRIPT_PATH}/provisioning && {REMOTE_PROVISIONING_SCRIPT_PATH}/provisioning/install_observability.sh",
    ]
    run(ssh_cmd)

