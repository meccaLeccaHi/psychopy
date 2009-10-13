#!/usr/bin/env python

# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, psychopy
import StringIO
if sys.argv[-1] in ['-v', '--version']:
    print 'PsychoPy2, version %s (c)Jonathan Peirce, 2009, GNU GPL license' %psychopy.__version__
    sys.exit()
if sys.argv[-1] in ['-h', '--help']:
    print """Starts the PsychoPy2 application.

Usage:  python PsychoPy.py [options] [file]

Without options or files provided starts the psychopy using prefs to
decide on the view(s) to open.  If optional [file] is provided action
depends on the type of the [file]:

 Python script 'file.py' -- opens coder

 Experiment design 'file.psyexp' -- opens builder

Options:
    -c, --coder, coder       opens coder view only
    -b, --builder, builder   opens builder view only

    --version        prints version and exits
    -h, --help       prints this help and exit

"""
    sys.exit()

# Ensure 2.8 version of wx
if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.ensureMinimal('2.8')
import wx

import sys, os, threading, time, platform
from psychopy import preferences, configobj, configobjValidate
from psychopy.monitors import MonitorCenter
#other app subpackages needs to be imported as explicitly in app
from psychopy.app import coder, builder, wxIDs, connections

links={
    wxIDs.psychopyHome:"http://www.psychopy.org/",
    wxIDs.psychopyReference:"http://www.psychopy.org/reference",
    wxIDs.psychopyTutorial:"http://www.psychopy.org/home.php/Docs/Tutorials"
    }

class PsychoSplashScreen(wx.SplashScreen):
    """
    Create a splash screen widget.
    """
    def __init__(self, app):
        self.app=app
        splashFile = os.path.join(self.app.prefs.paths['resources'], 'psychopySplash.png')
        aBitmap = wx.Image(name = splashFile).ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.NO_BORDER
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle,
                                 0, None)
        #setup statusbar
        self.SetBackgroundColour('WHITE')
        self.status = wx.StaticText(self, -1, "Initialising PsychoPy and Libs",
                                    wx.Point(0,250),#splash image is 640x240
                                    wx.Size(520, 20), wx.ALIGN_LEFT|wx.ALIGN_TOP)
        self.status.SetMinSize(wx.Size(520,20))
        self.Fit()
        self.Close()

class MenuFrame(wx.Frame):
    """A simple, empty frame with a menubar that should be the last frame to close on a mac
    """
    def __init__(self, parent=None, ID=-1, app=None, title="PsychoPy2"):
        wx.Frame.__init__(self, parent, ID, title, size=(1,1))
        self.app=app

        self.menuBar = wx.MenuBar()

        self.viewMenu = wx.Menu()
        self.menuBar.Append(self.viewMenu, '&View')
        self.viewMenu.Append(self.app.IDs.openBuilderView, "&Open Builder view\t%s" %self.app.keys.switchToBuilder, "Open a new Builder view")
        wx.EVT_MENU(self, self.app.IDs.openBuilderView,  self.app.showBuilder)
        self.viewMenu.Append(self.app.IDs.openCoderView, "&Open Coder view\t%s" %self.app.keys.switchToCoder, "Open a new Coder view")
        wx.EVT_MENU(self, self.app.IDs.openCoderView,  self.app.showCoder)
        item=self.viewMenu.Append(wx.ID_EXIT, "&Quit\t%s" %self.app.keys.quit, "Terminate the program")
        self.Bind(wx.EVT_MENU, self.app.quit, item)

        self.SetMenuBar(self.menuBar)
        self.Show()

class PsychoPyApp(wx.App):
    def OnInit(self):
        self.version=psychopy.__version__
        self.SetAppName('PsychoPy2')
        #set default paths and import options
        self.prefs = preferences.Preferences() #from preferences.py
        self.keys = self.prefs.keys
        self.prefs.pageCurrent = 0  # track last-viewed page of prefs, to return there
        self.IDs=wxIDs
        self.quitting=False
        
        #on a mac, don't exit when the last frame is deleted, just show a menu
        if platform.system()=='Darwin':
            self.menuFrame=MenuFrame(parent=None, app=self)
        #get preferred view(s) from prefs and previous view
        if self.prefs.app['defaultView']=='last':
            mainFrame = self.prefs.appData['lastFrame']
        else:
            # configobjValidate should take care of this situation (?), but doesn't:
            if self.prefs.app['defaultView'] in ['last', 'coder', 'builder', 'both']:
                mainFrame = self.prefs.app['defaultView']
            else:
                self.prefs.app['defaultView'] = 'both'
                mainFrame = 'both'
        #then override the main frame by command options and passed files
        scripts=[]; exps=[]
        if len(sys.argv)>1:
            if sys.argv[1]==__name__:
                args = sys.argv[2:] # program was excecuted as "python.exe PsychoPyIDE.py %1'
            else:
                args = sys.argv[1:] # program was excecuted as "PsychoPyIDE.py %1'
            #choose which frame to start with
            if args[0] in ['builder', '--builder', '-b']:
                    mainFrame='builder'
                    args = args[1:]#can remove that argument
            elif args[0] in ['coder','--coder', '-c']:
                    mainFrame='coder'
                    args = args[1:]#can remove that argument
            #did we get .py or .psyexp files?
            elif args[0][-7:]=='.psyexp':
                    mainFrame='builder'
                    exps=[args[0]]
            elif args[0][-3:]=='.py':
                    mainFrame='coder'
                    scripts=[args[0]]
        else:
            args=[]

        #connections.checkForUpdates(app=self)

        self.dpi = int(wx.GetDisplaySize()[0]/float(wx.GetDisplaySizeMM()[0])*25.4)
        if not (50<self.dpi<120): self.dpi=80#dpi was unreasonable, make one up

        splash = PsychoSplashScreen(self)
        if splash:
            splash.Show()

        #create both frame for coder/builder as necess
        self.coder = self.builder = None
        if mainFrame in ['both', 'coder']: self.showCoder(fileList=scripts)
        if mainFrame in ['both', 'builder']: self.showBuilder(fileList=exps)

        #send anonymous info to www.psychopy.org/usage.php
        #please don't disable this - it's important for PsychoPy's development
        # on mac OS 10.6, I had no internet connection, and the app crashed (python crashed with a bus error)
        # try statsThread.start() except pass also crashed. so I added a check whether the proxy is ''
        if self.prefs.connections['allowUsageStats'] and self.prefs.connections['proxy'] <> '':
            statsThread = threading.Thread(target=connections.sendUsageStats, args=(self.prefs.connections['proxy'],))
            statsThread.start()
        
        """This is in wx demo. Probably useful one day.
        #---------------------------------------------
        def ShowTip(self):
            config = GetConfig()
            showTipText = config.Read("tips")
            if showTipText:
                showTip, index = eval(showTipText)
            else:
                showTip, index = (1, 0)

            if showTip:
                tp = wx.CreateFileTipProvider(opj("data/tips.txt"), index)
                ##tp = MyTP(0)
                showTip = wx.ShowTip(self, tp)
                index = tp.GetCurrentTip()
                config.Write("tips", str( (showTip, index) ))
                config.Flush()"""

        return True

    def showCoder(self, event=None, fileList=None):
        if self.coder==None:
            self.coder=coder.CoderFrame(None, -1,
                      title="PsychoPy2 Coder (IDE) (v%s)" %self.version,
                      files = fileList, app=self)
        self.coder.Show(True)
        self.SetTopWindow(self.coder)
        self.coder.Raise()
        self.coder.setOutputWindow()#takes control of sys.stdout
    def showBuilder(self, event=None, fileList=None):
        if self.builder==None:
            self.builder=builder.BuilderFrame(None, -1,
                                  title="PsychoPy2 Experiment Builder",
                                  files = fileList, app=self)
        self.builder.Show(True)
        self.builder.Raise()
        self.SetTopWindow(self.builder)
    def openMonitorCenter(self,event):
        frame = MonitorCenter.MainFrame(None,'PsychoPy2 Monitor Center')
        frame.Show(True)
    def MacOpenFile(self,fileName):
        if fileName.endswith('.py'):
            self.coder.setCurrentDoc(fileName)
        elif fileName.endswith('.psyexp'):
            self.builder.setCurrentDoc(fileName)
    def quit(self, event=None):
        self.quitting=True
        #see whether any files need saving
        for frame in [self.coder, self.builder]:
            if frame==None: continue
            ok=frame.checkSave()
            if not ok: return#user cancelled quit
        #save info about current frames for next run
        if self.coder and not self.builder:
            self.prefs.appData['lastFrame']='coder'
        elif self.builder and not self.coder:
            self.prefs.appData['lastFrame']='builder'
        else:
            self.prefs.appData['lastFrame']='both'
        #hide the frames then close
        for frame in [self.coder, self.builder]:
            if frame==None: continue
            frame.closeFrame(checkSave=False)#should update (but not save) prefs.appData
            self.prefs.saveAppData()#must do this before destroying the frame?
            frame.Destroy()#because closeFrame actually just Hides the frame
        if platform.system()=='Darwin':
            self.menuFrame.Destroy()
        sys.exit()#really force a quit
    def showPrefs(self, event):
        prefsDlg = PreferencesDlg(app=self)
        prefsDlg.Show()

    def showAbout(self, event):

        licFile = open(os.path.join(self.prefs.paths['psychopy'],'LICENSE.txt'))
        license = licFile.read()
        licFile.close()

        msg = """For stimulus generation and experimental control in python.

PsychoPy depends on your feedback. If something doesn't work then
let me/us know at psychopy-users@googlegroups.com"""
        info = wx.AboutDialogInfo()
        info.SetName('PsychoPy')
        info.SetVersion('v'+psychopy.__version__)
        info.SetDescription(msg)

        info.SetCopyright('(C) 2002-2009 Jonathan Peirce')
        info.SetWebSite('http://www.psychopy.org')
        info.SetLicence(license)
        info.AddDeveloper('Jonathan Peirce')
        info.AddDeveloper('Yaroslav Halchenko')
        info.AddDocWriter('Jonathan Peirce')

        wx.AboutBox(info)

    def followLink(self, event):
        wx.LaunchDefaultBrowser(links[event.GetId()])
        
        
class PreferencesDlg(wx.Frame):
    def __init__(self, parent=None, ID=-1, app=None, title="PsychoPy Preferences"):
        wx.Frame.__init__(self, parent, ID, title, size=(700,700))
        panel = wx.Panel(self)
        self.nb = wx.Notebook(panel)
        self.pageIDs={}#store the page numbers
        self.paths = app.prefs.paths
        self.app=app
        
        self.prefs={'user' : app.prefs.userPrefsCfg,
                    'site' : app.prefs.sitePrefsCfg,
                    'keys' : app.prefs.keysPrefsCfg,
                    'help' : app.prefs.helpPrefsCfg}
        self.prefPagesOrder = ['user', 'site', 'keys', 'help']
        
        for n, prefsType in enumerate(self.prefPagesOrder):
            sitePage = self.makePage(self.prefs[prefsType])
            self.nb.AddPage(sitePage,prefsType)
            self.pageIDs[prefsType]=n

        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        panel.SetSizer(sizer)

        self.menuBar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        item = self.fileMenu.Append(wx.ID_SAVE,   "&Save prefs\t%s" %app.keys.save)
        self.Bind(wx.EVT_MENU, self.save, item)
        item = self.fileMenu.Append(wx.ID_CLOSE,   "&Close prefs\t%s" %app.keys.close)
        self.Bind(wx.EVT_MENU, self.close, item)
        self.fileMenu.AppendSeparator()
        item = self.fileMenu.Append(wx.ID_EXIT, "&Quit\t%s" %app.keys.quit, "Terminate the application")
        self.Bind(wx.EVT_MENU, self.quit, item)

        self.menuBar.Append(self.fileMenu, "&File")
        self.SetMenuBar(self.menuBar)
        
        try:
            self.nb.ChangeSelection(app.prefs.pageCurrent)
        except:
            pass # the above can throw an error if prefs already open

    def makePage(self, prefs):
        page = wx.stc.StyledTextCtrl(parent=self.nb)

        # setup the style
        if sys.platform=='darwin':
            page.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:Courier New,size:10d")
        else:
            page.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:Courier,size:12d")
        page.StyleClearAll()  # Reset all to be like the default
        page.SetLexer(wx.stc.STC_LEX_PROPERTIES)
        page.StyleSetSpec(wx.stc.STC_PROPS_SECTION,"fore:#FF5555,bold")
        page.StyleSetSpec(wx.stc.STC_PROPS_COMMENT,"fore:#007F00")

        buff=StringIO.StringIO()
        prefs.write(buff)
        if sys.platform == 'darwin' and 'keybindings' in prefs.keys():
            # display Cmd+ instead of Ctrl+, because that's how the keys will work
            page.SetText(buff.getvalue().replace('Ctrl+','Cmd+'))
        else:
            page.SetText(buff.getvalue())
        buff.close()

        # check that the folder exists
        dirname = os.path.dirname(prefs.filename)
        if not os.path.isdir(dirname):
            try: os.makedirs(dirname)
            except: 
                page.SetReadOnly(True)
        # make the text read-only?
        try:
            if prefs.filename.find("prefsHelp.cfg") > -1: raise Exception()  # read-only if a protected page, like prefsHelp.cfg
            f = open(prefs.filename, 'a')  # read-only if write-access fails; this test did not work for me: os.access(dirname,os.W_OK)
            f.close()
        except:  # make the textctrl read-only, and comment color blue
            if prefs.filename.find("prefsUser.cfg") < 0:  # user prefs should always be editable
                page.SetReadOnly(True)
                page.StyleSetSpec(wx.stc.STC_PROPS_COMMENT,"fore:#0033BB")
        return page
    
    def close(self, event=None):
        app.prefs.pageCurrent = self.nb.GetSelection()
        self.checkForUnsaved()        
        self.Destroy()
        
    def quit(self, event=None):
        self.checkForUnsaved()        
        self.close()
        self.app.quit()
        
    def checkForUnsaved(self, event=None):
        pageCurrent = self.nb.GetSelection()
        # better: copied from coder line 1232+; example of how to call: coder line 1444
        #for ii in range(self.notebook.GetPageCount()):
        #    doc = self.nb.GetPage(ii)
        #    filename=doc.filename
        #    if doc.UNSAVED:
        #        dlg = dialogs.MessageDialog(self,message='Save changes to %s before quitting?' %filename, type='Warning')
        #        resp = dlg.ShowModal()
        #        sys.stdout.flush()
        #        dlg.Destroy()
        #        if resp  == wx.ID_CANCEL: return 0 #return, don't quit
        #        elif resp == wx.ID_YES: self.save() #save then quit
        #        elif resp == wx.ID_NO: pass #don't save just quit        
 
        if app.prefs.prefsCfg['app']['autoSavePrefs']:
            for prefsType in self.prefs.keys():
                if self.isChanged(prefsType):
                   print "auto-",
                   break
            self.save()
        app.prefs.pageCurrent = pageCurrent
        
    def save(self, event=None):
        # user changes are to two separate cfg's; merge to set values to actually use now 
        prefsSpec = configobj.ConfigObj(os.path.join(self.paths['prefs'], 'prefsSite.spec'), encoding='UTF8', list_values=False)
        app.prefs.prefsCfg = configobj.ConfigObj(app.prefs.sitePrefsCfg, configspec=prefsSpec)
        app.prefs.prefsCfg.merge(app.prefs.userPrefsCfg)

        pageCurrent = self.nb.GetSelection()
        for prefsType in self.prefs.keys():
            pageText = self.getPageText(prefsType)
            filePath = self.paths['%sPrefsFile' % prefsType]
            if self.isChanged(prefsType):
                try:
                    f = open(filePath, 'w')
                    f.write(pageText)
                    f.close()
                    print "saved", filePath
                except:
                    pass
        # reload / refresh:
        self.app.prefs = preferences.Preferences()  # validation happens in here
        self.app.keys = self.app.prefs.keys
        
        self.nb.ChangeSelection(pageCurrent)
        return 1  # ok
    
    def getPageText(self,prefsType):
        """Get the prefs text for a given page
        """
        self.nb.ChangeSelection(self.pageIDs[prefsType])
        return self.nb.GetCurrentPage().GetText().encode('utf-8')
    def isChanged(self,prefsType='site'):
        filePath = self.paths['%sPrefsFile' %prefsType]
        if not os.path.isfile(filePath):
            return True
        f = open(filePath, 'r')  # 'r+' fails if the file does not have write permission
        savedTxt = f.read()
        f.close()
        #find the notebook page
        currTxt = self.getPageText(prefsType)
        return (currTxt!=savedTxt)

if __name__=='__main__':
    app = PsychoPyApp(0)
    app.MainLoop()
