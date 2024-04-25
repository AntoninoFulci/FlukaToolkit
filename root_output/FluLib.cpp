
#include <stdio.h>
#include <iostream>
#include <TTree.h>
#include <TFile.h>


#ifndef WIN32
#define myusrini myusrini_
#else
#define myusrini MYUSRINI
#endif

static TFile *RootFile  = 0;
static TTree *Source    = 0;
static TTree *Events    = 0;
static TTree *DepEvents = 0;
static TTree *SimulationSummary = 0;

bool first1 = true;
bool first2 = true;
bool first3 = true;

extern "C" {
  void myusrini (){
    printf("Executing MYUSRINI\n");
    RootFile  = new TFile("dump.root","recreate");
    Source    = new TTree("Source", "Particles");
    Events    = new TTree("Events", "Particles");
    DepEvents = new TTree("DepEvents", "Particles");
    SimulationSummary = new TTree("RunSummary", "RunSummary");

    Source->SetAutoSave(0);
    Events->SetAutoSave(0);
    DepEvents->SetAutoSave(0);
    SimulationSummary->SetAutoSave(0);

  }
}

#ifndef WIN32
#define sourcefill sourcefill_
#else
#define sourcefill SOURCEFILL
#endif

extern "C" {
  void sourcefill(Int_t &NCase, Int_t &ParticleID,
                Double_t &EKin, Double_t &P, 
                Double_t &Vx, Double_t &Vy, Double_t &Vz,
                Double_t &Cx, Double_t &Cy, Double_t &Cz,
                Double_t &Weight
                ){
    if(first1){
      Source->Branch("NCase",&NCase);
      Source->Branch("ParticleID",&ParticleID);
      Source->Branch("EKin",&EKin);
      Source->Branch("P",&P);
      Source->Branch("Vx",&Vx);
      Source->Branch("Vy",&Vy);
      Source->Branch("Vz",&Vz);
      Source->Branch("Cx",&Cx);
      Source->Branch("Cy",&Cy);
      Source->Branch("Cz",&Cz);

      first1 = false;
    }


   Source->Fill();
  }
}

#ifndef WIN32
#define treefill treefill_
#else
#define treefill TREEFILL
#endif

extern "C" {
  void treefill(Int_t &NCase, Int_t &SurfaceID, Int_t &ParticleID,
                Double_t &ETot, Double_t &P, Double_t &Vx, Double_t &Vy, Double_t &Vz,
                Double_t &Px, Double_t &Py, Double_t &Pz,
                Double_t &Cx, Double_t &Cy, Double_t &Cz,
                Double_t &Weight1, Double_t &Weight2,
                Int_t &MotherID, Int_t &ProcessID,
                Double_t &MotherETot, Double_t &MotherVx, Double_t &MotherVy, Double_t &MotherVz,
                Double_t &UniqueID
                ){
    if(first2){
      Events->Branch("NCase",&NCase);
      Events->Branch("SurfaceID",&SurfaceID);
      Events->Branch("ParticleID",&ParticleID);
      Events->Branch("ETot",&ETot);
      Events->Branch("P",&P);
      Events->Branch("Vx",&Vx);
      Events->Branch("Vy",&Vy);
      Events->Branch("Vz",&Vz);
      Events->Branch("Px",&Px);
      Events->Branch("Py",&Py);
      Events->Branch("Pz",&Pz);
      Events->Branch("Cx",&Cx);
      Events->Branch("Cy",&Cy);
      Events->Branch("Cz",&Cz);
      Events->Branch("Weight1",&Weight1);
      Events->Branch("Weight2",&Weight2);
      Events->Branch("MotherID",&MotherID);
      Events->Branch("ProcessID",&ProcessID);
      Events->Branch("MotherETot",&MotherETot);
      Events->Branch("MotherVx",&MotherVx);
      Events->Branch("MotherVy",&MotherVy);
      Events->Branch("MotherVz",&MotherVz);
      Events->Branch("UniqueID",&UniqueID);

      first2 = false;
    }


   Events->Fill();
  }
}

#ifndef WIN32
#define depfill depfill_
#else
#define depfill DEPFILL
#endif

extern "C" {
  void depfill(Int_t &NCase, Int_t &RegionID, Int_t &ICode,Int_t &ParticleID,
                Double_t &ETot, Double_t &P, Double_t &Vx, Double_t &Vy, Double_t &Vz,
                Double_t &Px, Double_t &Py, Double_t &Pz,
                Double_t &Cx, Double_t &Cy, Double_t &Cz,
                Double_t &Weight1, Double_t &Weight2,
                Int_t &MotherID, Int_t &ProcessID,
                Double_t &MotherETot, Double_t &MotherVx, Double_t &MotherVy, Double_t &MotherVz
                ){
    if(first3){
      DepEvents->Branch("NCase",&NCase);
      DepEvents->Branch("RegionID",&RegionID);
      DepEvents->Branch("ICode",&ICode);
      DepEvents->Branch("ParticleID",&ParticleID);
      DepEvents->Branch("ETot",&ETot);
      DepEvents->Branch("P",&P);
      DepEvents->Branch("Vx",&Vx);
      DepEvents->Branch("Vy",&Vy);
      DepEvents->Branch("Vz",&Vz);
      DepEvents->Branch("Px",&Px);
      DepEvents->Branch("Py",&Py);
      DepEvents->Branch("Pz",&Pz);
      DepEvents->Branch("Cx",&Cx);
      DepEvents->Branch("Cy",&Cy);
      DepEvents->Branch("Cz",&Cz);
      DepEvents->Branch("Weight1",&Weight1);
      DepEvents->Branch("Weight2",&Weight2);
      DepEvents->Branch("MotherID",&MotherID);
      DepEvents->Branch("ProcessID",&ProcessID);
      DepEvents->Branch("MotherETot",&MotherETot);
      DepEvents->Branch("MotherVx",&MotherVx);
      DepEvents->Branch("MotherVy",&MotherVy);
      DepEvents->Branch("MotherVz",&MotherVz);

      first3 = false;
    }


   DepEvents->Fill();
  }
}




#ifndef WIN32
#define fileclose fileclose_
#else
#define fileclose FILECLOSE
#endif

extern "C" {
  void fileclose(Int_t &TotEvent, Double_t &AvgTime, Double_t &TotTime){

    //Write and fill SimulationSummary
    SimulationSummary->Branch("TotEvents",&TotEvent);
    SimulationSummary->Branch("AvgTime",&AvgTime);
    SimulationSummary->Branch("TotTime",&TotTime);
    SimulationSummary->Fill();

    SimulationSummary->Write();
    Source->Write();
    Events->Write();
    DepEvents->Write();

    RootFile->Close();
  }
}
