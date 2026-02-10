import os
import sys

BASE_INPUT = os.path.dirname(os.path.abspath(__file__))
if BASE_INPUT not in sys.path:
    sys.path.insert(0, BASE_INPUT)

from METHODLIBRARY.function_library_intake.scan_local_files import scan_local_files

DEFAULT_DIRECTORY = "/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/EURKAI/RESOURCES/FUNCTIONS"

def main():
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = DEFAULT_DIRECTORY
    root_paths = [directory]
    print("Scanning functions in:", directory)
    result = scan_local_files(root_paths)
    print("scan_local_files result:")
    print(result)

if __name__ == "__main__":
    main()
