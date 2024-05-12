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

def main():
    create_folders()    
    if subprocess.run(["cargo", "--version"]).returncode != 0:
        subprocess.run(["curl", "--proto", "=https", "--tlsv1.2", "-sSf", "https://sh.rustup.rs", "|", "sh"])
        return
    
    execute_commands()

if __name__ == "__main__":
    main()
