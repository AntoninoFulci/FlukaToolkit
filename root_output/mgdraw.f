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
*     Copyright (C) 2003-2019:  CERN & INFN                            *
*     All Rights Reserved.                                             *
*                                                                      *
*     MaGnetic field trajectory DRAWing: actually this entry manages   *
*                                        all trajectory dumping for    *
*                                        drawing                       *
*                                                                      *
*     Created on   01 March 1990   by        Alfredo Ferrari           *
*                                              INFN - Milan            *
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
*
      DIMENSION DTQUEN ( MXTRCK, MAXQMG )
*
      CHARACTER*20 FILNAM
      CHARACTER*8 FL_InReg
      CHARACTER*8 FL_OutReg
      CHARACTER*8 REGION

      INTEGER SURFACEID
      INTEGER REGIONID
      
      double precision :: pID

      LOGICAL LFCOPE

      SAVE LFCOPE

      DATA LFCOPE / .FALSE. /

      RETURN
      
**********************************************************************
**********************************************************************
**********************************************************************

      ENTRY BXDRAW ( ICODE, MREG, NEWREG, XSCO, YSCO, ZSCO )

*     Ottiene il nome della regione d'uscita e lo mette in NAMREG
      CALL GEOR2N (MREG, FL_InReg, IERR)
*     Ottiene il nome  della regione d'entrata e lo mette in NAMREG2
      CALL GEOR2N (NEWREG, FL_OutReg, IERR)
      

      IF((JTRACK.eq.10).or.(JTRACK.eq.11)) THEN

      IF( (FL_InReg.eq."AIRGAIN").and.(FL_OutReg.eq."BOX3")
     &.or.(FL_InReg.eq."DIPSH3") .and.(FL_OutReg.eq."BOX1")
     &.or.(FL_InReg.eq."PermSh") .and.(FL_OutReg.eq."BOX1")
     &.or.(FL_InReg.eq."SHDW1")  .and.(FL_OutReg.eq."BOX1")
     &.or.(FL_InReg.eq."SHDW2")  .and.(FL_OutReg.eq."BOX1")
     &.or.(FL_InReg.eq."FESRFE") .and.(FL_OutReg.eq."BOX2")
     &.or.(FL_InReg.eq."SRFE")   .and.(FL_OutReg.eq."BOX2")
     &.or.(FL_InReg.eq."ALSRFE") .and.(FL_OutReg.eq."BOX2")
     &)THEN
      SURFACEID = 1
      ! write(*,*) "Surface IN", FL_InReg, "Surface OUT", FL_OutReg, "Vz", ZSCO
      CALL treefill (NCASE,
     &                  SURFACEID,JTRACK,ETRACK,PTRACK,
     &                  XSCO, YSCO, ZSCO,
     &                  PTRACK*CXTRCK, PTRACK*CYTRCK, PTRACK*CZTRCK,
     &                  CXTRCK, CYTRCK, CZTRCK,
     &                  WTRACK, WSCRNG,
     &                  ISPUSR(1),ISPUSR(2),
     &                  SPAUSR(2),SPAUSR(3),SPAUSR(4),SPAUSR(5),
     &                  pID)
        END IF
 
      END IF
      
      RETURN

      ENTRY EEDRAW ( ICODE )
      RETURN

*======================================================================*
*                                                                      *
*     ENergy deposition DRAWing:                                       *
*                                                                      *
*     Icode = 1x: call from Kaskad                                     *
*             10: elastic interaction recoil                           *
*             11: inelastic interaction recoil                         *
*             12: stopping particle                                    *
*             13: pseudo-neutron deposition                            *
*             14: escape                                               *
*             15: time kill                                            *
*             16: recoil from (heavy) bremsstrahlung                   *
*     Icode = 2x: call from Emfsco                                     *
*             20: local energy deposition (i.e. photoelectric)         *
*             21: below threshold, iarg=1                              *
*             22: below threshold, iarg=2                              *
*             23: escape                                               *
*             24: time kill                                            *
*     Icode = 3x: call from Kasneu                                     *
*             30: target recoil                                        *
*             31: below threshold                                      *
*             32: escape                                               *
*             33: time kill                                            *
*     Icode = 4x: call from Kashea                                     *
*             40: escape                                               *
*             41: time kill                                            *
*             42: delta ray stack overflow                             *
*     Icode = 5x: call from Kasoph                                     *
*             50: optical photon absorption                            *
*             51: escape                                               *
*             52: time kill                                            *
*                                                                      *
*======================================================================*
*                                                                      *

      ENTRY ENDRAW ( ICODE, MREG, RULL, XSCO, YSCO, ZSCO )

      RETURN
*
*======================================================================*
*                                                                      *
*     SOurce particle DRAWing:                                         *
*                                                                      *
*======================================================================*
*
      ENTRY SODRAW

      RETURN
*
      ENTRY USDRAW ( ICODE, MREG, XSCO, YSCO, ZSCO )

* No output by default:
      RETURN
*=== End of subrutine Mgdraw ==========================================*
      END

