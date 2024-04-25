      SUBROUTINE MGDRAW ( ICODE, MREG )

      INCLUDE 'dblprc.inc'
      INCLUDE 'dimpar.inc'
      INCLUDE 'iounit.inc'
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

      DIMENSION DTQUEN ( MXTRCK, MAXQMG )

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
*======================================================================*
*                                                                      *
*     Trajectory dumping for drawing                                   *
*                                                                      *
*======================================================================*


      RETURN

*======================================================================*
*                                                                      *
*     Boundary Cross DRAWing                                           *
*                                                                      *
*======================================================================*

      ENTRY BXDRAW ( ICODE, MREG, NEWREG, XSCO, YSCO, ZSCO )

      CALL GEOR2N (MREG, FL_InReg, IERR)
      CALL GEOR2N (NEWREG, FL_OutReg, IERR)

      IF( (FL_InReg.eq."REG1").and.(FL_OutReg.eq."REG2")
     &)THEN
      SURFACEID = 1

      CALL treefill (NCASE,
     &               SURFACEID,JTRACK,ETRACK,PTRACK,
     &               XSCO, YSCO, ZSCO,
     &               PTRACK*CXTRCK, PTRACK*CYTRCK, PTRACK*CZTRCK,
     &               CXTRCK, CYTRCK, CZTRCK,
     &               WTRACK, WSCRNG,
     &               ISPUSR(1),ISPUSR(2),
     &               SPAUSR(2),SPAUSR(3),SPAUSR(4),SPAUSR(5),
     &               pID)
        END IF
      
      RETURN

*======================================================================*
*                                                                      *
*     Event end dumping DRAWing                                        *
*                                                                      *
*======================================================================*

      ENTRY EEDRAW ( ICODE )
      RETURN
                                                                      
*======================================================================*
*                                                                      *
*     ENergy deposition DRAWing                                        *
*                                                                      *
*======================================================================*

      ENTRY ENDRAW ( ICODE, MREG, RULL, XSCO, YSCO, ZSCO )
      CALL GEOR2N (MREG, REGION, IERR)

      IF(REGION.eq."TARGET")THEN
            REGIONID = 1
            CALL depfill(NCASE,
     &                  REGIONID,ICODE,JTRACK,ETRACK,PTRACK,
     &                  XSCO, YSCO, ZSCO,
     &                  PTRACK*CXTRCK, PTRACK*CYTRCK, PTRACK*CZTRCK,
     &                  CXTRCK, CYTRCK, CZTRCK,
     &                  WTRACK, WSCRNG,
     &                  ISPUSR(1),ISPUSR(2),
     &                  SPAUSR(2),SPAUSR(3),SPAUSR(4),SPAUSR(5),
     &                  pID)
        END IF

      RETURN

*======================================================================*
*                                                                      *
*     SOurce particle DRAWing                                          *
*                                                                      *
*======================================================================*

      ENTRY SODRAW

      CALL sourcefill ( NCASE, ILOFLK(NPFLKA),
     &                  TKEFLK(NPFLKA), PMOFLK(NPFLKA),
     &                  XFLK(NPFLKA), YFLK(NPFLKA), ZFLK(NPFLKA),
     &                  TXFLK(NPFLKA), TYFLK(NPFLKA), TZFLK(NPFLKA),
     &                  WTFLK(NPFLKA)
     &                )

      RETURN

*======================================================================*
*                                                                      *
*     User defined DRAWing                                             *
*                                                                      *
*======================================================================*

      ENTRY USDRAW ( ICODE, MREG, XSCO, YSCO, ZSCO )

      SPAUSR(1) = ETRACK

      SPAUSR(2) = XSCO
      SPAUSR(3) = YSCO
      SPAUSR(4) = ZSCO

      ISPUSR(1) = JTRACK
      ISPUSR(2) = ICODE
      ISPUSR(3) = 1

      RETURN

      END

