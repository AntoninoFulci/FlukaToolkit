#include <stdio.h>
#include <iostream>
#include <TTree.h>
#include <TFile.h>
#include <TSystem.h>
#include <ctime>
#include <ROOT/RNTuple.hxx>
#include <ROOT/RNTupleModel.hxx>
#include <ROOT/RNTupleWriter.hxx>

#ifndef WIN32
#define myusrini myusrini_
#else
#define myusrini MYUSRINI
#endif

// Pointers to ROOT file and RNTuple writer
static std::unique_ptr<TFile> RootFile = nullptr;
static std::unique_ptr<ROOT::RNTupleWriter> SimulationSummaryWriter = nullptr;
static std::unique_ptr<ROOT::RNTupleWriter> SourceWriter = nullptr;
static std::unique_ptr<ROOT::RNTupleWriter> EventsWriter = nullptr;
static std::unique_ptr<ROOT::RNTupleWriter> DepEventsWriter = nullptr;
static std::unique_ptr<ROOT::RNTupleWriter> USDEventsWriter = nullptr;

// Pointers to RNTuple fields
static std::shared_ptr<std::time_t> ptrStartTime = nullptr;
static std::shared_ptr<int> ptrTotEvents = nullptr;
static std::shared_ptr<double> ptrAvgTime = nullptr;
static std::shared_ptr<double> ptrTotTime = nullptr;

// Source fields
static std::shared_ptr<int> ptrNCase_src = nullptr;
static std::shared_ptr<int> ptrParticleID_src = nullptr;
static std::shared_ptr<double> ptrEKin_src = nullptr;
static std::shared_ptr<double> ptrP_src = nullptr;
static std::shared_ptr<double> ptrVx_src = nullptr;
static std::shared_ptr<double> ptrVy_src = nullptr;
static std::shared_ptr<double> ptrVz_src = nullptr;
static std::shared_ptr<double> ptrCx_src = nullptr;
static std::shared_ptr<double> ptrCy_src = nullptr;
static std::shared_ptr<double> ptrCz_src = nullptr;
static std::shared_ptr<double> ptrWeight_src = nullptr;

// Events fields
static std::shared_ptr<int> ptrNCase_vnt = nullptr;
static std::shared_ptr<int> ptrSurfaceID_vnt = nullptr;
static std::shared_ptr<int> ptrParticleID_vnt = nullptr;
static std::shared_ptr<double> ptrETot_vnt = nullptr;
static std::shared_ptr<double> ptrP_vnt = nullptr;
static std::shared_ptr<double> ptrVx_vnt = nullptr;
static std::shared_ptr<double> ptrVy_vnt = nullptr;
static std::shared_ptr<double> ptrVz_vnt = nullptr;
static std::shared_ptr<double> ptrCx_vnt = nullptr;
static std::shared_ptr<double> ptrCy_vnt = nullptr;
static std::shared_ptr<double> ptrCz_vnt = nullptr;
static std::shared_ptr<double> ptrWeight1_vnt = nullptr;
static std::shared_ptr<double> ptrWeight2_vnt = nullptr;
static std::shared_ptr<int> ptrMotherID_vnt = nullptr;
static std::shared_ptr<int> ptrProcessID_vnt = nullptr;
static std::shared_ptr<double> ptrMotherETot_vnt = nullptr;
static std::shared_ptr<double> ptrMotherVx_vnt = nullptr;
static std::shared_ptr<double> ptrMotherVy_vnt = nullptr;
static std::shared_ptr<double> ptrMotherVz_vnt = nullptr;
static std::shared_ptr<double> ptrUniqueID_vnt = nullptr;

// DepEvents fields
static std::shared_ptr<int> ptrNCase_dep = nullptr;
static std::shared_ptr<int> ptrRegionID_dep = nullptr;
static std::shared_ptr<int> ptrICode_dep = nullptr;
static std::shared_ptr<int> ptrParticleID_dep = nullptr;
static std::shared_ptr<double> ptrETot_dep = nullptr;
static std::shared_ptr<double> ptrP_dep = nullptr;
static std::shared_ptr<double> ptrVx_dep = nullptr;
static std::shared_ptr<double> ptrVy_dep = nullptr;
static std::shared_ptr<double> ptrVz_dep = nullptr;
static std::shared_ptr<double> ptrCx_dep = nullptr;
static std::shared_ptr<double> ptrCy_dep = nullptr;
static std::shared_ptr<double> ptrCz_dep = nullptr;
static std::shared_ptr<double> ptrWeight1_dep = nullptr;
static std::shared_ptr<double> ptrWeight2_dep = nullptr;
static std::shared_ptr<int> ptrMotherID_dep = nullptr;
static std::shared_ptr<int> ptrProcessID_dep = nullptr;
static std::shared_ptr<double> ptrMotherETot_dep = nullptr;
static std::shared_ptr<double> ptrMotherVx_dep = nullptr;
static std::shared_ptr<double> ptrMotherVy_dep = nullptr;
static std::shared_ptr<double> ptrMotherVz_dep = nullptr;
static std::shared_ptr<double> ptrUniqueID_dep = nullptr;

// USDEvents fields
static std::shared_ptr<int> ptrNCase_usd = nullptr;
static std::shared_ptr<int> ptrRegionID_usd = nullptr;
static std::shared_ptr<int> ptrICode_usd = nullptr;
static std::shared_ptr<int> ptrParticleID_usd = nullptr;
static std::shared_ptr<double> ptrEKin_usd = nullptr;
static std::shared_ptr<double> ptrP_usd = nullptr;
static std::shared_ptr<double> ptrVx_usd = nullptr;
static std::shared_ptr<double> ptrVy_usd = nullptr;
static std::shared_ptr<double> ptrVz_usd = nullptr;
static std::shared_ptr<double> ptrCx_usd = nullptr;
static std::shared_ptr<double> ptrCy_usd = nullptr;
static std::shared_ptr<double> ptrCz_usd = nullptr;
static std::shared_ptr<double> ptrWeight_usd = nullptr;
static std::shared_ptr<int> ptrMotherID_usd = nullptr;
static std::shared_ptr<double> ptrMotherETot_usd = nullptr;

extern "C" {
  void myusrini (){
    printf("Executing MYUSRINI (RNTuple version)\n");

    // Remove any existing file to start clean
    gSystem->Unlink("dump.root");

    // Create an empty ROOT file first
    RootFile = std::make_unique<TFile>("dump.root", "RECREATE");
    RootFile->Close();

    // Now open the file in UPDATE mode for all RNTuples
    RootFile = std::make_unique<TFile>("dump.root", "UPDATE");

    // Create RNTuple model for simulation summary
    auto summaryModel = ROOT::RNTupleModel::Create();
    ptrStartTime = summaryModel->MakeField<std::time_t>("StartTime");
    ptrTotEvents = summaryModel->MakeField<int>("TotEvents");
    ptrAvgTime = summaryModel->MakeField<double>("AvgTime");
    ptrTotTime = summaryModel->MakeField<double>("TotTime");
    printf("Created summary model with fields\n");

    // Create RNTuple writer for simulation summary
    SimulationSummaryWriter = ROOT::RNTupleWriter::Append(std::move(summaryModel), "SimulationSummary", *RootFile);
    printf("Created SimulationSummaryWriter: %p\n", SimulationSummaryWriter.get());

    // Initialize the start time
    *ptrStartTime = std::time(nullptr);

    // Create RNTuple model for Source
    auto sourceModel = ROOT::RNTupleModel::Create();
    ptrNCase_src = sourceModel->MakeField<int>("NCase");
    ptrParticleID_src = sourceModel->MakeField<int>("ParticleID");
    ptrEKin_src = sourceModel->MakeField<double>("EKin");
    ptrP_src = sourceModel->MakeField<double>("P");
    ptrVx_src = sourceModel->MakeField<double>("Vx");
    ptrVy_src = sourceModel->MakeField<double>("Vy");
    ptrVz_src = sourceModel->MakeField<double>("Vz");
    ptrCx_src = sourceModel->MakeField<double>("Cx");
    ptrCy_src = sourceModel->MakeField<double>("Cy");
    ptrCz_src = sourceModel->MakeField<double>("Cz");
    ptrWeight_src = sourceModel->MakeField<double>("Weight");

    // Create RNTuple writer for Source (use Append for subsequent RNTuples)
    SourceWriter = ROOT::RNTupleWriter::Append(std::move(sourceModel), "Source", *RootFile);
    printf("Created SourceWriter: %p\n", SourceWriter.get());
    // printf("Skipping SourceWriter creation for debugging\n");

    // Create RNTuple model for Events
    auto eventsModel = ROOT::RNTupleModel::Create();
    ptrNCase_vnt = eventsModel->MakeField<int>("NCase");
    ptrSurfaceID_vnt = eventsModel->MakeField<int>("SurfaceID");
    ptrParticleID_vnt = eventsModel->MakeField<int>("ParticleID");
    ptrETot_vnt = eventsModel->MakeField<double>("ETot");
    ptrP_vnt = eventsModel->MakeField<double>("P");
    ptrVx_vnt = eventsModel->MakeField<double>("Vx");
    ptrVy_vnt = eventsModel->MakeField<double>("Vy");
    ptrVz_vnt = eventsModel->MakeField<double>("Vz");
    ptrCx_vnt = eventsModel->MakeField<double>("Cx");
    ptrCy_vnt = eventsModel->MakeField<double>("Cy");
    ptrCz_vnt = eventsModel->MakeField<double>("Cz");
    ptrWeight1_vnt = eventsModel->MakeField<double>("Weight1");
    ptrWeight2_vnt = eventsModel->MakeField<double>("Weight2");
    ptrMotherID_vnt = eventsModel->MakeField<int>("MotherID");
    ptrProcessID_vnt = eventsModel->MakeField<int>("ProcessID");
    ptrMotherETot_vnt = eventsModel->MakeField<double>("MotherETot");
    ptrMotherVx_vnt = eventsModel->MakeField<double>("MotherVx");
    ptrMotherVy_vnt = eventsModel->MakeField<double>("MotherVy");
    ptrMotherVz_vnt = eventsModel->MakeField<double>("MotherVz");
    ptrUniqueID_vnt = eventsModel->MakeField<double>("UniqueID");

    // Create RNTuple writer for Events
    EventsWriter = ROOT::RNTupleWriter::Append(std::move(eventsModel), "Events", *RootFile);
    printf("Created EventsWriter: %p\n", EventsWriter.get());

    // Create RNTuple model for DepEvents
    auto depEventsModel = ROOT::RNTupleModel::Create();
    ptrNCase_dep = depEventsModel->MakeField<int>("NCase");
    ptrRegionID_dep = depEventsModel->MakeField<int>("RegionID");
    ptrICode_dep = depEventsModel->MakeField<int>("ICode");
    ptrParticleID_dep = depEventsModel->MakeField<int>("ParticleID");
    ptrETot_dep = depEventsModel->MakeField<double>("ETot");
    ptrP_dep = depEventsModel->MakeField<double>("P");
    ptrVx_dep = depEventsModel->MakeField<double>("Vx");
    ptrVy_dep = depEventsModel->MakeField<double>("Vy");
    ptrVz_dep = depEventsModel->MakeField<double>("Vz");
    ptrCx_dep = depEventsModel->MakeField<double>("Cx");
    ptrCy_dep = depEventsModel->MakeField<double>("Cy");
    ptrCz_dep = depEventsModel->MakeField<double>("Cz");
    ptrWeight1_dep = depEventsModel->MakeField<double>("Weight1");
    ptrWeight2_dep = depEventsModel->MakeField<double>("Weight2");
    ptrMotherID_dep = depEventsModel->MakeField<int>("MotherID");
    ptrProcessID_dep = depEventsModel->MakeField<int>("ProcessID");
    ptrMotherETot_dep = depEventsModel->MakeField<double>("MotherETot");
    ptrMotherVx_dep = depEventsModel->MakeField<double>("MotherVx");
    ptrMotherVy_dep = depEventsModel->MakeField<double>("MotherVy");
    ptrMotherVz_dep = depEventsModel->MakeField<double>("MotherVz");
    ptrUniqueID_dep = depEventsModel->MakeField<double>("UniqueID");

    // Create RNTuple writer for DepEvents
    DepEventsWriter = ROOT::RNTupleWriter::Append(std::move(depEventsModel), "DepEvents", *RootFile);
    // printf("Skipping DepEventsWriter creation for debugging\n");

    // Create RNTuple model for USDEvents
    auto usdEventsModel = ROOT::RNTupleModel::Create();
    ptrNCase_usd = usdEventsModel->MakeField<int>("NCase");
    ptrRegionID_usd = usdEventsModel->MakeField<int>("RegionID");
    ptrICode_usd = usdEventsModel->MakeField<int>("ICode");
    ptrParticleID_usd = usdEventsModel->MakeField<int>("ParticleID");
    ptrEKin_usd = usdEventsModel->MakeField<double>("EKin");
    ptrP_usd = usdEventsModel->MakeField<double>("P");
    ptrVx_usd = usdEventsModel->MakeField<double>("Vx");
    ptrVy_usd = usdEventsModel->MakeField<double>("Vy");
    ptrVz_usd = usdEventsModel->MakeField<double>("Vz");
    ptrCx_usd = usdEventsModel->MakeField<double>("Cx");
    ptrCy_usd = usdEventsModel->MakeField<double>("Cy");
    ptrCz_usd = usdEventsModel->MakeField<double>("Cz");
    ptrWeight_usd = usdEventsModel->MakeField<double>("Weight");
    ptrMotherID_usd = usdEventsModel->MakeField<int>("MotherID");
    ptrMotherETot_usd = usdEventsModel->MakeField<double>("MotherETot");

    // Create RNTuple writer for USDEvents
    USDEventsWriter = ROOT::RNTupleWriter::Append(std::move(usdEventsModel), "USDEvents", *RootFile);
    // printf("Skipping USDEventsWriter creation for debugging\n");
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

    // Check if field pointers are valid
    if (!ptrNCase_src) {
      printf("ERROR: ptrNCase_src is null!\n");
      return;
    }

    // Set values in Source RNTuple fields
    *ptrNCase_src = NCase;
    *ptrParticleID_src = ParticleID;
    *ptrEKin_src = EKin;
    *ptrP_src = P;
    *ptrVx_src = Vx;
    *ptrVy_src = Vy;
    *ptrVz_src = Vz;
    *ptrCx_src = Cx;
    *ptrCy_src = Cy;
    *ptrCz_src = Cz;
    *ptrWeight_src = Weight;

    // Fill the Source RNTuple
    if (SourceWriter) {
      SourceWriter->Fill();
      printf("Filled Source RNTuple entry: NCase=%d, ParticleID=%d\n", NCase, ParticleID);
    } else {
      printf("ERROR: SourceWriter is null!\n");
    }
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

    printf(" inside\n");

    // Check if field pointers are valid
    if (!ptrNCase_vnt) {
      printf("ERROR: ptrNCase_vnt is null!\n");
      return;
    }

    // Set values in Events RNTuple fields
    *ptrNCase_vnt = NCase;
    *ptrSurfaceID_vnt = SurfaceID;
    *ptrParticleID_vnt = ParticleID;
    *ptrETot_vnt = ETot;
    *ptrP_vnt = P;
    *ptrVx_vnt = Vx;
    *ptrVy_vnt = Vy;
    *ptrVz_vnt = Vz;
    *ptrCx_vnt = Cx;
    *ptrCy_vnt = Cy;
    *ptrCz_vnt = Cz;
    *ptrWeight1_vnt = Weight1;
    *ptrWeight2_vnt = Weight2;
    *ptrMotherID_vnt = MotherID;
    *ptrProcessID_vnt = ProcessID;
    *ptrMotherETot_vnt = MotherETot;
    *ptrMotherVx_vnt = MotherVx;
    *ptrMotherVy_vnt = MotherVy;
    *ptrMotherVz_vnt = MotherVz;
    *ptrUniqueID_vnt = UniqueID;

    // Fill the Events RNTuple
    if (EventsWriter) {
      EventsWriter->Fill();
      printf("Filled Events RNTuple entry: NCase=%d, SurfaceID=%d, ParticleID=%d\n", NCase, SurfaceID, ParticleID);
    } else {
      printf("ERROR: EventsWriter is null!\n");
    }
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
                Double_t &MotherETot, Double_t &MotherVx, Double_t &MotherVy, Double_t &MotherVz,
                Double_t &UniqueID
                ){

    // Set values in DepEvents RNTuple fields
    *ptrNCase_dep = NCase;
    *ptrRegionID_dep = RegionID;
    *ptrICode_dep = ICode;
    *ptrParticleID_dep = ParticleID;
    *ptrETot_dep = ETot;
    *ptrP_dep = P;
    *ptrVx_dep = Vx;
    *ptrVy_dep = Vy;
    *ptrVz_dep = Vz;
    *ptrCx_dep = Cx;
    *ptrCy_dep = Cy;
    *ptrCz_dep = Cz;
    *ptrWeight1_dep = Weight1;
    *ptrWeight2_dep = Weight2;
    *ptrMotherID_dep = MotherID;
    *ptrProcessID_dep = ProcessID;
    *ptrMotherETot_dep = MotherETot;
    *ptrMotherVx_dep = MotherVx;
    *ptrMotherVy_dep = MotherVy;
    *ptrMotherVz_dep = MotherVz;
    *ptrUniqueID_dep = UniqueID;

    // Fill the DepEvents RNTuple
    if (DepEventsWriter) {
      DepEventsWriter->Fill();
    }
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

    // Set values in USDEvents RNTuple fields
    *ptrNCase_usd = NCase;
    *ptrRegionID_usd = RegionID;
    *ptrICode_usd = ICode;
    *ptrParticleID_usd = ParticleID;
    *ptrEKin_usd = EKin;
    *ptrP_usd = P;
    *ptrVx_usd = Vx;
    *ptrVy_usd = Vy;
    *ptrVz_usd = Vz;
    *ptrCx_usd = Cx;
    *ptrCy_usd = Cy;
    *ptrCz_usd = Cz;
    *ptrWeight_usd = Weight;
    *ptrMotherID_usd = MotherID;
    *ptrMotherETot_usd = MotherETot;

    // Fill the USDEvents RNTuple
    if (USDEventsWriter) {
      USDEventsWriter->Fill();
    }
  }
}

#ifndef WIN32
#define fileclose fileclose_
#else
#define fileclose FILECLOSE
#endif

extern "C" {
  void fileclose(Int_t &TotEvent, Double_t &AvgTime_in, Double_t &TotTime_in){
    printf("Executing FILECLOSE (RNTuple version)\n");
    printf("Summary data: TotEvents=%d, AvgTime=%f, TotTime=%f\n", TotEvent, AvgTime_in, TotTime_in);

    // Set the final field values
    *ptrTotEvents = TotEvent;
    *ptrAvgTime = AvgTime_in;
    *ptrTotTime = TotTime_in;

    // Fill the simulation summary entry
    if (SimulationSummaryWriter) {
      SimulationSummaryWriter->Fill();
      printf("Filled SimulationSummary entry\n");
    } else {
      printf("ERROR: SimulationSummaryWriter is null!\n");
    }

    // Commit all datasets by resetting the writers
    SimulationSummaryWriter.reset();
    SourceWriter.reset();  // Commented out for debugging
    EventsWriter.reset();
    DepEventsWriter.reset();  // Commented out for debugging
    USDEventsWriter.reset();  // Commented out for debugging

    // Close and clean up the file
    if (RootFile) {
      RootFile->Close();
      RootFile.reset();
    }

    printf("Simulation complete. Data written to dump.root\n");
  }
}
