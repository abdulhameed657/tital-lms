import os

def fix_file(filename):
    if not os.path.exists(filename):
        print(f"{filename} does not exist.")
        return
        
    print(f"Checking encoding for {filename}...")
    try:
        # Try reading as UTF-16
        with open(filename, 'rb') as f:
            content_bytes = f.read()
            
        if content_bytes.startswith(b'\xff\xfe') or content_bytes.startswith(b'\xfe\xff'):
            print(f"{filename} is UTF-16 encoded. Re-encoding to UTF-8...")
            content_str = content_bytes.decode('utf-16')
            with open(filename, 'w', encoding='utf-8') as f_out:
                f_out.write(content_str)
            print(f"Successfully re-encoded {filename} to UTF-8.")
        elif content_bytes.startswith(b'\xef\xbb\xbf'):
            print(f"{filename} is UTF-8 with BOM. Cleaning BOM...")
            content_str = content_bytes.decode('utf-8-sig')
            with open(filename, 'w', encoding='utf-8') as f_out:
                f_out.write(content_str)
            print(f"Successfully cleaned BOM from {filename}.")
        else:
            print(f"{filename} is already standard or compatible encoding. Attempting to decode as UTF-8...")
            try:
                content_bytes.decode('utf-8')
                print(f"{filename} decodes correctly as UTF-8.")
            except UnicodeDecodeError:
                print(f"{filename} failed to decode as UTF-8. Trying UTF-16 fallback...")
                content_str = content_bytes.decode('utf-16')
                with open(filename, 'w', encoding='utf-8') as f_out:
                    f_out.write(content_str)
                print(f"Successfully converted {filename} from UTF-16 to UTF-8.")
    except Exception as e:
        print(f"Error handling {filename}: {e}")

if __name__ == "__main__":
    for f in ['.env', '.flaskenv']:
        fix_file(f)
