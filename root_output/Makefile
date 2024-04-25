OS := $(shell uname)
ARCH := $(shell uname -m)
ObjSuf        = o
SrcSuf        = cpp

ROOTCFLAGS   := $(shell root-config --cflags)
ROOTLIBS     := $(shell root-config --libs)
ROOTGLIBS    := $(shell root-config --glibs)

FLUKA        := $(shell fluka-config --path)

# Used to solve a bug in XCode15
XCODEBUG      = -ld_classic -lz -lc++

#For MacOs
CXX           = g++
CXXFLAGS      = -O -Wall -fPIC 
LD            = g++
LDFLAGS       = -O $(XCODEBUG)
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

NAME 		   ?= rootfluka
OPT_FLUKA_LIBS ?= 0

ifeq ($(OPT_FLUKA_LIBS),1)
	LIBS += $(shell fluka-config --libpath) $(FLUKA_OPT_LIBS) -lrqmd -lDPMJET -lfluka
else
	LIBS += $(shell fluka-config --libpath) -lfluka
endif

#------------------------------------------------------------------------------
all:            FluLib.o rootfluka
		@rm -f *.o core *.so ResultsDict.cpp *.pcm $(OBJS)
		@mv rootfluka $(NAME)

FluLib.o:
	    @echo "Generating Library $@..."
	    g++ -c FluLib.cpp $(ROOTCFLAGS)

.f.$(ObjSuf):
	@echo "flutil/fff"
	       $(FLUKA)/bin/fff $?

rootfluka:     $(OBJS) FluLib.$(ObjSuf)
		gfortran -o $@ -fuse-ld=bfd $(XCODEBUG) $? $(LIBS)


clean:
		@rm -f rootfluka* *.o core *.so ResultsDict.cpp *.pcm $(OBJS)

.$(SrcSuf).$(ObjSuf):
	$(CXX) $(CXXFLAGS) -c $<

print-%:
	@echo $* = $($*)
