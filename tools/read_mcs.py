import argparse
import subprocess
import re

def get_wifi_info(ifname):
    try:
        # Run the iw dev <ifname> link command
        result = subprocess.run(['iw', 'dev', ifname, 'link'], capture_output=True, text=True, check=True)
        output = result.stdout

        # Regex pattern to find the MCS value
        mcs_pattern = re.compile(r'MCS (\d+)')
        # Regex pattern to find the TX bitrate
        tx_bitrate_pattern = re.compile(r'tx bitrate: (\d+(\.\d+)?)')

        # Search for the MCS value in the output
        mcs_match = mcs_pattern.search(output)
        if mcs_match:
            mcs_value = mcs_match.group(1)
        else:
            mcs_value = "MCS value not found."

        # Search for the TX bitrate in the output
        tx_bitrate_match = tx_bitrate_pattern.search(output)
        if tx_bitrate_match:
            tx_bitrate_value = tx_bitrate_match.group(1) + " Mbps"
        else:
            tx_bitrate_value = "TX bitrate not found."

        return mcs_value, tx_bitrate_value

    except subprocess.CalledProcessError as e:
        return f"Failed to run command: {e}", None
    except Exception as e:
        return f"An error occurred: {str(e)}", None

def main():
    parser = argparse.ArgumentParser(description="Get MCS value and TX bitrate from iw dev <ifname> link output.")
    parser.add_argument('ifname', type=str, help='The network interface name')
    args = parser.parse_args()

    mcs_value, tx_bitrate_value = get_wifi_info(args.ifname)
    # print(f"MCS value for interface {args.ifname}: {mcs_value}")
    print(f"TX bitrate for interface: {tx_bitrate_value}")

if __name__ == "__main__":
    main()