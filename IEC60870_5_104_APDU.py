###############################################################################
#   IMPORT
###############################################################################
import helper as h
import IEC60870_5_104_dict as d

###############################################################################
#   IEC60870-5-104 I-Frame
###############################################################################
#<APDU>------------------------------------
class APDU():
    def __init__(self, frame):
        self.APCI =  APCI(frame)
        self.ASDU =  ASDU(frame)
    def pO(self):
        print ("")
        print ("=<APDU>================================================================================")
        self.APCI.pO()
        self.ASDU.pO()
        
#----<APCI>------------------------------------
class APCI():
    def __init__(self, frame):
        self.start =  frame[0]
        self.length = frame[1]
        self.CF =     CF(frame)
    def pO(self):
        print ("  -<APCI>------------------------------------------------------------------------------")
        print ("  # - 8765 4321 - 0x   -  DEZ - Information")
        print ("  .....................................................................................")
        print ("  1 - " + h.fPL(self.start) + " - start")
        print ("  2 - " + h.fPL(self.length) + " - APDU lenght")
        print ("  3 - .... ...0 - 0x00 -    0 - Format = I")

class CF():
    def __init__(self, frame):
        self._1 =  frame[2]
        self._2 =  frame[3]
        self._3 =  frame[4]
        self._4 =  frame[5]
        self.Tx  = (frame[3]<<8 | frame[2])>>1
        self.Rx  = (frame[5]<<8 | frame[4])>>1
    def pO(self):
        print ("  3 - " + h.fPL(self.CF._1) + " - CF1")
        print ("  4 - " + h.fPL(self.CF._2) + " - CF2")
        print ("  5 - " + h.fPL(self.CF._3) + " - CF3")
        print ("  6 - " + h.fPL(self.CF._4) + " - CF4")
        print ("                         {0:4} - Tx count".format(self.Tx))
        print ("                         {0:4} - Rx count".format(self.Rx))
    
#----<ASDU>------------------------------------
class ASDU():
    def __init__(self, frame):
        self.TI =         TI(frame)
        self.SQ =         frame[7]>>7
        self.NofObjects = frame[7] & 0b01111111
        self.Test =       frame[8]>>7
        self.PN =         (frame[8] & 0b01000000)>>6
        self.COT =        COT(frame)
        self.ORG =        frame[9]
        self.CASDU =      CASDU(frame)
        self.InfoObject = InfoObject(frame)
    def pO(self):
        print ("  -<ASDU>------------------------------------------------------------------------------")
        print ("  # - 8765 4321 - 0x   -  DEZ - Information")
        print ("  .....................................................................................")
        self.TI.pO()
        print ("      ---------------------------------------------------------------------------------")
        print ("  8 - {0}... .... - 0x{0:02X} - {0:4} - SQ (Structure Qualifier)".format(self.SQ))
        print ("  8 - .{0:03b} {1:04b} - 0x{2:02X} - {2:4} - Number of objects".format(self.NofObjects>>4, self.NofObjects&0b00001111, self.NofObjects))
        print ("  9 - {0}... .... - 0x{0:02X} - {0:4} - T (Test)".format(self.Test))
        print ("  9 - .{0}.. .... - 0x{0:02X} - {0:4} - P/N (positive/negative)".format(self.PN))
        self.COT.pO()
        print (" 10 - " + h.fPL(self.ORG) + " - Originator Address (ORG)")
        print ("      ---------------------------------------------------------------------------------")
        self.CASDU.pO()
        self.InfoObject.pO()
        print ("=======================================================================================")
        print ("")
         
class TI():
    def __init__(self, frame):
        self.Typ =   frame[6]
        self.ref =   d.ti[self.Typ]["ref"]
        self.des =   d.ti[self.Typ]["des"]
    def pO(self):
        print ("  7 - " + h.fPL(self.Typ) + " - Type Identifier")
        print ("                                " + self.ref)
        print ("                                " + self.des)

class COT():
    def __init__(self, frame):
        self.DEZ   = frame[8] & 0b00111111
        self.long  = d.cot[self.DEZ]["long"]
        self.short = d.cot[self.DEZ]["short"]
    def pO(self):
        print ("  9 - ..{0:02b} {1:04b} - 0x{2:02X} - {2:4} - Cause of transmission (COT)".format(self.DEZ>>4, self.DEZ&0b00001111, self.DEZ))
        print ("                                " + self.long + " - " + self.short)

class CASDU():
    def __init__(self, frame):
        self.DEZ =   frame[11]<<8 | frame[10]
        self._1  =   frame[10]
        self._2  =   frame[11]
    def pO(self):
        print (" 11 - " + h.fPL(self._1) + " - CASDU1 (LSB) Address Field (Common Address of ASDU)")
        print (" 12 - " + h.fPL(self._2) + " - CASDU2 (MSB) Address Field (Common Address of ASDU)")
        addr ="{:6,d}".format(self.DEZ)
        addr = addr.replace(",",".")
        print ("                       "+ addr +" - CASDU Address Field (Common Address of ASDU)")

class InfoObject():
    def __init__(self, frame):
        self.address = Address(frame)
        type = frame[6]
        elements = []  #all InfoObjectElements
        self.data = [] #data details
        try:
            self.loadListOK = False
            elements = d.infoObjects[type]                   
            for i in range(len(elements)):                     
                self.data.append(Typ(elements[i]))  
            self.loadListOK = True
        except BaseException as ex:
            h.logEx(ex, "infoObject")
        
    def pO(self):
        print ("    -<InfoObject>----------------------------------------------------------------------")
        self.address.pO()
        if self.loadListOK:
            print ("    ---<InfoObjectData>----------------------------------------------------------------")
            for i in range(len(self.data)):
                print("        {} - {}".format(self.data[i].typ, self.data[i].typLong))
                for j in range(len(self.data[i].detail)):
                    print("          - {}".format(self.data[i].detail[j]))
        else:
            print("    ERROR - Information Object not in list")

class Typ():
    def __init__(self, data):
        self.typ = data[0][0]
        self.typLong = data[0][1]
        detailList = data[1]
        self.detail = []
        
        for i in range(len(detailList)):
            self.detail.append(detailList[i]["name"])

class Address():
    def __init__(self, frame):
        self.DEZ =   frame[14]<<16 | frame[13]<<8 | frame[12]
        self._1 =    frame[12]
        self._2 =    frame[13]
        self._3 =    frame[14]  
    def pO(self):
        print ("    ---<InfoObjectAddress>-------------------------------------------------------------")
        print (" 13 - " + h.fPL(self._1) + " - Information Object Address (IOA) (LSB)")
        print (" 14 - " + h.fPL(self._2) + " - Information Object Address (IOA) (...)")
        print (" 15 - " + h.fPL(self._3) + " - Information Object Address (IOA) (MSB)")
        addr ="{:10,d}".format(self.DEZ)
        addr = addr.replace(",",".")
        print ("                   "+ addr + " - Information Object Address (IOA)")
   
