# Based on n64.mk from libdragon
.DEFAULT_GOAL := all

PROJ_NAME := sodium64
BUILD_DIR := build
SRC_DIRS := src
PROFILE ?= 0
HW_PROFILE ?= 0
COLOR_DIAG ?= 0
NATIVE_DIAG ?= 0
NATIVE_DIAG_TRACE ?= 0
REMOTE ?= 0
SCENE_STATE ?= 0
SCENE_SLOT ?= 0
ifeq ($(SCENE_SLOT),1)
ifneq ($(SCENE_STATE)$(SCENE_RSP_CONTEXT)$(NATIVE_DIAG_TRACE)$(AUDIO_OBSERVER),1111)
$(error SCENE_SLOT requires SCENE_STATE=1 SCENE_RSP_CONTEXT=1 NATIVE_DIAG_TRACE=1 AUDIO_OBSERVER=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_SCENE_SLOT=1 -Os
ifeq ($(BACKDROP_ROWS),1)
$(error SCENE_SLOT currently covers BACKDROP_ROWS=0; Main row cursor/candidate owners require a separate continuation gate)
endif
endif
SCENE_RSP_CONTEXT ?= 0
ifeq ($(SCENE_RSP_CONTEXT),1)
ifneq ($(SCENE_STATE),1)
$(error SCENE_RSP_CONTEXT requires SCENE_STATE=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_SCENE_RSP_CONTEXT=1
endif
DSP_RSP_GAUSS_PROBE ?= 0
ifeq ($(DSP_RSP_GAUSS_PROBE),1)
ifneq ($(SCENE_STATE)$(SCENE_RSP_CONTEXT)$(NATIVE_DIAG_TRACE)$(AUDIO_OBSERVER),1111)
$(error DSP_RSP_GAUSS_PROBE requires SCENE_STATE=1 SCENE_RSP_CONTEXT=1 NATIVE_DIAG_TRACE=1 AUDIO_OBSERVER=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_DSP_RSP_GAUSS_PROBE=1 -Os
endif
DSP_RSP_GAUSS_DMA ?= 0
DSP_RSP_BRR_PROBE ?= 0
DSP_RSP_BRR_RESIDENT ?= 0
ifeq ($(DSP_RSP_BRR_RESIDENT),1)
ifneq ($(DSP_RSP_BRR_PROBE)$(DSP_RSP_GAUSS_DMA),11)
$(error DSP_RSP_BRR_RESIDENT requires DSP_RSP_BRR_PROBE=1 DSP_RSP_GAUSS_DMA=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_DSP_RSP_BRR_RESIDENT=1
endif
ifeq ($(DSP_RSP_BRR_PROBE),1)
ifneq ($(DSP_RSP_GAUSS_PROBE),1)
$(error DSP_RSP_BRR_PROBE requires DSP_RSP_GAUSS_PROBE=1 and its full-context guards)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_DSP_RSP_BRR_PROBE=1
endif
ifeq ($(DSP_RSP_GAUSS_DMA),1)
ifneq ($(DSP_RSP_GAUSS_PROBE),1)
$(error DSP_RSP_GAUSS_DMA requires DSP_RSP_GAUSS_PROBE=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_DSP_RSP_GAUSS_DMA=1
endif
SCENE_RSP_REBIND ?= 0
SCENE_RSP_GPR_ONLY ?= 0
ifeq ($(SCENE_RSP_GPR_ONLY),1)
ifneq ($(SCENE_RSP_REBIND),1)
$(error SCENE_RSP_GPR_ONLY requires SCENE_RSP_REBIND=1)
endif
endif
ifeq ($(SCENE_RSP_REBIND),1)
ifneq ($(SCENE_STATE),1)
$(error SCENE_RSP_REBIND requires SCENE_STATE=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_SCENE_RSP_REBIND=1
endif
ifeq ($(SCENE_STATE),1)
ifneq ($(REMOTE),1)
$(error SCENE_STATE requires REMOTE=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_SCENE_STATE=1
endif
SIGNAL_PROFILE ?= 0
WIDE_MATH ?= 0
ELIGIBILITY_TAGS ?= 0
MASK_SCAN ?= 0
SECTION_OBSERVER ?= 0
AUDIO_OBSERVER ?= 0
DSP_PITCH_CACHE ?= 0
DSP_BRR_ACCURATE ?= 0
DSP_BRR_GROUP ?= 0
ifeq ($(DSP_BRR_GROUP),1)
ifneq ($(DSP_BRR_ACCURATE),1)
$(error DSP_BRR_GROUP requires DSP_BRR_ACCURATE=1)
endif
endif
DSP_KOFF_RELEASE ?= 0
DSP_DRY_MIX ?= 0
DSP_VOICE_BASE ?= 0
DSP_GAIN_PROBE ?= 0
FULL_DSP_PROBE ?= 0
FULL_DSP_SNAPSHOT_CORE ?= 0
ifeq ($(FULL_DSP_SNAPSHOT_CORE),1)
ifneq ($(FULL_DSP_PROBE),1)
$(error FULL_DSP_SNAPSHOT_CORE requires FULL_DSP_PROBE=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_FULL_DSP_SNAPSHOT_CORE=1
N64_CXXFLAGS_PROBE += -DSODIUM64_FULL_DSP_SNAPSHOT_CORE=1
endif
DSP_FULL_GAUSS_BATCH ?= 0
DSP_FULL_BRR_BATCH ?= 0
DSP_FULL_WINDOW ?= 0
ifeq ($(DSP_FULL_WINDOW),1)
ifneq ($(FULL_DSP_PROBE),1)
$(error DSP_FULL_WINDOW requires FULL_DSP_PROBE=1)
endif
ifneq ($(DSP_FULL_GAUSS_BATCH)$(DSP_FULL_BRR_BATCH),00)
$(error DSP_FULL_WINDOW is qualified with DSP_FULL_GAUSS_BATCH=0 DSP_FULL_BRR_BATCH=0)
endif
N64_CXXFLAGS_DSP += -DSODIUM64_DSP_FULL_WINDOW=1
N64_CXXFLAGS_PROBE += -DSODIUM64_DSP_FULL_WINDOW=1
N64_CFLAGS_REMOTE += -DSODIUM64_DSP_FULL_WINDOW=1
endif
ifeq ($(DSP_FULL_BRR_BATCH),1)
ifneq ($(FULL_DSP_PROBE),1)
$(error DSP_FULL_BRR_BATCH requires FULL_DSP_PROBE=1)
endif
ifneq ($(DSP_FULL_GAUSS_BATCH),0)
$(error DSP_FULL_BRR_BATCH is qualified independently; use DSP_FULL_GAUSS_BATCH=0)
endif
N64_CXXFLAGS_DSP += -DSODIUM64_DSP_FULL_BRR_BATCH=1
N64_CXXFLAGS_PROBE += -DSODIUM64_DSP_FULL_BRR_BATCH=1
endif
ifeq ($(DSP_FULL_GAUSS_BATCH),1)
ifneq ($(FULL_DSP_PROBE),1)
$(error DSP_FULL_GAUSS_BATCH requires FULL_DSP_PROBE=1)
endif
N64_CXXFLAGS_DSP += -DSODIUM64_DSP_FULL_GAUSS_BATCH=1
endif
DSP_SIGNAL_ELIDE ?= 0
ifeq ($(DSP_SIGNAL_ELIDE),1)
ifneq ($(FULL_DSP_PROBE),1)
$(error DSP_SIGNAL_ELIDE requires FULL_DSP_PROBE=1)
endif
N64_CXXFLAGS_DSP += -DSODIUM64_DSP_SIGNAL_ELIDE=1
endif
ifeq ($(FULL_DSP_PROBE),1)
ifneq ($(REMOTE)$(AUDIO_OBSERVER),11)
$(error FULL_DSP_PROBE requires REMOTE=1 AUDIO_OBSERVER=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_FULL_DSP_PROBE=1
endif
ifeq ($(DSP_GAIN_PROBE),1)
ifneq ($(REMOTE)$(DSP_DRY_MIX)$(MIX_OBSERVER),111)
$(error DSP_GAIN_PROBE requires REMOTE=1 DSP_DRY_MIX=1 MIX_OBSERVER=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_DSP_GAIN_PROBE=1
endif
ifeq ($(DSP_VOICE_BASE),1)
ifneq ($(DSP_DRY_MIX),1)
$(error DSP_VOICE_BASE requires DSP_DRY_MIX=1)
endif
endif
MIX_OBSERVER ?= 0
BRR_OBSERVER ?= 0
TLUT_SHADER ?= 0
TLUT_FLAT_WINDOW ?= 0
ifeq ($(TLUT_FLAT_WINDOW),1)
ifneq ($(TLUT_SHADER),1)
$(error TLUT_FLAT_WINDOW requires TLUT_SHADER=1)
endif
endif
FULL_ROW_MATH ?= 0
RDP_HALF_MATH ?= 0
FIXED_WINDOW_MATH ?= 0
RDP_FIXED_MATH ?= 0
FETCH_SIGNAL ?= 0
TMEM_ATLAS ?= 0
TMEM_ATLAS_BITS ?= 5
TMEM_COORD_ATLAS ?= 0
DECODE_BANK ?= 0
BG_SPANS ?= 0
ADAPTIVE_SPANS ?= 0
ADAPTIVE_NOSPAN ?= 0
SUB_ALPHA ?= 0
BACKDROP_ROWS ?= 0
ifeq ($(BACKDROP_ROWS),1)
ifneq ($(SUB_ALPHA),1)
$(error BACKDROP_ROWS requires SUB_ALPHA=1)
endif
endif
ifeq ($(SUB_ALPHA),1)
ifneq ($(ADAPTIVE_NOSPAN),1)
$(error SUB_ALPHA requires ADAPTIVE_NOSPAN=1)
endif
endif
ifeq ($(ADAPTIVE_NOSPAN),1)
ifneq ($(ADAPTIVE_SPANS),1)
$(error ADAPTIVE_NOSPAN requires ADAPTIVE_SPANS=1)
endif
endif
ifeq ($(ADAPTIVE_SPANS),1)
ifneq ($(BG_SPANS),1)
$(error ADAPTIVE_SPANS requires BG_SPANS=1)
endif
endif
ifeq ($(DECODE_BANK),1)
ifneq ($(TMEM_ATLAS),1)
$(error DECODE_BANK requires TMEM_ATLAS=1)
endif
endif
ifeq ($(BG_SPANS),1)
ifneq ($(DECODE_BANK)$(TMEM_ATLAS)$(TMEM_COORD_ATLAS)$(TMEM_ATLAS_BITS),1113)
$(error BG_SPANS requires DECODE_BANK=1 and the retained coordinate8 atlas)
endif
endif
ifeq ($(TMEM_COORD_ATLAS),1)
ifeq ($(filter $(TMEM_ATLAS)$(TMEM_ATLAS_BITS),12 13),)
$(error TMEM_COORD_ATLAS requires TMEM_ATLAS=1 TMEM_ATLAS_BITS=2 or 3)
endif
endif
ifeq ($(TMEM_ATLAS),1)
ifeq ($(filter $(TMEM_ATLAS_BITS),0 1 2 3 4 5),)
$(error TMEM_ATLAS_BITS must be between 0 and 5)
endif
endif
ifeq ($(FETCH_SIGNAL),1)
ifneq ($(SIGNAL_PROFILE),1)
$(error FETCH_SIGNAL requires SIGNAL_PROFILE=1)
endif
endif
RDP_MATH_PROBE ?= 0
RDP_FIXED_PROBE_ONLY ?= 0
ifeq ($(RDP_FIXED_PROBE_ONLY),1)
ifneq ($(RDP_MATH_PROBE),1)
$(error RDP_FIXED_PROBE_ONLY requires RDP_MATH_PROBE=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_RDP_FIXED_ONLY_PROBE=1
endif
ifeq ($(FIXED_WINDOW_MATH),1)
ifneq ($(ELIGIBILITY_TAGS),1)
$(error FIXED_WINDOW_MATH requires ELIGIBILITY_TAGS=1)
endif
endif
ifeq ($(RDP_FIXED_MATH),1)
ifneq ($(ELIGIBILITY_TAGS),1)
$(error RDP_FIXED_MATH requires ELIGIBILITY_TAGS=1)
endif
endif
ifeq ($(RDP_HALF_MATH),1)
ifneq ($(ELIGIBILITY_TAGS),1)
$(error RDP_HALF_MATH requires ELIGIBILITY_TAGS=1)
endif
endif
ifeq ($(RDP_MATH_PROBE),1)
ifneq ($(REMOTE),1)
$(error RDP_MATH_PROBE requires REMOTE=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_RDP_MATH_PROBE=1
endif
ifeq ($(SECTION_OBSERVER),1)
ifneq ($(REMOTE),1)
$(error SECTION_OBSERVER requires REMOTE=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_REMOTE_SECTION_OBSERVER=1 -DSODIUM64_NATIVE_DIAG=1 -DSODIUM64_NATIVE_DIAG_TRACE=1
endif
ifeq ($(AUDIO_OBSERVER),1)
ifneq ($(REMOTE),1)
$(error AUDIO_OBSERVER requires REMOTE=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_AUDIO_OBSERVER=1
endif
ifeq ($(MIX_OBSERVER),1)
ifneq ($(AUDIO_OBSERVER)$(DSP_DRY_MIX),11)
$(error MIX_OBSERVER requires AUDIO_OBSERVER=1 DSP_DRY_MIX=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_MIX_OBSERVER=1
endif
ifeq ($(DSP_KOFF_RELEASE),1)
N64_CFLAGS_REMOTE += -DSODIUM64_DSP_KOFF_RELEASE=1
endif
ifeq ($(BRR_OBSERVER),1)
ifneq ($(AUDIO_OBSERVER),1)
$(error BRR_OBSERVER requires AUDIO_OBSERVER=1)
endif
N64_CFLAGS_REMOTE += -DSODIUM64_BRR_OBSERVER=1
endif
ifeq ($(MASK_SCAN),1)
ifneq ($(WIDE_MATH),1)
$(error MASK_SCAN requires WIDE_MATH=1)
endif
endif
ifeq ($(SIGNAL_PROFILE),1)
ifneq ($(NATIVE_DIAG)$(NATIVE_DIAG_TRACE),11)
$(error SIGNAL_PROFILE requires NATIVE_DIAG=1 NATIVE_DIAG_TRACE=1)
endif
endif
ifeq ($(REMOTE),1)
ifneq ($(NATIVE_DIAG)$(NATIVE_DIAG_TRACE),11)
$(error REMOTE requires the isolated A14 NATIVE_DIAG=1 NATIVE_DIAG_TRACE=1 build)
endif
endif
ifeq ($(NATIVE_DIAG_TRACE),1)
ifneq ($(NATIVE_DIAG),1)
$(error NATIVE_DIAG_TRACE requires NATIVE_DIAG=1)
endif
endif
ifeq ($(NATIVE_DIAG),1)
ifneq ($(filter 1,$(PROFILE) $(HW_PROFILE) $(COLOR_DIAG)),)
$(error NATIVE_DIAG uses its own timer and SRAM format; other profilers must be off)
endif
endif
ifeq ($(COLOR_DIAG),1)
HW_PROFILE := 1
endif

# Real-N64 M0 profiling is a specialization of the statistical PROFILE build.
ifeq ($(HW_PROFILE),1)
PROFILE := 1
endif

SFILES := $(foreach dir,$(SRC_DIRS),$(wildcard $(dir)/*.S))
ifneq ($(DSP_RSP_BRR_PROBE),1)
SFILES := $(filter-out src/rsp_dsp_brr.S,$(SFILES))
endif
ifneq ($(DSP_RSP_GAUSS_PROBE),1)
SFILES := $(filter-out src/rsp_dsp_gauss.S,$(SFILES))
endif
ifneq ($(SCENE_RSP_CONTEXT),1)
SFILES := $(filter-out src/rsp_scene_capture.S src/rsp_scene_restore.S,$(SFILES))
endif
ifneq ($(SCENE_RSP_REBIND),1)
SFILES := $(filter-out src/rsp_scene_rebind.S,$(SFILES))
endif
ifneq ($(ADAPTIVE_SPANS),1)
SFILES := $(filter-out src/rsp_decoder_original.S,$(SFILES))
endif
ifneq ($(TMEM_ATLAS),1)
SFILES := $(filter-out src/rsp_object_cache.S,$(SFILES))
endif
ifneq ($(TLUT_SHADER),1)
SFILES := $(filter-out src/rsp_hcomp_tlut.S,$(SFILES))
endif
ifneq ($(RDP_HALF_MATH),1)
SFILES := $(filter-out src/rsp_hcomp_rdp.S,$(SFILES))
endif
ifneq ($(FIXED_WINDOW_MATH),1)
SFILES := $(filter-out src/rsp_hcomp_fixed_window.S,$(SFILES))
endif
ifneq ($(RDP_FIXED_MATH),1)
SFILES := $(filter-out src/rsp_hcomp_rdp_fixed.S,$(SFILES))
endif
ifneq ($(BACKDROP_ROWS),1)
SFILES := $(filter-out src/rsp_hcomp_backdrop.S,$(SFILES))
endif
HFILES := $(foreach dir,$(SRC_DIRS),$(wildcard $(dir)/*.h))
HFILES += $(foreach dir,$(SRC_DIRS),$(wildcard $(dir)/*.inc))
OFILES := $(patsubst %.S,$(BUILD_DIR)/%.o,$(SFILES))
ifeq ($(SCENE_SLOT),1)
OFILES += $(BUILD_DIR)/src/scene_slot.o $(BUILD_DIR)/src/scene_state_format.o
endif
ifeq ($(SCENE_RSP_CONTEXT),1)
OFILES += $(BUILD_DIR)/src/scene_rsp_context.o
endif
ifeq ($(SCENE_RSP_REBIND),1)
OFILES += $(BUILD_DIR)/src/scene_rsp_probe.o
endif
ifeq ($(FULL_DSP_PROBE),1)
OFILES += $(BUILD_DIR)/src/full_dsp_probe.o $(BUILD_DIR)/third_party/snes_spc/SPC_DSP.o
endif
ifeq ($(DSP_FULL_WINDOW),1)
OFILES += $(BUILD_DIR)/src/full_dsp_window.o
OFILES += $(BUILD_DIR)/src/full_dsp_window_memory.o
endif
ifeq ($(NATIVE_DIAG_TRACE),1)
OFILES += $(BUILD_DIR)/src/continuous_save_c.o
endif
ifeq ($(REMOTE),1)
OFILES += $(BUILD_DIR)/src/remote_control_c.o
N64_ASFLAGS_REMOTE = -DSODIUM64_REMOTE=1
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
ifeq ($(DSP_RSP_BRR_RESIDENT),1)
N64_RSPASFLAGS += -DSODIUM64_DSP_RSP_BRR_RESIDENT=1
endif
ifeq ($(SCENE_RSP_GPR_ONLY),1)
N64_RSPASFLAGS += -DSODIUM64_SCENE_RSP_GPR_ONLY=1
endif
N64_ASFLAGS += $(N64_ASFLAGS_REMOTE)
ifeq ($(SCENE_STATE),1)
N64_ASFLAGS += -DSODIUM64_SCENE_STATE=1
endif
ifeq ($(SCENE_SLOT),1)
N64_ASFLAGS += -DSODIUM64_SCENE_SLOT=1
N64_RSPASFLAGS += -DSODIUM64_SCENE_SLOT=1
endif
ifeq ($(FULL_DSP_PROBE),1)
N64_ASFLAGS += -DSODIUM64_FULL_DSP_PROBE=1
N64_RSPASFLAGS += -DSODIUM64_FULL_DSP_PROBE=1
endif
ifeq ($(DSP_FULL_WINDOW),1)
N64_ASFLAGS += -DSODIUM64_DSP_FULL_WINDOW=1
endif
ifeq ($(AUDIO_OBSERVER),1)
N64_ASFLAGS += -DSODIUM64_AUDIO_OBSERVER=1
N64_RSPASFLAGS += -DSODIUM64_AUDIO_OBSERVER=1
endif
ifeq ($(DSP_PITCH_CACHE),1)
N64_ASFLAGS += -DSODIUM64_DSP_PITCH_CACHE=1
endif
ifeq ($(DSP_BRR_ACCURATE),1)
N64_ASFLAGS += -DSODIUM64_DSP_BRR_ACCURATE=1
endif
ifeq ($(DSP_BRR_GROUP),1)
N64_ASFLAGS += -DSODIUM64_DSP_BRR_GROUP=1
endif
ifeq ($(DSP_KOFF_RELEASE),1)
N64_ASFLAGS += -DSODIUM64_DSP_KOFF_RELEASE=1
endif
ifeq ($(DSP_DRY_MIX),1)
N64_ASFLAGS += -DSODIUM64_DSP_DRY_MIX=1
endif
ifeq ($(DSP_VOICE_BASE),1)
N64_ASFLAGS += -DSODIUM64_DSP_VOICE_BASE=1
endif
ifeq ($(DSP_GAIN_PROBE),1)
N64_ASFLAGS += -DSODIUM64_DSP_GAIN_PROBE=1
endif
ifeq ($(MIX_OBSERVER),1)
N64_ASFLAGS += -DSODIUM64_MIX_OBSERVER=1
N64_RSPASFLAGS += -DSODIUM64_MIX_OBSERVER=1
endif
ifeq ($(BRR_OBSERVER),1)
N64_ASFLAGS += -DSODIUM64_BRR_OBSERVER=1
N64_RSPASFLAGS += -DSODIUM64_BRR_OBSERVER=1
endif
ifeq ($(TMEM_ATLAS),1)
N64_ASFLAGS += -DSODIUM64_TMEM_ATLAS=1
N64_RSPASFLAGS += -DSODIUM64_TMEM_ATLAS=1
N64_RSPASFLAGS += -DSODIUM64_TMEM_ATLAS_BITS=$(TMEM_ATLAS_BITS)
endif
ifeq ($(TMEM_COORD_ATLAS),1)
N64_RSPASFLAGS += -DSODIUM64_TMEM_COORD_ATLAS=1
endif
ifeq ($(DECODE_BANK),1)
N64_RSPASFLAGS += -DSODIUM64_DECODE_BANK=1
endif
ifeq ($(BG_SPANS),1)
N64_RSPASFLAGS += -DSODIUM64_BG_SPANS=1
endif
ifeq ($(ADAPTIVE_SPANS),1)
N64_ASFLAGS += -DSODIUM64_ADAPTIVE_SPANS=1
N64_RSPASFLAGS += -DSODIUM64_ADAPTIVE_SPANS=1
endif
ifeq ($(ADAPTIVE_NOSPAN),1)
N64_ASFLAGS += -DSODIUM64_ADAPTIVE_NOSPAN=1
N64_RSPASFLAGS += -DSODIUM64_ADAPTIVE_NOSPAN=1
endif
ifeq ($(SUB_ALPHA),1)
N64_RSPASFLAGS += -DSODIUM64_SUB_ALPHA=1
endif
ifeq ($(BACKDROP_ROWS),1)
N64_ASFLAGS += -DSODIUM64_BACKDROP_ROWS=1
N64_RSPASFLAGS += -DSODIUM64_BACKDROP_ROWS=1
N64_CFLAGS_REMOTE += -DSODIUM64_BACKDROP_ROWS=1
endif
ifeq ($(FETCH_SIGNAL),1)
N64_RSPASFLAGS += -DSODIUM64_RDP_FETCH_SIGNAL=1
endif
ifeq ($(WIDE_MATH),1)
N64_RSPASFLAGS += -DSODIUM64_HCOMP_WIDE_MATH=1
endif
ifeq ($(ELIGIBILITY_TAGS),1)
N64_RSPASFLAGS += -DSODIUM64_ELIGIBILITY_TAGS=1
endif
ifeq ($(MASK_SCAN),1)
N64_RSPASFLAGS += -DSODIUM64_HCOMP_MASK_SCAN=1
endif
ifeq ($(TLUT_SHADER),1)
N64_ASFLAGS += -DSODIUM64_HCOMP_TLUT_SHADER=1
N64_RSPASFLAGS += -DSODIUM64_HCOMP_TLUT_SHADER=1
endif
ifeq ($(TLUT_FLAT_WINDOW),1)
N64_RSPASFLAGS += -DSODIUM64_HCOMP_TLUT_FLAT_WINDOW=1
endif
ifeq ($(FULL_ROW_MATH),1)
N64_RSPASFLAGS += -DSODIUM64_HCOMP_FULL_ROW_MATH=1
endif
ifeq ($(RDP_HALF_MATH),1)
N64_ASFLAGS += -DSODIUM64_HCOMP_RDP_HALF_MATH=1
N64_RSPASFLAGS += -DSODIUM64_HCOMP_RDP_HALF_MATH=1
endif
ifeq ($(FIXED_WINDOW_MATH),1)
N64_ASFLAGS += -DSODIUM64_HCOMP_FIXED_WINDOW_MATH=1
N64_RSPASFLAGS += -DSODIUM64_HCOMP_FIXED_WINDOW_MATH=1
endif
ifeq ($(RDP_FIXED_MATH),1)
N64_ASFLAGS += -DSODIUM64_HCOMP_RDP_FIXED_MATH=1
N64_RSPASFLAGS += -DSODIUM64_HCOMP_RDP_FIXED_MATH=1
endif
N64_LDFLAGS = -L$(N64_LIBDIR) -Tn64.ld --gc-sections
N64_TOOLFLAGS = --title $(N64_ROM_TITLE)
N64_ED64ROMCONFIGFLAGS = --savetype $(N64_ROM_SAVETYPE) --regionfree

ifeq ($(NATIVE_DIAG),1)
N64_ASFLAGS += -DSODIUM64_NATIVE_DIAG=1
ifeq ($(NATIVE_DIAG_TRACE),1)
N64_ASFLAGS += -DSODIUM64_NATIVE_DIAG_TRACE=1
N64_RSPASFLAGS += -DSODIUM64_NATIVE_DIAG_TRACE=1
ifeq ($(SIGNAL_PROFILE),1)
N64_ASFLAGS += -DSODIUM64_SIGNAL_PROFILE=1
N64_RSPASFLAGS += -DSODIUM64_SIGNAL_PROFILE=1
endif
ifeq ($(SCENE_SLOT),1)
N64_LDFLAGS += -Tsrc/scene_slot_memory.ld
else ifeq ($(FULL_DSP_PROBE),1)
N64_LDFLAGS += -Tsrc/full_dsp_probe_memory.ld
else ifneq ($(filter 1,$(AUDIO_OBSERVER) $(BRR_OBSERVER) $(MIX_OBSERVER)),)
N64_LDFLAGS += -Tsrc/brr_observer_memory.ld
else
N64_LDFLAGS += -Tsrc/diagnostic_memory.ld
endif
endif
endif

ifeq ($(PROFILE),1)
N64_ASFLAGS += -DSODIUM64_PROFILE=1
N64_RSPASFLAGS += -DSODIUM64_PROFILE=1
endif
ifeq ($(HW_PROFILE),1)
N64_ASFLAGS += -DSODIUM64_HW_PROFILE=1
ifeq ($(COLOR_DIAG),1)
N64_ASFLAGS += -DSODIUM64_COLOR_DIAG=1
endif
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
		RSPLINK=rsp.ld; \
		case "$$FILENAME" in rsp_decoder_original) RSPLINK=src/rsp_decoder_original.ld;; rsp_object_cache|rsp_hcomp|rsp_hcomp_math|rsp_hcomp_fast|rsp_hcomp_setup|rsp_hcomp_tlut|rsp_hcomp_rdp|rsp_hcomp_fixed_window|rsp_hcomp_rdp_fixed|rsp_hcomp_backdrop|rsp_mode7_window) RSPLINK=src/rsp_hcomp.ld;; esac; \
		echo "    [RSP] $<"; \
		$(N64_CC) $(RSPASFLAGS) -L$(N64_LIBDIR) -nostartfiles -Wl,-T$$RSPLINK -Wl,--gc-sections  -Wl,-Map=$(BUILD_DIR)/$(notdir $(basename $@)).map -o $@ $<; \
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

# Only the trace recorder links this SD sink. Sodium uses sp as a queue index;
# its assembly bridge supplies a private O64 stack and preserves guest GPR64.
$(BUILD_DIR)/src/continuous_save_c.o: src/continuous_save.c tools/sc64-diagnostic-save/continuous_save_abi.h
	@mkdir -p $(dir $@)
	$(N64_CC) -c -O2 -std=c11 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -ffreestanding -fno-builtin -fno-stack-protector -Wall -Wextra -Werror -o $@ $<

$(BUILD_DIR)/src/remote_control_c.o: src/remote_control.c src/remote_control.h src/defines.h src/scene_rsp_probe.h src/scene_rsp_context.h tools/sc64-diagnostic-save/recorder_runtime_abi.h
	@mkdir -p $(dir $@)
	$(N64_CC) -c -O2 -std=c11 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -ffreestanding -fno-builtin -fno-stack-protector -Wall -Wextra -Werror $(N64_CFLAGS_REMOTE) -o $@ $<

$(BUILD_DIR)/src/full_dsp_probe.o: src/full_dsp_probe.cpp src/full_dsp_probe.h $(wildcard third_party/snes_spc/*.h)
	@mkdir -p $(dir $@)
	$(N64_CXX) -c -O2 -std=c++98 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -fno-builtin -fno-stack-protector -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections -DNDEBUG -DBLARGG_BIG_ENDIAN=1 -Wall -Wextra -Werror $(N64_CXXFLAGS_PROBE) -o $@ $<

$(BUILD_DIR)/src/full_dsp_window.o: src/full_dsp_window.cpp src/full_dsp_window.h $(wildcard third_party/snes_spc/*.h)
	@mkdir -p $(dir $@)
	$(N64_CXX) -c -O2 -std=c++98 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -fno-builtin -fno-stack-protector -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections -DNDEBUG -DBLARGG_BIG_ENDIAN=1 -Wall -Wextra -Werror $(N64_CXXFLAGS_PROBE) -o $@ $<

$(BUILD_DIR)/src/full_dsp_window_memory.o: src/full_dsp_window_memory.cpp src/full_dsp_window_memory.h src/full_dsp_window.h $(wildcard third_party/snes_spc/*.h)
	@mkdir -p $(dir $@)
	$(N64_CXX) -c -O2 -std=c++98 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -fno-builtin -fno-stack-protector -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections -DNDEBUG -DBLARGG_BIG_ENDIAN=1 -Wall -Wextra -Werror $(N64_CXXFLAGS_PROBE) -o $@ $<

$(BUILD_DIR)/src/scene_rsp_probe.o: src/scene_rsp_probe.c src/scene_rsp_probe.h
	@mkdir -p $(dir $@)
	$(N64_CC) -c -O2 -std=c11 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -ffreestanding -fno-builtin -fno-stack-protector -Wall -Wextra -Werror -o $@ $<

$(BUILD_DIR)/src/scene_rsp_context.o: src/scene_rsp_context.c src/scene_rsp_context.h src/scene_rsp_probe.h
	@mkdir -p $(dir $@)
	$(N64_CC) -c -O2 -std=c11 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -ffreestanding -fno-builtin -fno-stack-protector -Wall -Wextra -Werror $(N64_CFLAGS_REMOTE) -o $@ $<

$(BUILD_DIR)/src/scene_slot.o $(BUILD_DIR)/src/scene_state_format.o: $(BUILD_DIR)/%.o: %.c src/scene_slot.h src/scene_state_format.h
	@mkdir -p $(dir $@)
	$(N64_CC) -c -Os -std=c11 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -ffreestanding -fno-builtin -fno-stack-protector -Wall -Wextra -Werror -o $@ $<

$(BUILD_DIR)/third_party/snes_spc/SPC_DSP.o: third_party/snes_spc/SPC_DSP.cpp $(wildcard third_party/snes_spc/*.h)
	@mkdir -p $(dir $@)
	$(N64_CXX) -c -O2 -std=c++98 -march=vr4300 -mtune=vr4300 -mabi=o64 -mno-abicalls -fno-pic -G0 -fno-builtin -fno-stack-protector -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections -DNDEBUG -DBLARGG_BIG_ENDIAN=1 -Wno-implicit-fallthrough $(N64_CXXFLAGS_DSP) -o $@ $<

%.elf: $(N64_LIBDIR)/n64.ld
	@mkdir -p $(dir $@)
	@echo "    [LD] $@"
	$(CXX) -o $@ $(filter-out $(N64_LIBDIR)/n64.ld,$^) -lc $(patsubst %,-Wl$(COMMA)%,$(LDFLAGS)) -Wl,-Map=$(BUILD_DIR)/$(notdir $(basename $@)).map
	$(N64_SIZE) -G $@

.SILENT:

all: $(PROJ_NAME).z64

$(BUILD_DIR)/$(PROJ_NAME).elf: $(OFILES)

$(OFILES): $(HFILES)

$(BUILD_DIR)/src/rsp_hcomp.o $(BUILD_DIR)/src/rsp_hcomp_math.o $(BUILD_DIR)/src/rsp_hcomp_fast.o $(BUILD_DIR)/src/rsp_hcomp_setup.o $(BUILD_DIR)/src/rsp_mode7_window.o: src/rsp_hcomp.ld
$(BUILD_DIR)/src/rsp_hcomp_tlut.o: src/rsp_hcomp.ld
$(BUILD_DIR)/src/rsp_hcomp_rdp.o: src/rsp_hcomp.ld
$(BUILD_DIR)/src/rsp_hcomp_fixed_window.o: src/rsp_hcomp.ld
$(BUILD_DIR)/src/rsp_hcomp_rdp_fixed.o: src/rsp_hcomp.ld
$(BUILD_DIR)/src/rsp_hcomp_backdrop.o: src/rsp_hcomp.ld
$(BUILD_DIR)/src/rsp_object_cache.o: src/rsp_hcomp.ld

clean:
	rm -rf $(BUILD_DIR) $(PROJ_NAME).z64

.PHONY: all clean


