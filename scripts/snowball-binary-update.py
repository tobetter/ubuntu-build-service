#!/usr/bin/env python

import os
import sys
import subprocess
import hashlib

def main():
    wget_cmd = os.environ.get("WGET_CMD")
    if wget_cmd == None:
        f = open('/var/run/linaro-binaries/snowball-binary-update')
        wget_cmd = f.read().strip()
        f.close()

    timestamp = os.environ.get('TIMESTAMP', 'Undefined')
    if timestamp == 'Undefined':
        sys.exit('Timestamp is not defined.')

    igloo_url = 'http://www.igloocommunity.org/download/android/ics/binaries/%s' % timestamp
    md5sum_url = '%s/MD5SUM' % igloo_url
    vendor_url = '%s/vendor.tar.bz2' % igloo_url

    subprocess.call("%s %s %s" % (wget_cmd, md5sum_url, vendor_url), shell=True)

    f = open('MD5SUM')
    (md5, file) = f.read().strip().split(" ", 1)
    f.close()

    vendor_md5 = hashlib.md5(open('vendor.tar.bz2').read()).hexdigest()

    if md5 == vendor_md5:
        print 'vendor.tar.bz2: OK'
    else:
        print 'vendor.tar.bz2: FAILED'
        sys.exit('checksum did NOT match.')

if __name__ == "__main__":
        main()
