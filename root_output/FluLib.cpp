#include <stdio.h>
#include <iostream>
#include <TTree.h>
#include <TFile.h>
#include <ctime>

#ifndef WIN32
#define myusrini myusrini_
#else
#define myusrini MYUSRINI
#endif

// Pointers to ROOT file and trees
static TFile *RootFile  = 0;
static TTree *Source    = 0;
static TTree *Events    = 0;
static TTree *DepEvents = 0;
static TTree *USDEvents = 0;
static TTree *SimulationSummary = 0;

// Flags to check if branches are created
bool source_flag    = true;
bool events_flag    = true;
bool depevents_flag = true;
bool usdevents_flag = true;

// Variables for Source tree
int    NCase_src;
int    ParticleID_src;
double EKin_src;
double P_src; 
double Vx_src;
double Vy_src;
double Vz_src;
double Cx_src;
double Cy_src;
double Cz_src;
double Weight_src;

// Variables for Events tree
int    NCase_vnt;
int    SurfaceID_vnt;
int    ParticleID_vnt;
double ETot_vnt;
double P_vnt;
double Vx_vnt;
double Vy_vnt;
double Vz_vnt;
double Cx_vnt;
double Cy_vnt;
double Cz_vnt;
double Weight1_vnt;
double Weight2_vnt;
int    MotherID_vnt;
int    ProcessID_vnt;
double MotherETot_vnt;
double MotherVx_vnt;
double MotherVy_vnt;
double MotherVz_vnt;
double UniqueID_vnt;

// Variables for DepEvents tree
int    NCase_dep;
int    RegionID_dep;
int    ICode_dep;
int    ParticleID_dep;
double ETot_dep;
double P_dep;
double Vx_dep;
double Vy_dep;
double Vz_dep;
double Cx_dep;
double Cy_dep;
double Cz_dep;
double Weight1_dep;
double Weight2_dep;
int    MotherID_dep;
int    ProcessID_dep;
double MotherETot_dep;
double MotherVx_dep;
double MotherVy_dep;
double MotherVz_dep;
double UniqueID_dep;

// Variables for USDEvents tree
int    NCase_usd;
int    RegionID_usd;
int    ICode_usd;
int    ParticleID_usd;
double EKin_usd;
double P_usd;
double Vx_usd;
double Vy_usd;
double Vz_usd;
double Cx_usd;
double Cy_usd;
double Cz_usd;
double Weight_usd;
int    MotherID_usd;
double MotherETot_usd;

// Variable to store the start time of the simulation
std::time_t start_time;

extern "C" {
  void myusrini (){
    printf("Executing MYUSRINI\n");

    // Create ROOT file and trees
    RootFile  = new TFile("dump.root","recreate");
    Source    = new TTree("Source", "Particles");
    Events    = new TTree("Events", "Particles");
    DepEvents = new TTree("DepEvents", "Particles");
    USDEvents = new TTree("USDEvents", "Particles");
    SimulationSummary = new TTree("RunSummary", "RunSummary");

    // Disable auto-save for trees
    Source->SetAutoSave(0);
    Events->SetAutoSave(0);
    DepEvents->SetAutoSave(0);
    USDEvents->SetAutoSave(0);
    SimulationSummary->SetAutoSave(0);

    // Save the start time of the simulation
    start_time = std::time(nullptr);
    SimulationSummary->Branch("StartTime", &start_time);
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
    
    // Assign values to Source tree variables
    NCase_src       = NCase;
    ParticleID_src  = ParticleID;
    EKin_src        = EKin;  
    P_src           = P;
    Vx_src          = Vx;
    Vy_src          = Vy;
    Vz_src          = Vz;
    Cx_src          = Cx;
    Cy_src          = Cy;
    Cz_src          = Cz;
    Weight_src      = Weight;

    // Create branches for Source tree if not already created
    if(source_flag){
      Source->Branch("NCase",       &NCase_src);
      Source->Branch("ParticleID",  &ParticleID_src);
      Source->Branch("EKin",        &EKin_src);
      Source->Branch("P",           &P_src);
      Source->Branch("Vx",          &Vx_src);
      Source->Branch("Vy",          &Vy_src);
      Source->Branch("Vz",          &Vz_src);
      Source->Branch("Cx",          &Cx_src);
      Source->Branch("Cy",          &Cy_src);
      Source->Branch("Cz",          &Cz_src);

      source_flag = false;
    }

    // Fill the Source tree
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
                Double_t &Cx, Double_t &Cy, Double_t &Cz,
                Double_t &Weight1, Double_t &Weight2,
                Int_t &MotherID, Int_t &ProcessID,
                Double_t &MotherETot, Double_t &MotherVx, Double_t &MotherVy, Double_t &MotherVz,
                Double_t &UniqueID
                ){

    // Assign values to Events tree variables
    NCase_vnt       = NCase;
    SurfaceID_vnt   = SurfaceID;
    ParticleID_vnt  = ParticleID;
    ETot_vnt        = ETot;
    P_vnt           = P;
    Vx_vnt          = Vx;
    Vy_vnt          = Vy;
    Vz_vnt          = Vz;
    Cx_vnt          = Cx;
    Cy_vnt          = Cy;
    Cz_vnt          = Cz;
    Weight1_vnt     = Weight1;
    Weight2_vnt     = Weight2;
    MotherID_vnt    = MotherID;
    ProcessID_vnt   = ProcessID;
    MotherETot_vnt  = MotherETot;
    MotherVx_vnt    = MotherVx;
    MotherVy_vnt    = MotherVy;
    MotherVz_vnt    = MotherVz;
    UniqueID_vnt    = UniqueID;

    // Create branches for Events tree if not already created
    if(events_flag){
      Events->Branch("NCase",       &NCase_vnt);
      Events->Branch("SurfaceID",   &SurfaceID_vnt);
      Events->Branch("ParticleID",  &ParticleID_vnt);
      Events->Branch("ETot",        &ETot_vnt);
      Events->Branch("P",           &P_vnt);
      Events->Branch("Vx",          &Vx_vnt);
      Events->Branch("Vy",          &Vy_vnt);
      Events->Branch("Vz",          &Vz_vnt);
      Events->Branch("Cx",          &Cx_vnt);
      Events->Branch("Cy",          &Cy_vnt);
      Events->Branch("Cz",          &Cz_vnt);
      Events->Branch("Weight1",     &Weight1_vnt);
      Events->Branch("Weight2",     &Weight2_vnt);
      Events->Branch("MotherID",    &MotherID_vnt);
      Events->Branch("ProcessID",   &ProcessID_vnt);
      Events->Branch("MotherETot",  &MotherETot_vnt);
      Events->Branch("MotherVx",    &MotherVx_vnt);
      Events->Branch("MotherVy",    &MotherVy_vnt);
      Events->Branch("MotherVz",    &MotherVz_vnt);
      Events->Branch("UniqueID",    &UniqueID_vnt);

      events_flag = false;
    }

    // Fill the Events tree
    Events->Fill();
  }
}

#ifndef WIN32
#define depfill depfill_
#else
#define depfill DEPFILL
#endif

extern "C" {
  void depfill(Int_t &NCase, Int_t &RegionID, Int_t &ICode, Int_t &ParticleID,
                Double_t &ETot, Double_t &P, Double_t &Vx, Double_t &Vy, Double_t &Vz,
                Double_t &Cx, Double_t &Cy, Double_t &Cz,
                Double_t &Weight1, Double_t &Weight2,
                Int_t &MotherID, Int_t &ProcessID,
                Double_t &MotherETot, Double_t &MotherVx, Double_t &MotherVy, Double_t &MotherVz
                ){

    // Assign values to DepEvents tree variables
    NCase_dep       = NCase;
    RegionID_dep    = RegionID;
    ICode_dep       = ICode;
    ParticleID_dep  = ParticleID;
    ETot_dep        = ETot;
    P_dep           = P;
    Vx_dep          = Vx;
    Vy_dep          = Vy;
    Vz_dep          = Vz;
    Cx_dep          = Cx;
    Cy_dep          = Cy;
    Cz_dep          = Cz;
    Weight1_dep     = Weight1;
    Weight2_dep     = Weight2;
    MotherID_dep    = MotherID;
    ProcessID_dep   = ProcessID;
    MotherETot_dep  = MotherETot;
    MotherVx_dep    = MotherVx;
    MotherVy_dep    = MotherVy;
    MotherVz_dep    = MotherVz;              

    // Create branches for DepEvents tree if not already created
    if(depevents_flag){
      DepEvents->Branch("NCase",      &NCase_dep);
      DepEvents->Branch("RegionID",   &RegionID_dep);
      DepEvents->Branch("ICode",      &ICode_dep);
      DepEvents->Branch("ParticleID", &ParticleID_dep);
      DepEvents->Branch("ETot",       &ETot_dep);
      DepEvents->Branch("P",          &P_dep);
      DepEvents->Branch("Vx",         &Vx_dep);
      DepEvents->Branch("MotherVx",   &MotherVx_dep);
      DepEvents->Branch("MotherVy",   &MotherVy_dep);
      DepEvents->Branch("MotherVz",   &MotherVz_dep);

      depevents_flag = false;
    }


   DepEvents->Fill();
  }
}

#ifndef WIN32
#define usdfill usdfill_
#else
#define usdfill USDFILL
#endif

extern "C" {
  void usdfill(Int_t &NCase, Int_t &RegionID, Int_t &ICode, Int_t &ParticleID,
                Double_t &EKin, Double_t &P, Double_t &Vx, Double_t &Vy, Double_t &Vz,
                Double_t &Cx, Double_t &Cy, Double_t &Cz,
                Double_t &Weight,
                Int_t &MotherID,
                Double_t &MotherETot
                ){

    NCase_usd       = NCase;
    RegionID_usd    = RegionID;
    ICode_usd       = ICode;
    ParticleID_usd  = ParticleID;
    EKin_usd        = EKin;
    P_usd           = P;
    Vx_usd          = Vx;
    Vy_usd          = Vy;
    Vz_usd          = Vz;
    Cx_usd          = Cx;
    Cy_usd          = Cy;
    Cz_usd          = Cz;
    Weight_usd      = Weight;
    MotherID_usd    = MotherID;
    MotherETot_usd  = MotherETot;            

    if(usdevents_flag){
      USDEvents->Branch("NCase",      &NCase_usd);
      USDEvents->Branch("RegionID",   &RegionID_usd);
      USDEvents->Branch("ICode",      &ICode_usd);
      USDEvents->Branch("ParticleID", &ParticleID_usd);
      USDEvents->Branch("EKin",       &EKin_usd);
      USDEvents->Branch("P",          &P_usd);
      USDEvents->Branch("Vx",         &Vx_usd);
      USDEvents->Branch("Vy",         &Vy_usd);
      USDEvents->Branch("Vz",         &Vz_usd);
      USDEvents->Branch("Cx",         &Cx_usd);
      USDEvents->Branch("Cy",         &Cy_usd);
      USDEvents->Branch("Cz",         &Cz_usd);
      USDEvents->Branch("Weight",     &Weight_usd);
      USDEvents->Branch("MotherID",   &MotherID_usd);
      USDEvents->Branch("MotherETot", &MotherETot_usd);

      usdevents_flag = false;
    }


   USDEvents->Fill();
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
    SimulationSummary->Branch("AvgTime",  &AvgTime);
    SimulationSummary->Branch("TotTime",  &TotTime);
    SimulationSummary->Fill();

    SimulationSummary->Write();
    Source->Write();
    Events->Write();
    DepEvents->Write();
    USDEvents->Write();

    RootFile->Close();
  }
}
