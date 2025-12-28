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


def update_lb_config(main_vm_dns: str,side_vm_dns: list):
    local_script = Path(__file__).resolve().parent / "provisioning/config.yml"

    if not local_script.exists():
        print(f"❌ Local script not found: {local_script}")
        sys.exit(1)

    if len(side_vm_dns) != 2:
        print(f"❌ Requires 2 Side VM DNS Names: {side_vm_dns}")
        sys.exit(1)

    # Read the YAML
    with open(local_script, "r") as f:
        data = yaml.safe_load(f)
    
    side_vm1 = side_vm_dns[0]
    side_vm2 = side_vm_dns[1]

    data['prometheus']['url'] = f'http://{main_vm_dns}:9090/api/v1/query'

    data['servers']['vm1'] = f'{side_vm1}:5000'
    data['servers']['vm2'] = f'{side_vm2}:5000'

    data['instances']['vm1'] = f'{side_vm1}:9100'
    data['instances']['vm2'] = f'{side_vm2}:9100'

    # Write back to YAML
    with open(local_script, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

def install_lb(private_key_path, main_vm_dns, side_vm_dns):
    # Resolve local provisioning script path relative to this Python file
    provisioning_script_path = Path(__file__).resolve().parent / "provisioning"

    print(f"🚀 Installing Load Balancer on {main_vm_dns}")
    update_lb_config(main_vm_dns=main_vm_dns, side_vm_dns=side_vm_dns)

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
        f"chmod -R a+x {REMOTE_PROVISIONING_SCRIPT_PATH}/provisioning && {REMOTE_PROVISIONING_SCRIPT_PATH}/provisioning/install_loadbalancer.sh",
    ]
    run(ssh_cmd)
