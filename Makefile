XBMC_PROFILE?=$(HOME)/.xbmc
ADDON_NAME=plugin.video.giantbomb
ADDON_INSTALL_DIR=$(XBMC_PROFILE)/addons/$(ADDON_NAME)

.PHONY: uninstall-dev
uninstall-dev:
	rm -rf $(ADDON_INSTALL_DIR)

.PHONY: install-dev
install-dev: uninstall-dev
	cp -R $(ADDON_NAME) $(ADDON_INSTALL_DIR)

.PHONY: package
package:
	zip $(ADDON_NAME).zip $(ADDON_NAME)
