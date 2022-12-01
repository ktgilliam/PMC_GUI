class PrimaryMirrorControlInterface:
    _isHomed = False
    def TipRelative(self,steps):
        print('Tip Relative: ' + str(steps))
        
    def TiltRelative(self,steps):
        print('Tilt Relative: ' + str(steps))
        
    def FocusRelative(self,steps):
        print('Focus Relative: ' + str(steps))
        
    def TipAbsolute(self,steps):
        print('Tip Absolute: ' + str(steps))
        
    def TiltAbsolute(self,steps):
        print('Tilt Absolute: ' + str(steps))
        
    def FocusAbsolute(self,steps):
        print('Focus Absolute: ' + str(steps))
        
    def Connect(self):
        print('Connecting')
        return True
    
    def Disonnect(self):
        print('Disconnecting')
    
    def HomeAll(self):
        self._isHomed = True
        print('Homing')
        
    def isHomed(self):
        return self._isHomed