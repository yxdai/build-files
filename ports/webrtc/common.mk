ifndef QCONFIG
QCONFIG=qconfig.mk
endif
include $(QCONFIG)

include $(MKFILES_ROOT)/qmacros.mk

BUILDDIR = $(CURDIR)
SRC_ROOT = $(PROJECT_ROOT)/../../..
PUBLIC_HDR = $(PROJECT_ROOT)/public
PUBLIC_INCVPATH = $(PUBLIC_HDR)
WEBRTC_HDR = $(PUBLIC_HDR)

IS_DEBUG:=$(filter g, $(VARIANT_LIST))
IS_IOPKT:=$(filter iopkt, $(VARIANT_LIST))
IS_IOSOCK:=$(filter iosock, $(VARIANT_LIST))
IS_IOAUDIO:=$(filter ioaudio, $(VARIANT_LIST))
IS_IOSND:=$(filter iosnd, $(VARIANT_LIST))

ifeq ($(CPU),aarch64)
GN_GEN_ARGS += target_cpu="arm64"
else ifeq ($(CPU),x86_64)
GN_GEN_ARGS += target_cpu="x64"
endif
GN_GEN_ARGS += target_os="qnx" treat_warnings_as_errors=false
GN_GEN_ARGS += $(if $(IS_DEBUG),is_debug=true,is_debug=false)

ifeq ($(IS_IOSOCK),iosock)
GN_GEN_ARGS += rtc_qnx_use_io_sock=true
else ifeq ($(IS_IOPKT),iopkt)
GN_GEN_ARGS += rtc_qnx_use_io_sock=false
endif

ifeq ($(IS_IOSND),iosnd)
GN_GEN_ARGS += rtc_qnx_use_io_snd=true
else ifeq ($(IS_IOAUDIO),ioaudio)
GN_GEN_ARGS += rtc_qnx_use_io_snd=false
endif


WEBRTC_INSTALL_DIR=usr/lib

all: $(BUILDDIR)/args.gn
	cd $(SRC_ROOT);autoninja -C $(BUILDDIR)

$(BUILDDIR)/args.gn: $(BUILDDIR)
	cd $(SRC_ROOT);gn gen $(BUILDDIR) --args='$(GN_GEN_ARGS)'

clean:
	$(RM_HOST) -fr $(filter-out Makefile,$(wildcard *))
	$(RM_HOST) -fr $(PUBLIC_HDR)

install: all
	$(CP_HOST) $(BUILDDIR)/obj/libwebrtc.a $(INSTALL_ROOT_AR)/$(WEBRTC_INSTALL_DIR)/libwebrtc.a
	$(CP_HOST) $(BUILDDIR)/obj/third_party/libyuv/libyuv_internal.a $(INSTALL_ROOT_AR)/$(WEBRTC_INSTALL_DIR)/libyuv_internal.a
	$(if $(filter aarch64, $(CPU)), $(CP_HOST) $(BUILDDIR)/obj/third_party/libyuv/libyuv_neon.a $(INSTALL_ROOT_AR)/$(WEBRTC_INSTALL_DIR)/libyuv_neon.a)

uninstall:
	$(RM_HOST) $(INSTALL_ROOT_AR)/$(WEBRTC_INSTALL_DIR)/libwebrtc.a
	$(RM_HOST) $(INSTALL_ROOT_AR)/$(WEBRTC_INSTALL_DIR)/libyuv_internal.a
	$(if $(filter aarch64, $(CPU)), $(RM_HOST) $(INSTALL_ROOT_AR)/$(WEBRTC_INSTALL_DIR)/libyuv_neon.a)

hinstall: $(PUBLIC_HDR)
	$(CP_HOST) -r $(WEBRTC_HDR) $(INSTALL_ROOT_HDR)
