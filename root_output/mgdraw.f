*                                                                      *
*=== mgdraw ===========================================================*
*                                                                      *
      SUBROUTINE MGDRAW ( ICODE, MREG )

      INCLUDE 'dblprc.inc'
      INCLUDE 'dimpar.inc'
      INCLUDE 'iounit.inc'
*
*----------------------------------------------------------------------*
*                                                                      *
*     Copyright (C) 2022: CERN                                         *
*     All Rights Reserved.                                             *
*                                                                      *
*     MaGnetic field trajectory DRAWing: actually this entry manages   *
*                                        all trajectory dumping for    *
*                                        drawing                       *
*                                                                      *
*----------------------------------------------------------------------*
*
      INCLUDE 'caslim.inc'
      INCLUDE 'comput.inc'
      INCLUDE 'sourcm.inc'
      INCLUDE 'fheavy.inc'
      INCLUDE 'flkstk.inc'
      INCLUDE 'genstk.inc'
      INCLUDE 'mgddcm.inc'
      INCLUDE 'paprop.inc'
      INCLUDE 'quemgd.inc'
      INCLUDE 'sumcou.inc'
      INCLUDE 'trackr.inc'

      CHARACTER*8 INREG
      CHARACTER*8 OUTREG

      double precision :: pID

      INTEGER :: SURFID

      LOGICAL LFCOPE
      SAVE LFCOPE
      DATA LFCOPE / .FALSE. /
      
      CHARACTER(len=8), DIMENSION(97) :: FW_DET

      FW_DET = [CHARACTER(len=8) :: "NULL1", "NULL2", "NULL3",
     &"ENCLOS3","FW_DET5","FW_DET6",
     &"FW_DET7","FW_DET8","FW_DET9","FW_DET10","FW_DET11","FW_DET12",
     &"FW_DET13","FW_DET14","FW_DET15","FW_DET16","FW_DET17","FW_DET18",
     &"FW_DET19","FW_DET20","FW_DET21","FW_DET22","FW_DET23","FW_DET24",
     &"FW_DET25","FW_DET26","FW_DET27","FW_DET28","FW_DET29","FW_DET30",
     &"FW_DET31","FW_DET32","FW_DET33","FW_DET34","FW_DET35","FW_DET36",
     &"FW_DET37","FW_DET38","FW_DET39","FW_DET40","FW_DET41","FW_DET42",
     &"FW_DET43","FW_DET44","FW_DET45","FW_DET46","FW_DET47","FW_DET48",
     &"FW_DET49","FW_DET50","FW_DET51","FW_DET52","FW_DET53","FW_DET54",
     &"FW_DET55","FW_DET56","FW_DET57","FW_DET58","FW_DET59","FW_DET60",
     &"FW_DET61","FW_DET62","FW_DET63","FW_DET64","FW_DET65","FW_DET66",
     &"FW_DET67","FW_DET68","FW_DET69","FW_DET70","FW_DET71","FW_DET72",
     &"FW_DET73","FW_DET74","FW_DET75","FW_DET76","FW_DET77","FW_DET78",
     &"FW_DET79","FW_DET80","FW_DET81","FW_DET82","FW_DET83","FW_DET84",
     &"FW_DET85","FW_DET86","FW_DET87","FW_DET88","FW_DET89","FW_DET90",
     &"FW_DET91","FW_DET92","FW_DET93","FW_DET94","FW_DET95","FW_DET96",
     &"FW_DET97"
     &]

      RETURN
*
      ENTRY BXDRAW ( ICODE, MREG, NEWREG, XSCO, YSCO, ZSCO )

      CALL GEOR2N (MREG, INREG, IERR)
      CALL GEOR2N (NEWREG, OUTREG, IERR)

      !sample muons, neutrons and neutrinos that exits from the beam-dump
      IF( (JTRACK.eq.10).or.(JTRACK.eq.11)            !muons
     &.or.(JTRACK.eq.8)                               !neutrons
     &.or.(JTRACK.eq.5).or.(JTRACK.eq.6)              !neutrinos
     &.or.(JTRACK.eq.27).or.(JTRACK.eq.28)
     &.or.(JTRACK.eq.43).or.(JTRACK.eq.44)  
     &) THEN

      IF( (INREG.eq."ENCLOS1").and.(OUTREG.eq."NATM")
     &.or.(INREG.eq."ENCLOS1").and.(OUTREG.eq."ATM_TAIL")
     &.or.(INREG.eq."ENCLOS2").and.(OUTREG.eq."HEBLIN")
     &.or.(INREG.eq."ENCLOS2").and.(OUTREG.eq."NATM")
     &) THEN
            CALL treefill (NCASE,
     &               0,JTRACK,ETRACK,PTRACK,
     &               XSCO, YSCO, ZSCO,
     &               CXTRCK, CYTRCK, CZTRCK,
     &               WTRACK, WSCRNG,
     &               ISPUSR(1),ISPUSR(2),
     &               SPAUSR(1),SPAUSR(2),SPAUSR(3),SPAUSR(4),
     &               pID)

      END IF

      !at the beginning of the concrete after the dump
      IF( (INREG.eq."ENCLOS3").and.(OUTREG.eq."WALL1")      !when analyzing remember to fix vz=682.3462+4728.54=5410.8862
     &.or.(INREG.eq."ENCLOS3").and.(OUTREG.eq."FW_DET5")
     &) THEN
            CALL treefill (NCASE,
     &               1,JTRACK,ETRACK,PTRACK,
     &               XSCO, YSCO, ZSCO,
     &               CXTRCK, CYTRCK, CZTRCK,
     &               WTRACK, WSCRNG,
     &               ISPUSR(1),ISPUSR(2),
     &               SPAUSR(1),SPAUSR(2),SPAUSR(3),SPAUSR(4),
     &               pID)

      END IF

      !at the exit of the conrect after the dump on a very large surface
      !rember to costrint this during the analysis

      IF( (INREG.eq."Dumpcov").and.(OUTREG.eq."CEXIT")      !when analyzing remember to fix vz=6204.0
     &.or.(INREG.eq."FW_DET28").and.(OUTREG.eq."FW_DET29")
     &) THEN
            CALL treefill (NCASE,
     &               2,JTRACK,ETRACK,PTRACK,
     &               XSCO, YSCO, ZSCO,
     &               CXTRCK, CYTRCK, CZTRCK,
     &               WTRACK, WSCRNG,
     &               ISPUSR(1),ISPUSR(2),
     &               SPAUSR(1),SPAUSR(2),SPAUSR(3),SPAUSR(4),
     &               pID)

      END IF

      !sample neutrinos above ground for nuBDX
      IF( (INREG.eq."Dirt4").and.(OUTREG.eq."NUBDXD1")
     &) THEN
            CALL treefill (NCASE,
     &               101,JTRACK,ETRACK,PTRACK,
     &               XSCO, YSCO, ZSCO,
     &               CXTRCK, CYTRCK, CZTRCK,
     &               WTRACK, WSCRNG,
     &               ISPUSR(1),ISPUSR(2),
     &               SPAUSR(1),SPAUSR(2),SPAUSR(3),SPAUSR(4),
     &               pID)

      END IF

      END IF

      !sample muons impinging on BDX vault foward face
      IF( (JTRACK.eq.10).or.(JTRACK.eq.11)) THEN
      IF( (INREG.eq."FW_DET42").and.(OUTREG.eq."BDXCONC"))THEN
            CALL treefill (NCASE,
     &               3,JTRACK,ETRACK,PTRACK,
     &               XSCO, YSCO, ZSCO,
     &               CXTRCK, CYTRCK, CZTRCK,
     &               WTRACK, WSCRNG,
     &               ISPUSR(1),ISPUSR(2),
     &               SPAUSR(1),SPAUSR(2),SPAUSR(3),SPAUSR(4),
     &               pID)

      END IF
      END IF
      
      !sample everything that enters the detector
      IF((INREG.eq."BDXAIR").and.(OUTREG.eq."BDXDET")) THEN      
            
      CALL treefill (NCASE,
     &               4,JTRACK,ETRACK,PTRACK,
     &               XSCO, YSCO, ZSCO,
     &               CXTRCK, CYTRCK, CZTRCK,
     &               WTRACK, WSCRNG,
     &               ISPUSR(1),ISPUSR(2),
     &               SPAUSR(1),SPAUSR(2),SPAUSR(3),SPAUSR(4),
     &               pID)
      
      END IF


      RETURN
*
      ENTRY EEDRAW ( ICODE )
      RETURN
*
      ENTRY ENDRAW ( ICODE, MREG, RULL, XSCO, YSCO, ZSCO )
      RETURN
*
      ENTRY SODRAW

      !to activate this remember to put userdump what(4)=4
      CALL sourcefill ( NCASE, ILOFLK(NPFLKA),
     &                  TKEFLK(NPFLKA), PMOFLK(NPFLKA),
     &                  XFLK(NPFLKA), YFLK(NPFLKA), ZFLK(NPFLKA),
     &                  TXFLK(NPFLKA), TYFLK(NPFLKA), TZFLK(NPFLKA),
     &                  WTFLK(NPFLKA)
     &                )
     
      RETURN
*
      ENTRY USDRAW ( ICODE, MREG, XSCO, YSCO, ZSCO )

      !to activate this remember to put userdump what(5)=1

      !this to generic save the mother particle and production vertex, should work for everything except special cases handled below
      ISPUSR(1) = JTRACK      !mother particle ID
      ISPUSR(2) = ICODE       !process code

      SPAUSR(1) = ETRACK      !mother particle total energy

      SPAUSR(2) = XSCO        !interaction point
      SPAUSR(3) = YSCO
      SPAUSR(4) = ZSCO


      ! Everytime in the selectec region there is a muon in the secondary produced, then:
      ! if the muon is produced by the decay of something then it saves it thorugh the secondary stack
      ! if the muon is photoproduced it checks if the number of secondaries produced is less than 1 and it saves it through fluka stack

      ! In this case is better to use the region number instead of the name
      ! In this geometry we are interested to muons produced in the beam-dump
      ! Their number ranges from WINDOWS n122 to TANKTAIL n667


      IF ((ICODE.EQ.217).AND.(NP.LE.1).AND.(NPFLKA.GE.1)) THEN  !here to restrict for photoproduced particles where the number of secondaries is less than 1
            DO I=NPFLKA-1,NPFLKA
                  IF((ILOFLK(I).eq.10).or.(ILOFLK(I).eq.11)) THEN       !here to restrict for muons only
                        IF((MREG.ge.122).and.(MREG.le.667)) THEN        !here to selected a range of regions (the dump volume)
                        CALL usdfill(NCASE, MREG, ICODE, ILOFLK(I),
     &                               TKEFLK(I), PMOFLK(I), 
     &                               XSCO, YSCO, ZSCO,
     &                               TXFLK(I), TYFLK(I), TZFLK(I), WTFLK(I),
     &                               JTRACK, ETRACK)
                        END IF
                  END IF
            END DO
      ELSE IF (ICODE.EQ.102) THEN !select particles produced by decays
            AX=ZERZER
            AY=ZERZER
            AZ=ZERZER

            DO n=1, NP
!                 set custom icode for that dacay-at-rest or decay-in-flight
                  IF(ABS(AX).LT.ANGLGB.AND.ABS(AY).LT.ANGLGB.AND.ABS(AZ).LT.ANGLGB) THEN
                        ISPUSR(2) = 1021                !decay-at-rest
                  ELSE
                        ISPUSR(2) = 1020                !decay-in-flight
                  END IF

                  IF ((KPART(n).eq.10).or.(KPART(n).eq.11)) THEN !here to restrict for muons only
                        IF((MREG.ge.122).and.(MREG.le.667)) THEN !here to selected a range of regions (the dump volume)
                        CALL usdfill(NCASE, MREG, ISPUSR(2), KPART(n),
     &                               TKI(n), PLR(n), XSCO, YSCO, ZSCO,
     &                               CXR(n), CYR(n), CZR(n), WEI(n),
     &                               JTRACK, ETRACK)
                        END IF
                  END IF


            END DO
      END IF


      RETURN
*=== End of subrutine Mgdraw ==========================================*
      END

