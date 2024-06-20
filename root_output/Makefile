OS := $(shell uname)
ARCH := $(shell uname -m)
ObjSuf        = o
SrcSuf        = cpp

ROOTCFLAGS   := $(shell root-config --cflags)
ROOTLIBS     := $(shell root-config --libs)
ROOTGLIBS    := $(shell root-config --glibs)

FLUKA        := $(shell fluka-config --path)

# Used to solve a bug in XCode15
ifeq ($(OS),Darwin)
	ifeq ($(ARCH),arm64)
		SYS_LDFLAGS = -ld_classic -lz -lc++
	endif
else
	SYS_LDFLAGS = -lz
endif

#For MacOs
CXX           = g++
CXXFLAGS      = -O -Wall -fPIC 
LD            = g++
LDFLAGS       = -O $(SYS_LDFLAGS)
SOFLAGS       = -shared

CXXFLAGS     += $(ROOTCFLAGS)
LIBS          = -lstdc++
LIBS         += -L.
LIBS         += $(ROOTLIBS) $(SYSLIBS)

FLUKA_OPT_LIBS 		:= $(wildcard $(FLUKA)/lib/interface/*.o)

GLIBS         = $(ROOTGLIBS) $(SYSLIBS)

#------------------------------------------------------------------------------

OBJS            = usrini.o usrout.o
OBJS           += mgdraw.o
# OBJS		   += source_newgen.o

NAME 		   ?= rootfluka
OPT_FLUKA_LIBS ?= 1

ifeq ($(OPT_FLUKA_LIBS),1)
	LIBS += $(shell fluka-config --libpath) $(FLUKA_OPT_LIBS) -lrqmd -lDPMJET -lfluka
else
	LIBS += $(shell fluka-config --libpath) -lfluka
endif

#------------------------------------------------------------------------------
all:            FluLib.o rootfluka
		@rm -f *.o core *.so ResultsDict.cpp *.pcm $(OBJS)
		@if [ $(NAME) != "rootfluka" ]; then\
			mv rootfluka $(NAME);\
		fi
		

FluLib.o:
	    @echo "Generating Library $@..."
	    g++ -c FluLib.cpp $(ROOTCFLAGS)

.f.$(ObjSuf):
	@echo "flutil/fff"
	       $(FLUKA)/bin/fff $?

rootfluka:     $(OBJS) FluLib.$(ObjSuf)
		gfortran -o $@ -fuse-ld=bfd $(SYS_LDFLAGS) $? $(LIBS)


clean:
		@rm -f rootfluka* *.o core *.so ResultsDict.cpp *.pcm $(OBJS)

.$(SrcSuf).$(ObjSuf):
	$(CXX) $(CXXFLAGS) -c $<

print-%:
	@echo $* = $($*)
