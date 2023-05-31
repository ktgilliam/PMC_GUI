from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty
import numpy as np

from tec_iface import *
BoxAIface = TecControllerInterface()
BoxBIface = TecControllerInterface()

tmp_num_tecs = 132
NUM_BOXES = 2
#NUM_BOXES = 1
NUM_BOARDS = 5

class ControllerRequest(IntEnum):
    NO_REQUESTS = 0
    TOGGLE_CONNECTION_A=1
    TOGGLE_CONNECTION_B=2
    ALL_TO_ZERO=3
    LOAD_FROM_FILE=4
    
class ControllerState(IntEnum):
    INIT=0
    DISCONNECTED=1
    CONNECT_IN_PROGRESS = 2
    CONNECTED=3
    
class TECField(GridLayout):
    tec_no = NumericProperty()
    def __init__(self, tec_no, **kwargs): 
        super().__init__(**kwargs)
        self.tec_no = tec_no
class TECFieldHeader(GridLayout):
    pass
class TECFieldList(GridLayout):
    num_tec = NumericProperty()
    
    def __init__(self, **kwargs): 
        super(TECFieldList, self).__init__(**kwargs)
        self.num_tec = tmp_num_tecs
        # layout = self.ids['fields']
        # for ii in range(self.num_tec):
        #     tf = TECField(ii+1)
        #     layout.add_widget(tf)
            
    def createFields(self):
        self.height = self.num_tec * 50 / self.cols
        for ii in range(self.num_tec):
            tf = TECField(tec_no=ii+1, width = (self.parent.width-50)/self.cols)
            self.add_widget(tf)
            
class TECControlWidget(GridLayout):
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        
    def loadList(self):
        list = self.ids['tec_field_list']
        list.createFields()
        a = 5        
            
class TECController():
    
    ControllerRequestList = deque([])
    
    def __init__(self, ctrlWidget, nursery, debugMode = False, **kwargs): 
        self.nursery = nursery
        self.controllerWidget = ctrlWidget
        self.debugMode = debugMode
    
    def get_tec_data(logdata=False,fname='tec'):
        pass
        # Get the data by box, board, and channel.  It's more efficient
    #     start = time.time();
    #     if(logdata):
    #         print("I should log data now")
    # #        fname = fname+time.strftime("%Y%m%d%H%M%S")+'.pkl'
    # #        print(fname)
    #         pfile = open(fname,'ab')
    #     for box in range(NUM_BOXES):
    #         for board in range(NUM_BOARDS):
    #             data = objTec.getTecByBoxBoard(box+1,board);
    #             pwrs = objTec.parseTecMessage(data);     # This is the parsed tec powers
    #             # now get the tec numbers for the box and board
    # ##            pwrs = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]  # Dummy values while not connected to TECs
    #             boxIndex = np.squeeze(np.where(cc.BOXMAP[:,1] == box+1));
    #             boardIndex = np.squeeze(np.where(cc.BOXMAP[boxIndex,2] == board));
    #             tecs = cc.BOXMAP[boxIndex[boardIndex],0]  # this is the list of the tec numbers, now populate the corresponding edit boxes
    #             # this routine will get the data into the GUI label
    #             ii = 0;
    #             for tec in tecs:
    #                 if (Ivalues):
    #                     tec_widgets[tec-1].metrics[0].value_str = f'{round((float(pwrs[ii+1])/100.0*8.11-1.32),2)}'
    #                 else:
    #                     tec_widgets[tec-1].metrics[0].value_str = f'{pwrs[ii+1]}'
    #                 tec_widgets[tec-1].metrics[0].update(tec_widgets[tec-1].metrics[0])
    # ##                tec_widgets[tec-1].metrics[0].new.setText(f'{pwrs[ii+1]}')
    #                 ii += 1;
    #                 if(logdata and tec==teclog):
    # #                    numdata = 2+2*len(tempchans)
    # #                    data = np.zeros((num_data,1))
    #                     tecdat = []
    #                     data = []
    #                     tecdat.append(teclog)
    #                     tecdat.append(f'{pwrs[ii]}')
    # #                    data[0] = teclog
    # #                    data[1] = f'{pwrs[ii]}'
    #                     data.append( float(''.join(tecdat)) )
    #                     pickle.dump(data,pfile)
    #                     pfile.close()
    async def updateControls(self):
        """Main state machine for handling events in the app
        """
        self.connectionFailedEvent = trio.Event()
        # while 1:
        #     currentState = await self.getControllerState()
        #     if currentState == ControllerState.INIT:
        #         await self.initStateHandler()
        #     elif currentState == ControllerState.DISCONNECTED:
        #         await self.disconnectedStateHandler()
        #     elif currentState == ControllerState.CONNECT_IN_PROGRESS:
        #         if self.debugMode:
        #             await trio.sleep(0)
        #             ttfIface._connected = True #overriding the pmc connection flag (bad)
        #             await self.terminalManager.addMessage('Connecting... (debug mode so not really)')
        #             await self.connectionSucceededHandler()
        #             # await trio.sleep(0)
        #         else:
        #             await self.connectInProgressStateHandler()
        #             if self.connectionFailedEvent.is_set():
        #                 await self.resetConnection()
        #             else:
        #                 await self.connectionSucceededHandler()
        #     elif currentState == ControllerState.CONNECTED:
        #         await self.connectedStateHandler()                
        #     self.controllerWidget.updateOutputFields()
        #     await trio.sleep(0)