#!/usr/bin/python

import os
import sys

def main():
    ppa = os.environ.get("PPA", "Undefined")
    if ppa == "Undefined":
        sys.exit("PPA is not defined.")
    else:
        ppa_file = os.path.join('/var/run/linaro-ppa', ppa)
        f = open(ppa_file)
        sources_entry = f.read().strip()
        f.close()

    hwpack = os.environ.get("HWPACK", "Undefined")
    if hwpack == "Undefined":
        sys.exit("Hardware pack is not defined.")
    else:
        hwpack_file = os.path.join('hwpacks', hwpack)
        f = open(hwpack_file, "a")
        f.write(sources_entry)
        f.close()

if __name__ == "__main__":
        main()
