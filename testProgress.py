import wx
import wx.adv


class MyPanel(wx.Panel):

    def __init__(self, parent, id):

        wx.Panel.__init__(self, parent, id)
        self.SetBackgroundColour("black")
        gif_fname = "Spinner_Green_Dots.gif"
        animation = wx.adv.Animation(gif_fname)
        gif = wx.adv.AnimationCtrl(self, -1, animation)

        gif.Play()


app = wx.App()
frame = wx.Frame(None, -1, "wx.animate.GIFAnimationCtrl()", size=(200, 220))
MyPanel(frame, -1)
frame.Show(True)
app.MainLoop()
