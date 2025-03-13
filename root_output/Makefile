# OS and Architecture detection
OS   := $(shell uname)
ARCH := $(shell uname -m)

# FLUKA-VERSION detection
FLUKA_VERSION := $(shell basename $(shell fluka-config --path) | sed 's/^fluka//')
$(info FLUKA_VERSION = $(FLUKA_VERSION))

# File suffixes
ObjSuf  = o
SrcSuf  = cpp

# Check if the system is macOS, the version is not 14.7, and FLUKA version is 4-4.1
ifeq ($(OS),Darwin)
	ifeq ($(FLUKA_VERSION),4-4.1)
export MACOSX_DEPLOYMENT_TARGET = 15.0
	endif
endif

# ROOT configuration
ROOTCFLAGS := $(shell root-config --cflags)
ROOTLIBS   := $(shell root-config --libs)
ROOTGLIBS  := $(shell root-config --glibs)

# FLUKA configuration
FLUKA 			:= $(shell fluka-config --path)
FLUKA_COMPILER 	:= $(shell fluka-config --compiler)
FLUKA_LIB_PATH 	:= $(shell fluka-config --libpath)
FLUKA_LIBS 		:= $(shell fluka-config --lib)
FLUKA_DPMLIB 	:= $(shell fluka-config --dpmlib)
FLUKA_RQMDLIB 	:= $(shell fluka-config --rqmdlib)

# OS-specific linker flags
SYS_LDFLAGS := -lz
ifeq ($(OS),Darwin)
	ifeq ($(ARCH),arm64)
		SYS_LDFLAGS += -ld_classic -lc++
	endif
endif

# Compiler and linker settings
CXX      = g++
CXXFLAGS = -O -Wall -fPIC
LDFLAGS  = -O $(SYS_LDFLAGS)
SOFLAGS  = -shared

# Add ROOT flags to compiler
CXXFLAGS += $(ROOTCFLAGS)

# Libraries
LIBS = -L.
LIBS += $(ROOTLIBS) $(SYSLIBS)
LIBS += $(FLUKA_LIBS)

# FLUKA optional libraries
FLUKA_OPT_INTOBJS := $(shell fluka-config --intobjs)

# Linker libraries
GLIBS = $(ROOTGLIBS) $(SYSLIBS)

# Objects
OBJS = 
# Uncomment to add source file:
# OBJS += usrini.o usrout.o mgdraw.o
# OBJS += source_newgen.o

# Output directory and binary name
NAME ?= rootfluka
OUTPUT_DIR = RootFlukaExecutables
FULL_OUTPUT_PATH = $(shell pwd)/$(OUTPUT_DIR)

# FLUKA library linking option
OPT_FLUKA_LIBS ?= 1
ifeq ($(OPT_FLUKA_LIBS), 1)
	LIBS += $(FLUKA_LIB_PATH) $(FLUKA_OPT_INTOBJS) $(FLUKA_RQMDLIB) $(FLUKA_DPMLIB)
else
	LIBS += $(FLUKA_LIB_PATH)
endif

# Colors
COLOR_PURPLE = \033[0;35m
COLOR_RED    = \033[0;31m
COLOR_CYAN   = \033[0;36m
COLOR_RESET  = \033[0m

# Main build target
all: $(OUTPUT_DIR) $(OUTPUT_DIR)/$(NAME)
	@rm -f *.o *.mod $(OBJS)
	

# Ensure the output directory exists
$(OUTPUT_DIR):
	@mkdir -p $(OUTPUT_DIR)

# Build FluLib.o
FluLib.o: FluLib.cpp
	@printf "$(COLOR_PURPLE)Generating Library $(COLOR_RED)$@$(COLOR_PURPLE)...$(COLOR_RESET)\n"
	$(CXX) -c $< $(ROOTCFLAGS)

# FLUKA Fortran source compilation
.f.$(ObjSuf):
	@printf "$(COLOR_PURPLE)Running FLUKA fff compiler for $(COLOR_RED)$<$(COLOR_PURPLE)...$(COLOR_RESET)\n"
	$(FLUKA)/bin/fff $<

# Main executable placed in RootFlukaExecutables/
$(OUTPUT_DIR)/$(NAME): $(OBJS) FluLib.$(ObjSuf)
	@printf "$(COLOR_PURPLE)Compiling executable $(COLOR_RED)$(NAME)$(COLOR_PURPLE) in $(COLOR_CYAN)$(FULL_OUTPUT_PATH)$(COLOR_PURPLE)...$(COLOR_RESET)\n"
	gfortran -o $@ -fuse-ld=bfd $(SYS_LDFLAGS) $^ $(LIBS)

# Clean target
clean:
	@printf "$(COLOR_PURPLE)Cleaning $(COLOR_CYAN)$(FULL_OUTPUT_PATH)/$(COLOR_RED)$(NAME)$(COLOR_PURPLE)...$(COLOR_RESET)\n"
	@rm -f $(OUTPUT_DIR)/$(NAME)* *.o *.so $(OBJS) rootfluka*

cleanall:
	@printf "$(COLOR_PURPLE)Cleaning $(COLOR_CYAN)$(FULL_OUTPUT_PATH)/$(COLOR_RED)*$(COLOR_PURPLE)...$(COLOR_RESET)\n"
	@rm -rf $(OUTPUT_DIR)/*

# Compile C++ source files into object files
.$(SrcSuf).$(ObjSuf):
	$(CXX) $(CXXFLAGS) -c $<

# Print variables (for debugging)
print-%:
	@printf $* = $($*)
