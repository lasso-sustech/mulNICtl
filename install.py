import os
import subprocess
import json

def create_folders():
    # Create main folders if they don't exist
    folders = ["temp", "config", "config/stream", "config/topo", "expSrc", "stream-replay/data", "stream-replay/logs"]
    for folder in folders:
        if not os.path.exists(folder):
            os.mkdir(folder)
            
def execute_commands():
    # Execute commands
    subprocess.run(["cargo", "build", "--release"], cwd="stream-replay")
    subprocess.run(["cargo", "build", "--release"], cwd="stream-replay-rx")
    
def pip_install():
    # if pip is not installed, install it
    try:
        subprocess.run(["pip", "--version"])
    except FileNotFoundError:
        subprocess.run(["sudo", "apt", "install", "python3-pip", "-y"])
        
    ## install required packages
    with open("requirements.txt") as f:
        packages = f.read().splitlines()
    for package in packages:
        subprocess.run(["pip", "install", package])    
        
def cargo_install():
    try:
        subprocess.run(["cargo", "--version"])
    except Exception as e:
        subprocess.run(["curl", "--proto", "=https", "--tlsv1.2", "-sSf", "https://sh.rustup.rs", "|", "sh"])
        

def main():
    create_folders()    
    cargo_install()
    execute_commands()
    pip_install()

if __name__ == "__main__":
    main()
