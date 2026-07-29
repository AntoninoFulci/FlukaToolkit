*                                                                      *
*=== mgdraw ===========================================================*
*                                                                      *
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

      CHARACTER*8 INREG
      CHARACTER*8 OUTREG
      CHARACTER*8 REGNAME
*
*----------------------------------------------------------------------*
*                                                                      *
*     Icode = 1: call from Kaskad                                      *
*     Icode = 2: call from Emfsco                                      *
*     Icode = 3: call from Kasneu                                      *
*     Icode = 4: call from Kashea                                      *
*     Icode = 5: call from Kasoph                                      *
*                                                                      *
*----------------------------------------------------------------------*
*
* *** user code here ***
      RETURN
*
*======================================================================*
*                                                                      *
*     Boundary-(X)crossing DRAWing:                                    *
*                                                                      *
*======================================================================*
*
      ENTRY BXDRAW ( ICODE, MREG, NEWREG, XSCO, YSCO, ZSCO )
      
      ! Get region names
      CALL GEOR2N (MREG, INREG, IERR)
      CALL GEOR2N (NEWREG, OUTREG, IERR)

      IF(JTRACK.eq.1) THEN
      IF((INREG.eq."VOID").and.(OUTREG.eq."TARGET")) THEN      
            
       CALL treefill (NCASE,
     &               1,JTRACK,ETRACK,PTRACK,
     &               XSCO, YSCO, ZSCO,
     &               CXTRCK, CYTRCK, CZTRCK,
     &               WTRACK, WSCRNG,
     &               ISPUSR(1),ISPUSR(2),
     &               SPAUSR(1),SPAUSR(2),SPAUSR(3),SPAUSR(4),
     &               pID)
      
      END IF
      END IF

      RETURN
*
*======================================================================*
*                                                                      *
*     Event End DRAWing:                                               *
*                                                                      *
*======================================================================*
*
      ENTRY EEDRAW ( ICODE )
* *** user code here ***
      RETURN
*
*======================================================================*
*                                                                      *
*     ENergy deposition DRAWing:                                       *
*                                                                      *
*======================================================================*
*
      ENTRY ENDRAW ( ICODE, MREG, RULL, XSCO, YSCO, ZSCO )
* *** user code here ***
      RETURN
*
*======================================================================*
*                                                                      *
*     SOurce particle DRAWing:                                         *
*                                                                      *
*======================================================================*
*
      ENTRY SODRAW
* *** user code here ***
      RETURN
*
*======================================================================*
*                                                                      *
*     USer dependent DRAWing:                                         *
*                                                                      *
*======================================================================*
*
      ENTRY USDRAW ( ICODE, MREG, XSCO, YSCO, ZSCO )
* *** user code here ***
      RETURN
*=== End of subroutine Mgdraw =========================================*
      END
