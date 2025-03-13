# Output directory and binary name
NAME ?= rootfluka
OUTPUT_DIR = RootFlukaExecutables
FULL_OUTPUT_PATH = $(shell pwd)/$(OUTPUT_DIR)

# Objects
OBJS ?= usrini.o usrout.o mgdraw.o

# OS and Architecture detection
OS   := $(shell uname)
ARCH := $(shell uname -m)

# FLUKA-VERSION detection
FLUKA_VERSION := $(shell basename $(shell fluka-config --path) | sed 's/^fluka//')
$(info FLUKA_VERSION = $(FLUKA_VERSION))

# File suffixes
ObjSuf  = o
SrcSuf  = cpp

# ROOT configuration
ROOTCFLAGS := $(shell root-config --cflags)
ROOTLIBS   := $(shell root-config --libs)
ROOTGLIBS  := $(shell root-config --glibs)

# FLUKA configuration
FLUKA 				:= $(shell fluka-config --path)
FLUKA_COMPILER 		:= $(shell fluka-config --compiler)
FLUKA_LIB_PATH 		:= $(shell fluka-config --libpath)
FLUKA_LIBS 			:= $(shell fluka-config --lib)
FLUKA_DPMLIB 		:= $(shell fluka-config --dpmlib)
FLUKA_RQMDLIB 		:= $(shell fluka-config --rqmdlib)
FLUKA_OPT_INTOBJS 	:= $(shell fluka-config --intobjs)

# OS-specific linker flags
SYS_LDFLAGS := -lz
ifeq ($(OS),Darwin)
	ifeq ($(ARCH),arm64)
		export MACOSX_DEPLOYMENT_TARGET = 15.0
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

# FLUKA library linking option
OPT_FLUKA_LIBS ?= 1
ifeq ($(OPT_FLUKA_LIBS), 1)
	LIBS += $(FLUKA_LIB_PATH) $(FLUKA_OPT_INTOBJS) $(FLUKA_RQMDLIB) $(FLUKA_DPMLIB) $(FLUKA_LIBS)
else
	LIBS += $(FLUKA_LIB_PATH) $(FLUKA_LIBS)
endif

# Main build target
all: $(OUTPUT_DIR) $(OUTPUT_DIR)/$(NAME)
	@rm -f *.o *.mod $(OBJS)

# Ensure the output directory exists
$(OUTPUT_DIR):
	@mkdir -p $(OUTPUT_DIR)

# Build FluLib.o
FluLib.o: FluLib.cpp
	@printf "Generating Library $@...\n"
	$(CXX) -c $< $(ROOTCFLAGS)

# FLUKA Fortran source compilation
.f.$(ObjSuf):
	@printf "Running FLUKA fff compiler for $<...\n"
	$(FLUKA)/bin/fff $<

# Main executable placed in RootFlukaExecutables/
$(OUTPUT_DIR)/$(NAME): $(OBJS) FluLib.$(ObjSuf)
	@printf "Compiling executable $(FULL_OUTPUT_PATH)/$(NAME)...\n"
	gfortran -o $@ -fuse-ld=bfd $(SYS_LDFLAGS) $^ $(LIBS)

# Clean target
clean:
	@printf "Cleaning $(FULL_OUTPUT_PATH)/$(NAME)...\n"
	@rm -f $(OUTPUT_DIR)/$(NAME)* *.o *.so $(OBJS) rootfluka*

cleanall:
	@printf "Cleaning $(FULL_OUTPUT_PATH)/*...\n"
	@rm -rf $(OUTPUT_DIR)/*

# Compile C++ source files into object files
.$(SrcSuf).$(ObjSuf):
	$(CXX) $(CXXFLAGS) -c $<

# Print variables (for debugging)
print-%:
	@printf $* = $($*)
