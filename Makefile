# Based on n64.mk from libdragon
.DEFAULT_GOAL := all

PROJ_NAME := sodium64
BUILD_DIR := build
SRC_DIRS := src
PROFILE ?= 0
HW_PROFILE ?= 0
HW_PROFILE_WARMUP ?= 2
REMOTE ?= 0
DSP_LIVE_GUEST ?= 0
DSP_LIVE_PREFIX ?= 0
DSP_LIVE_CORE ?= 0
DSP_LIVE_INPUT_QUEUE ?= 0
DSP_RSP_SWAP ?= 0
DSP_RSP_YIELD ?= 0
DSP_RSP_YIELD_SWAP ?= 0
DSP_RSP_YIELD_TASK ?= 0
DSP_RSP_RESIDENT_TEST ?= 0
ifeq ($(DSP_RSP_RESIDENT_TEST),1)
ifneq ($(DSP_RSP_YIELD)$(DSP_RSP_YIELD_SWAP)$(DSP_RSP_YIELD_TASK),100)
$(error The resident state proof is separate from the full bank exchange)
endif
N64_REMOTE_CFLAGS += -DSODIUM64_DSP_RSP_RESIDENT_TEST=1
endif
ifeq ($(DSP_RSP_YIELD_TASK),1)
ifneq ($(DSP_RSP_YIELD)$(DSP_RSP_YIELD_SWAP),11)
$(error The private RSP marker requires a section handoff with both banks)
endif
N64_REMOTE_CFLAGS += -DSODIUM64_DSP_RSP_YIELD_TASK=1
endif
ifeq ($(DSP_RSP_YIELD),1)
ifneq ($(DSP_RSP_SWAP),1)
$(error The section handoff uses the existing private memory exchange)
endif
endif
DSP_PCM_PERIOD ?= 1
ifneq ($(filter $(DSP_PCM_PERIOD),1 8),$(DSP_PCM_PERIOD))
$(error Unsupported private PCM period)
endif
ifeq ($(DSP_RSP_SWAP),1)
ifneq ($(DSP_LIVE_CORE),1)
$(error The bank exchange proof requires the complete live DSP workload)
endif
endif
ifeq ($(DSP_LIVE_CORE),1)
ifneq ($(REMOTE)$(DSP_LIVE_GUEST)$(DSP_LIVE_PREFIX),111)
$(error The complete live proof requires the private guest and fixed prefix)
endif
endif
ifeq ($(REMOTE),1)
ifneq ($(PROFILE)$(HW_PROFILE),00)
$(error REMOTE is a separate retired-frame bench, not a PROFILE/HW_PROFILE build)
endif
ifeq ($(origin PROJ_NAME),file)
PROJ_NAME := sodium64-usb-bench
endif
ifeq ($(origin BUILD_DIR),file)
BUILD_DIR := build_usb_bench
endif
endif

# Real-N64 M0 profiling is a specialization of the statistical PROFILE build.
ifeq ($(HW_PROFILE),1)
PROFILE := 1
endif

SFILES := $(foreach dir,$(SRC_DIRS),$(wildcard $(dir)/*.S))
HFILES := $(foreach dir,$(SRC_DIRS),$(wildcard $(dir)/*.h))
OFILES := $(patsubst %.S,$(BUILD_DIR)/%.o,$(SFILES))
ifeq ($(REMOTE),1)
OFILES += $(BUILD_DIR)/src/remote_control_c.o
ifeq ($(DSP_LIVE_CORE),1)
OFILES += $(BUILD_DIR)/src/live_dsp.o $(BUILD_DIR)/src/full_dsp_window.o $(BUILD_DIR)/third_party/snes_spc/SPC_DSP.o
ifeq ($(DSP_RSP_SWAP),1)
OFILES += $(BUILD_DIR)/src/live_rsp_swap.o
N64_REMOTE_CFLAGS += -DSODIUM64_DSP_RSP_SWAP=1
N64_DSP_PROBE_CFLAGS += -DSODIUM64_DSP_RSP_SWAP=1
ifeq ($(DSP_RSP_YIELD),1)
N64_REMOTE_CFLAGS += -DSODIUM64_DSP_RSP_YIELD=1
N64_DSP_PROBE_CFLAGS += -DSODIUM64_DSP_RSP_YIELD=1
ifeq ($(DSP_RSP_YIELD_SWAP),1)
N64_REMOTE_CFLAGS += -DSODIUM64_DSP_RSP_YIELD_SWAP=1
endif
endif
endif
endif
endif

N64_ROM_TITLE = "$(PROJ_NAME)"
N64_ROM_SAVETYPE = sram256k

# Override this to use a toolchain installed separately from libdragon
N64_GCCPREFIX ?= $(N64_INST)
N64_ROOTDIR = $(N64_INST)
N64_BINDIR = $(N64_ROOTDIR)/bin
N64_INCLUDEDIR = $(N64_ROOTDIR)/mips64-elf/include
N64_LIBDIR = $(N64_ROOTDIR)/mips64-elf/lib
N64_GCCPREFIX_TRIPLET = $(N64_GCCPREFIX)/bin/mips64-elf-

COMMA := ,

N64_CC = $(N64_GCCPREFIX_TRIPLET)gcc
N64_CXX = $(N64_GCCPREFIX_TRIPLET)g++
N64_AS = $(N64_GCCPREFIX_TRIPLET)as
N64_AR = $(N64_GCCPREFIX_TRIPLET)ar
N64_LD = $(N64_GCCPREFIX_TRIPLET)ld
N64_OBJCOPY = $(N64_GCCPREFIX_TRIPLET)objcopy
N64_OBJDUMP = $(N64_GCCPREFIX_TRIPLET)objdump
N64_SIZE = $(N64_GCCPREFIX_TRIPLET)size
N64_NM = $(N64_GCCPREFIX_TRIPLET)nm
N64_STRIP = $(N64_GCCPREFIX_TRIPLET)strip

N64_CHKSUM = $(N64_BINDIR)/chksum64
N64_ED64ROMCONFIG = $(N64_BINDIR)/ed64romconfig
N64_MKDFS = $(N64_BINDIR)/mkdfs
N64_TOOL = $(N64_BINDIR)/n64tool
N64_SYM = $(N64_BINDIR)/n64sym
N64_ELFCOMPRESS = $(N64_BINDIR)/n64elfcompress
N64_AUDIOCONV = $(N64_BINDIR)/audioconv64
N64_MKSPRITE = $(N64_BINDIR)/mksprite

N64_ASFLAGS = -mtune=vr4300 -march=vr4300 -Wa,--fatal-warnings
N64_RSPASFLAGS = -march=mips1 -mabi=32 -Wa,--fatal-warnings
ifeq ($(DSP_RSP_YIELD),1)
N64_ASFLAGS += -DSODIUM64_DSP_RSP_YIELD=1
N64_RSPASFLAGS += -DSODIUM64_DSP_RSP_YIELD=1
endif
N64_LDFLAGS = -L$(N64_LIBDIR) -Tn64.ld --gc-sections
ifeq ($(REMOTE),1)
N64_ASFLAGS += -DSODIUM64_REMOTE=1
ifeq ($(DSP_LIVE_GUEST),1)
N64_ASFLAGS += -DSODIUM64_DSP_LIVE_GUEST=1
N64_REMOTE_CFLAGS += -DSODIUM64_DSP_LIVE_GUEST=1
ifeq ($(DSP_LIVE_PREFIX),1)
N64_ASFLAGS += -DSODIUM64_DSP_LIVE_PREFIX=1
ifeq ($(DSP_LIVE_CORE),1)
N64_ASFLAGS += -DSODIUM64_DSP_LIVE_CORE=1 -DSODIUM64_DSP_PCM_PERIOD=$(DSP_PCM_PERIOD)
N64_DSP_PROBE_CFLAGS += -DSODIUM64_DSP_PCM_PERIOD=$(DSP_PCM_PERIOD)
N64_REMOTE_CFLAGS += -DSODIUM64_DSP_LIVE_CORE=1
ifeq ($(DSP_LIVE_INPUT_QUEUE),1)
N64_ASFLAGS += -DSODIUM64_DSP_LIVE_INPUT_QUEUE=1
N64_DSP_PROBE_CFLAGS += -DSODIUM64_DSP_LIVE_INPUT_QUEUE=1
N64_REMOTE_CFLAGS += -DSODIUM64_DSP_LIVE_INPUT_QUEUE=1
endif
endif
endif
endif
N64_LDFLAGS += -Tsrc/usb_bench_memory.ld
endif
N64_TOOLFLAGS = --title $(N64_ROM_TITLE)
N64_ED64ROMCONFIGFLAGS = --savetype $(N64_ROM_SAVETYPE) --regionfree

ifeq ($(PROFILE),1)
N64_ASFLAGS += -DSODIUM64_PROFILE=1
N64_LDFLAGS += -Tsrc/profile_memory.ld
endif
ifeq ($(HW_PROFILE),1)
N64_ASFLAGS += -DSODIUM64_HW_PROFILE=1 -DHW_PROFILE_WARMUP_SECONDS=$(HW_PROFILE_WARMUP)
endif

COMMA := ,

# Change the dependency chain of .z64 ROMs to use the N64 toolchain
%.z64: CC=$(N64_CC)
%.z64: CXX=$(N64_CXX)
%.z64: AS=$(N64_AS)
%.z64: LD=$(N64_LD)
%.z64: ASFLAGS+=$(N64_ASFLAGS)
%.z64: RSPASFLAGS+=$(N64_RSPASFLAGS)
%.z64: LDFLAGS+=$(N64_LDFLAGS)
%.z64: $(BUILD_DIR)/%.elf
	@echo "    [Z64] $@"
	$(N64_SYM) $< $<.sym
	cp $< $<.stripped
	$(N64_STRIP) -s $<.stripped
	$(N64_ELFCOMPRESS) -o $(dir $<) -c 1 $<.stripped
	@rm -f $@
	DFS_FILE="$(filter %.dfs, $^)"; \
	if [ -z "$$DFS_FILE" ]; then \
		$(N64_TOOL) $(N64_TOOLFLAGS) --toc --output $@ --align 256 $<.stripped --align 8 $<.sym; \
	else \
		$(N64_TOOL) $(N64_TOOLFLAGS) --toc --output $@ --align 256 $<.stripped --align 8 $<.sym --align 16 "$$DFS_FILE"; \
	fi
	if [ ! -z "$(strip $(N64_ED64ROMCONFIGFLAGS))" ]; then \
		$(N64_ED64ROMCONFIG) $(N64_ED64ROMCONFIGFLAGS) $@; \
	fi

# Assembly rule. We use .S for both RSP and MIPS assembly code, and we differentiate
# using the prefix of the filename: if it starts with "rsp", it is RSP ucode, otherwise
# it's a standard MIPS assembly file.
$(BUILD_DIR)/%.o: %.S
	@mkdir -p $(dir $@)
	set -e; \
	FILENAME="$(notdir $(basename $@))"; \
	if case "$$FILENAME" in "rsp"*) true;; *) false;; esac; then \
		SYMPREFIX="$(subst .,_,$(subst /,_,$(basename $@)))"; \
		TEXTSECTION="$(basename $@).text"; \
		DATASECTION="$(basename $@).data"; \
		BINARY="$(basename $@).elf"; \
		echo "    [RSP] $<"; \
		$(N64_CC) $(RSPASFLAGS) -L$(N64_LIBDIR) -nostartfiles -Wl,-Trsp.ld -Wl,--gc-sections  -Wl,-Map=$(BUILD_DIR)/$(notdir $(basename $@)).map -o $@ $<; \
		mv "$@" $$BINARY; \
		$(N64_OBJCOPY) -O binary -j .text $$BINARY $$TEXTSECTION.bin; \
		$(N64_OBJCOPY) -O binary -j .data $$BINARY $$DATASECTION.bin; \
		$(N64_OBJCOPY) -I binary -O elf32-bigmips -B mips4300 \
				--redefine-sym _binary_$${SYMPREFIX}_text_bin_start=$${FILENAME}_text_start \
				--redefine-sym _binary_$${SYMPREFIX}_text_bin_end=$${FILENAME}_text_end \
				--redefine-sym _binary_$${SYMPREFIX}_text_bin_size=$${FILENAME}_text_size \
				--set-section-alignment .data=8 \
				--rename-section .text=.data $$TEXTSECTION.bin $$TEXTSECTION.o; \
		$(N64_OBJCOPY) -I binary -O elf32-bigmips -B mips4300 \
				--redefine-sym _binary_$${SYMPREFIX}_data_bin_start=$${FILENAME}_data_start \
				--redefine-sym _binary_$${SYMPREFIX}_data_bin_end=$${FILENAME}_data_end \
				--redefine-sym _binary_$${SYMPREFIX}_data_bin_size=$${FILENAME}_data_size \
				--set-section-alignment .data=8 \
				--rename-section .text=.data $$DATASECTION.bin $$DATASECTION.o; \
		$(N64_SIZE) -G $$BINARY; \
		$(N64_LD) -relocatable $$TEXTSECTION.o $$DATASECTION.o -o $@; \
		rm $$TEXTSECTION.bin $$DATASECTION.bin $$TEXTSECTION.o $$DATASECTION.o; \
	else \
		echo "    [AS] $<"; \
		$(CC) -c $(ASFLAGS) -o $@ $<; \
	fi

$(BUILD_DIR)/src/remote_control_c.o: src/remote_control.c src/remote_control.h Makefile
	@mkdir -p $(dir $@)
	$(N64_CC) -c -Os -std=c11 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -ffreestanding -fno-builtin -fno-stack-protector -Wall -Wextra -Werror $(N64_REMOTE_CFLAGS) -o $@ $<

$(BUILD_DIR)/src/live_rsp_swap.o: src/live_rsp_swap.c src/live_rsp_swap.h Makefile
	@mkdir -p $(dir $@)
	$(N64_CC) -c -O2 -std=c11 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -ffreestanding -fno-builtin -fno-stack-protector -Wall -Wextra -Werror $(N64_REMOTE_CFLAGS) -o $@ $<

$(BUILD_DIR)/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(N64_CXX) -c -O2 -std=c++98 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -fno-stack-protector -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections -DNDEBUG -DBLARGG_BIG_ENDIAN=1 -DSODIUM64_DSP_FULL_WINDOW=1 -DSODIUM64_DSP_LIVE_CORE=1 -Wno-implicit-fallthrough $(N64_DSP_PROBE_CFLAGS) -o $@ $<

%.elf: $(N64_LIBDIR)/n64.ld
	@mkdir -p $(dir $@)
	@echo "    [LD] $@"
	$(CXX) -o $@ $(filter-out $(N64_LIBDIR)/n64.ld,$^) -lc $(patsubst %,-Wl$(COMMA)%,$(LDFLAGS)) -Wl,-Map=$(BUILD_DIR)/$(notdir $(basename $@)).map
	$(N64_SIZE) -G $@

.SILENT:

all: $(PROJ_NAME).z64

$(BUILD_DIR)/$(PROJ_NAME).elf: $(OFILES)

$(OFILES): $(HFILES)

clean:
	rm -rf $(BUILD_DIR) $(PROJ_NAME).z64

.PHONY: all clean
