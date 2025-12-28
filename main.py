import os
import subprocess
import time
import sys
import json
import requests
from scripts.node_exporter.install_node_exporter import install_node_exporter
from scripts.observability.install_observability import install_observability
from scripts.loadbalancer.install_lb import install_lb
from scripts.application.install_application import install_application

# CONFIG
PROJECT_ROOT_DIR = os.getcwd()
TERRAFORM_DIR    = os.path.join(PROJECT_ROOT_DIR, "terraform")
SCRIPTS_DIR      = os.path.join(PROJECT_ROOT_DIR, "scripts", "node_exporter")
PRIVATE_KEY_PATH = os.path.join(PROJECT_ROOT_DIR, "terraform", "private")

def run(cmd, cwd=None):
    print(f"\n▶ {cmd}")
    return subprocess.run(cmd, shell=True, cwd=cwd, check=True, capture_output=True, text=True)

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

def start():

    print("🚀 Running Terraform apply...")
    run("terraform init -input=false", cwd=TERRAFORM_DIR)
    run("terraform apply -auto-approve", cwd=TERRAFORM_DIR)

    print("⏳ Waiting for EC2 instances to boot...")
    time.sleep(60)

    vms_dns = list(json.loads(run("terraform output -json ec2_public_dns", cwd=TERRAFORM_DIR).stdout).values())
    main_vm_dns = vms_dns.pop(0)
    side_vm_dns = vms_dns

    for vm_dns in side_vm_dns:
        install_node_exporter(private_key_path=PRIVATE_KEY_PATH,vm_dns=vm_dns)

    print("✅ Node Exporter installation completed")

    install_observability(private_key_path=PRIVATE_KEY_PATH,main_vm_dns=main_vm_dns, side_vm_dns=side_vm_dns)
    install_application(private_key_path=PRIVATE_KEY_PATH,side_vm_dns=side_vm_dns)
    install_lb(private_key_path=PRIVATE_KEY_PATH,main_vm_dns=main_vm_dns,side_vm_dns=side_vm_dns)

    print("✅ Setup complete!")

def stop():
    run("terraform destroy -auto-approve", cwd=TERRAFORM_DIR)

if __name__ == "__main__":
    try:
        print("1. Start")
        print("2. Stop")
        option = int(input("Choose an option: "))
        if option not in [1,2]:
            print("Invalid Option")
            sys.exit(1)
        if option == 1:
            start()
        elif option == 2:
            stop()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)
