import os
import sys
import platform
import urllib.request
import subprocess

# Config
TAILWIND_VERSION = "v3.4.15"
BIN_DIR = os.path.join(os.path.dirname(__file__), ".bin")
INPUT_CSS = os.path.join(os.path.dirname(__file__), "titan_lms", "static", "css", "input.css")
OUTPUT_CSS = os.path.join(os.path.dirname(__file__), "titan_lms", "static", "css", "output.css")

def get_tailwind_url():
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    base_url = f"https://github.com/tailwindlabs/tailwindcss/releases/download/{TAILWIND_VERSION}/"
    
    if system == "windows":
        if "64" in machine or "x86_64" in machine:
            return base_url + "tailwindcss-windows-x64.exe", "tailwindcss.exe"
        else:
            return base_url + "tailwindcss-windows-x86.exe", "tailwindcss.exe"
    elif system == "darwin":
        if "arm" in machine or "aarch64" in machine:
            return base_url + "tailwindcss-macos-arm64", "tailwindcss"
        else:
            return base_url + "tailwindcss-macos-x64", "tailwindcss"
    elif system == "linux":
        if "arm" in machine or "aarch64" in machine:
            return base_url + "tailwindcss-linux-arm64", "tailwindcss"
        else:
            return base_url + "tailwindcss-linux-x64", "tailwindcss"
    else:
        raise Exception(f"Unsupported platform: {system} {machine}")

def main():
    try:
        url, exec_name = get_tailwind_url()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    os.makedirs(BIN_DIR, exist_ok=True)
    binary_path = os.path.join(BIN_DIR, exec_name)
    
    if not os.path.exists(binary_path):
        print(f"Tailwind CLI binary not found. Downloading from {url}...")
        try:
            # Custom User-Agent to prevent 403 from GitHub releases in some environments
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req) as response:
                with open(binary_path, 'wb') as out_file:
                    out_file.write(response.read())
            print("Download complete.")
            
            # Make executable on POSIX systems
            if platform.system().lower() != "windows":
                os.chmod(binary_path, 0o755)
        except Exception as e:
            print(f"Failed to download Tailwind CLI: {e}")
            sys.exit(1)
            
    print(f"Compiling Tailwind CSS...")
    print(f"Input:  {INPUT_CSS}")
    print(f"Output: {OUTPUT_CSS}")
    
    cmd = [binary_path, "-i", INPUT_CSS, "-o", OUTPUT_CSS]
    
    # Add --minify if production, otherwise let it run normally
    if len(sys.argv) > 1 and sys.argv[1] == "--minify":
        cmd.append("--minify")
        
    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print("CSS compilation successful!")
        else:
            print(f"Tailwind compiler exited with code {result.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Tailwind compiler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
