#! /usr/bin/env python

import wx
from wx.adv import AnimationCtrl


class Animate(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, -1, title)
        self.animation = AnimationCtrl(self)
        self.animation.LoadFile('ajax-bar-loader.gif')
        self.animation.Play()
        self.Show()


app = wx.App()
frame = Animate(None, -1, 'Animation')
app.MainLoop()
