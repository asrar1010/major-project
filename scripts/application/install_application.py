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


def install_application(private_key_path, side_vm_dns):
    if len(side_vm_dns) != 2:
        print(f"❌ Side VM DNS should be 2: {side_vm_dns}")
        sys.exit(1)
    # Resolve local provisioning script path relative to this Python file
    provisioning_script_path = Path(__file__).resolve().parent / "provisioning"

    print(f"🚀 Installing Application on {side_vm_dns}")

    # SCP the script to the remote host
    scp_cmd = [
        "scp",
        "-r",
        "-i", private_key_path,
        "-o", "StrictHostKeyChecking=no",
        str(provisioning_script_path),
        f"{SSH_USER}@{side_vm_dns[0]}:{REMOTE_PROVISIONING_SCRIPT_PATH}",
    ]
    run(scp_cmd)
    scp_cmd = [
        "scp",
        "-r",
        "-i", private_key_path,
        "-o", "StrictHostKeyChecking=no",
        str(provisioning_script_path),
        f"{SSH_USER}@{side_vm_dns[1]}:{REMOTE_PROVISIONING_SCRIPT_PATH}",
    ]
    run(scp_cmd)

    # Run the script remotely (chmod +x && sudo run)
    ssh_cmd = [
        "ssh",
        "-i", private_key_path,
        "-o", "StrictHostKeyChecking=no",
        f"{SSH_USER}@{side_vm_dns[0]}",
        f"chmod -R a+x {REMOTE_PROVISIONING_SCRIPT_PATH}/provisioning && {REMOTE_PROVISIONING_SCRIPT_PATH}/provisioning/install_application.sh instance_01",
    ]
    run(ssh_cmd)
    ssh_cmd = [
        "ssh",
        "-i", private_key_path,
        "-o", "StrictHostKeyChecking=no",
        f"{SSH_USER}@{side_vm_dns[1]}",
        f"chmod -R a+x {REMOTE_PROVISIONING_SCRIPT_PATH}/provisioning && {REMOTE_PROVISIONING_SCRIPT_PATH}/provisioning/install_application.sh instance_02",
    ]
    run(ssh_cmd)
