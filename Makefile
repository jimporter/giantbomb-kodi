XBMC_PROFILE?=$(HOME)/.xbmc
ADDON_NAME=plugin.video.giantbomb
ADDON_VERSION=5.0a1
ADDON_INSTALL_DIR=$(XBMC_PROFILE)/addons/$(ADDON_NAME)

.PHONY: uninstall-dev
uninstall-dev:
	rm -rf $(ADDON_INSTALL_DIR)

.PHONY: install-dev
install-dev: uninstall-dev
	cp -R $(ADDON_NAME) $(ADDON_INSTALL_DIR)

.PHONY: package
package:
	zip -r $(ADDON_NAME)-$(ADDON_VERSION).zip $(ADDON_NAME)

.PHONY: test
test:
	PYTHONPATH=$(PWD)/$(ADDON_NAME):$(PYTHONPATH) \
	python -m unittest discover test
