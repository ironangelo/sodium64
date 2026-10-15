# Pinned linker/tool invocation; compile the referenced libdragon first.
include Makefile
S64_LIBDRAGON_DIR ?= $(CURDIR)/libdragon
S64_TOOLS_DIR ?= $(S64_LIBDRAGON_DIR)/tools
S64_TOOLS_SUFFIX ?=
N64_CFLAGS += -I $(CURDIR)/pinned_include
N64_LDFLAGS = -g $(S64_LIBDRAGON_DIR)/libdragon.a -lm $(S64_LIBDRAGON_DIR)/libdragonsys.a -T$(S64_LIBDRAGON_DIR)/n64.ld --gc-sections --wrap __do_global_ctors
N64_SYM = $(S64_TOOLS_DIR)/n64sym/n64sym$(S64_TOOLS_SUFFIX)
N64_MKDFS = $(S64_TOOLS_DIR)/mkdfs/mkdfs$(S64_TOOLS_SUFFIX)
N64_TOOLFILES = $(S64_LIBDRAGON_DIR)/libdragon.version
