#!/bin/sh

# (C) 2012-2013 Fathi Boudra <fathi.boudra@linaro.org>

# Calls all necessary live-build programs in the correct order to complete
# the bootstrap, chroot, binary, and source stage.

# You need live-build package installed and superuser privileges.

IMAGEPREFIX=linaro-sid-kvm-`date +%Y%m%d`-$(BUILD_NUMBER)
LOGFILE=$(IMAGEPREFIX).build-log.txt
CONFIGFILE=$(IMAGEPREFIX).config.tar.bz2
LISTFILE=$(IMAGEPREFIX).contents
PKGSFILE=$(IMAGEPREFIX).packages
GZFILE=$(IMAGEPREFIX).img.gz
MD5SUMSFILE=$(IMAGEPREFIX).md5sums.txt
SHA1SUMSFILE=$(IMAGEPREFIX).sha1sums.txt

all:
	set -e; sudo lb build 2>&1 | tee $(LOGFILE)
	if [ -f binary.img ]; then \
		tar -jcf $(CONFIGFILE) auto/ config/ configure; \
		sudo mv binary.contents $(LISTFILE); \
		sudo mv binary.packages $(PKGSFILE); \
		sudo mv binary.img $(IMAGEPREFIX).img; \
		gzip -9 --rsyncable $(IMAGEPREFIX).img
		md5sum $(LOGFILE) $(CONFIGFILE) $(LISTFILE) $(PKGSFILE) $(GZFILE) > $(MD5SUMSFILE); \
		sha1sum $(LOGFILE) $(CONFIGFILE) $(LISTFILE) $(PKGSFILE) $(GZFILE) > $(SHA1SUMSFILE); \
	fi

clean:
	sudo lb clean --purge
	rm -f $(IMAGEPREFIX).*
