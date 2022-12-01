class PrimaryMirrorControlInterface:
        
    def TipRelative(self,steps):
        print('Tip Relative: ' + str(steps))
        
    def TiltRelative(self,steps):
        print('Tilt Relative: ' + str(steps))
        
    def FocusRelative(self,steps):
        print('Focus Relative: ' + str(steps))
        
    def Connect(self):
        print('Connecting')
        
    def HomeAll(self):
        print('Homing')