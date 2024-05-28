import subprocess
import re
import argparse

def get_wireless_channel(interface):
    try:
        output = subprocess.check_output(['iw', 'dev', interface, 'info']).decode('utf-8')
        match = re.search(r'channel\s+(\d+)', output)
        if match:
            return int(match.group(1))
        
        ## Try with iw dev link, use frequency
        output = subprocess.check_output(['iw', 'dev', interface, 'link']).decode('utf-8')
        match = re.search(r'freq:\s+(\d+)', output)
        if match:
            freq = int(match.group(1))
            if 2412 <= freq <= 2484:
                return (freq - 2412) // 5 + 1
            elif 5180 <= freq <= 5825:
                return (freq - 5180) // 5 + 36
        return None
    except subprocess.CalledProcessError:
        return None

def get_band_from_channel(channel):
    if channel is None:
        return "Unknown"
    if 1 <= channel <= 14:
        return "2.4 GHz"
    elif 36 <= channel <= 165:
        return "5 GHz"
    else:
        return "Unknown"

def main():
    parser = argparse.ArgumentParser(description="Retrieve channel information for a wireless interface")
    parser.add_argument("-i", "--interface", help="Name of the wireless interface (e.g., wlan0)")
    args = parser.parse_args()

    channel = get_wireless_channel(args.interface)
    band    = get_band_from_channel(channel)
    print(band)

if __name__ == "__main__":
    main()
