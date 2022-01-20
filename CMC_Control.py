###############################################################################
#   CMEngine connector
###############################################################################
import helper as h
import win32com.client

class CMEngine():
    def __init__(self):   
        h.log("scan for CMC-Devices")
        self.device_locked = False
        self.cm_engine = win32com.client.Dispatch("OMICRON.CMEngAL")
        self.ana = {"v": [[0, 0, 0],      #Amplitude
                         [0, -120, 120],  #Phase
                         [50, 50, 50]],   #Frequency
                    "i": [[0, 0, 0],      #Amplitude
                         [0, -120, 120],  #Phase
                         [50, 50, 50]]    #Frequency
                    }    
        if str(self.cm_engine.DevScanForNew(False)) == "None":
            h.log_error("No CMC devices found!")
            return
        else:
            device_list = self.cm_engine.DevGetList(0)  #return all associated CMCs
            h.log("Devices found: " + str(int(len(device_list)/4)))
            self.device_id = int(device_list[0])        #first associated CMC is used - make sure only one is associated

            self.cm_engine.DevUnlock(self.device_id)
            self.cm_engine.DevLock(self.device_id)
            self.device_locked = True
            #device information
            device_list = device_list.split(",")
            h.log("ID :  "+device_list[0])
            h.log("SER:  "+device_list[1])
            h.log("Type: "+self.cm_engine.DeviceType(self.device_id))
            h.log("IP:   "+self.cm_engine.IPAddress(self.device_id))
            h.log("--------------------------")

    def set_command(self, info_object):
        ioa_1 = info_object.address._1
        ioa_2 = info_object.address._2
        ioa_3 = info_object.address._3
        info_detail_typ = info_object.dataObject[0].name  #SCO / R32
        
        if info_object.address.DEZ == 1 and info_detail_typ == "SCO":
            self.power(info_object.dataObject[0].detail[2].state)
        if ioa_1 == 1 and ioa_2 in range(1,7) and ioa_3 in range (1,4) and info_detail_typ == "R32":
            value = info_object.dataObject[0].detail[0].value
            self.prepare_output(ioa_1, ioa_2, ioa_3, value)
        if ioa_1 == 99:
            self.reset_output()

        #set power:
        #IOA1           | IOA2       | IOA3            | value
        # 1             | 0          | 0               | SCS_ON / SCS_OFF
        #set output:
        #IOA1-Generator | IOA2-Phase | IOA3-parameter  | value
        # 1             | 1: UL1     | 1: Amplitude    | R32
        #               | 2: UL2     | 2: Phase        | R32
        #               | 3: UL3     | 3: Frequency    | R32
        #               | 4: IL1     |                 | R32
        #               | 5: IL2     |                 | R32 
        #               | 6: IL3     |                 | R32 
        # 99            | 0          | 0               | reset_output 

    def cmd(self, cmd):
        h.log("CMC Command: " + cmd)
        if self.device_locked:
            self.cm_engine.Exec(self.devId,cmd)
        else:
            h.log_error("No CMC connected!")

    def power(self, command):
        if command == "SCS_ON":
            self.cmd("out:on")
        else:  
            self.cmd("out:off")
            self.cmd("out:ana:off(zcross)")
            
    def reset_output(self):
        for _phase in range(0,2):
            for _parameter in range(0,2):
                self.ana["v"][_parameter][_phase] = 0
                self.ana["i"][_parameter][_phase] = 0
        self.ana["v"][1][1] = -120
        self.ana["i"][1][1] = -120
        self.ana["v"][1][2] = 120
        self.ana["i"][1][2] = 120
        for i in range(0,2):
            self.ana["v"][2][i] = 50
            self.ana["i"][2][i] = 50
        self.set_output()
               
    def prepare_output(self, generator, phase, parameter, value):
        u_max = 150
        i_max = 5
        f_min = 40
        f_max = 60
        
        triple = "v" if phase in range(0,4) else "i"
        ui_phase = phase if triple == "v" else phase - 3
        
        max_value = value
        if triple == "v" and parameter == 1 and value >= u_max:
            max_value = u_max
            h.log_error("U > Umax! --> set {}V".format(u_max))
        if triple == "i" and parameter == 1 and value >= i_max:
            max_value = i_max
            h.log_error("I > Imax! --> set {}A".format(i_max))
            
        if parameter == 3 and value not in range(f_min,f_max):
            max_value = 50
            h.log_error("f <> fmin/max! --> set {}Hz".format(50))
            
        
        self.ana[triple][parameter-1][ui_phase-1] = max_value
        self.set_output(generator, "v")
        self.set_output(generator, "i")

    def set_output(self, generator, vi):
        for phase in range(0,3):
            cmd = "out:{}({}:{}):a({:3.3f});p({:3.3f});f({:3.3f})" \
                                    .format(vi, generator, phase+1, 
                                            self.ana[vi][0][phase],
                                            self.ana[vi][1][phase],
                                            self.ana[vi][2][phase])
            self.cmd(cmd)
                
        #"out:v(1:1):a(10);p(0);f(50)"               
        """
        self.ana = {"v": [[0, 0, 0],     #Amplitude
                         [0, -120, 120], #Phase
                         [50, 50, 50]],  #Frequency
                    "i": [[0, 0, 0],     #Amplitude
                         [0, -120, 120], #Phase
                         [50, 50, 50]]   #Frequency
                    }    
        """ 

#--- Start up -----------------------------------------------------------------
def start():
    h.log (__name__+ " start")

#--- update  ------------------------------------------------------------------
def handle():
    h.log (__name__ + "handle")



