import tkinter, tkinter.filedialog
import os, os.path, sys
import re
import glob

pkgdir = os.path.dirname(__file__ )
d = os.path.abspath(os.path.join(pkgdir, "src"))
if d not in sys.path:
    sys.path.append(os.path.join(d))

import tof_rawto012

default_dir=os.path.abspath(os.path.join(pkgdir, "..", "tests", "COPDD", "in"))
home_dir=os.path.join(os.path.expanduser("~"))

class StdoutRedirector(object):
    '''A class for redirecting stdout to this Text widget.'''
    def __init__(self, text_area):
        object.__init__(self)
        self.text_area = text_area

    def write(self,s):
        self.text_area.insert(tkinter.constants.INSERT, s, "a")
        self.text_area.yview(tkinter.constants.END)

class StderrRedirector(object):
    '''A class for redirecting stdout to this Text widget.'''
    NTAGS = 0
    def __init__(self, text_area):
        object.__init__(self)
        self.text_area = text_area

    def write(self,s):
        textcolor="red"
        self.text_area.insert(tkinter.constants.INSERT, s, "a")
        end_index = self.text_area.index("end")
        begin_index = "%s-%sc" % (end_index, len(s) + 1)
        tag = str(ActrisConverterGui.NTAGS)
        self.text_area.tag_add(tag, begin_index, end_index)
        self.text_area.tag_config(tag, foreground=textcolor)
        ActrisConverterGui.NTAGS += 1
        self.text_area.yview(tkinter.constants.END)

class ActrisConverterGui(tkinter.Frame):

    # rendering stuff
    NTAGS = 0
    WIDTH=100

    def __init__(self, root):
        tkinter.Frame.__init__(self, root)
        self.root = root

        self.instr_type = tkinter.StringVar()
        f0 = tkinter.LabelFrame(root, text="Instrument type", pady=5)
        r0 = tkinter.Radiobutton(f0, text="ToF-ACSM", variable=self.instr_type, value="ToF-ACSM")
        r0.pack(side=tkinter.constants.LEFT, padx=5)
        r1 = tkinter.Radiobutton(f0, text="Q-ACSM", variable=self.instr_type, value="Q-ACSM")
        r1.pack(side=tkinter.constants.LEFT, padx=5)
        f0.pack(fill=tkinter.constants.BOTH, expand=1)
        self.instr_type.set("ToF-ACSM")
        
        # Input File frame
        self.infiles = tkinter.StringVar()
        f1 = tkinter.LabelFrame(root, text="Input files", pady=5)
        e1 = tkinter.Entry(f1, textvariable=self.infiles, width=ActrisConverterGui.WIDTH)
        e1.bind("<Return>", lambda e:self.check_infiles())
        e1.pack(side=tkinter.constants.LEFT, padx=5, fill=tkinter.constants.BOTH, expand=1)
        tkinter.Button(f1, text="Browse", command=self.askopeninfiles).pack(side=tkinter.constants.RIGHT, padx=5)
        f1.pack(fill=tkinter.constants.BOTH, expand=1)
        _infiles = glob.glob(os.path.join(default_dir, "*.txt"))
        self.infiles.set(" ".join(_infiles))

        # Input flags File frame
        self.infile_qa = tkinter.StringVar()
        f3 = tkinter.LabelFrame(root, text="Flags file", pady=5)
        e3 = tkinter.Entry(f3, textvariable=self.infile_qa, width=ActrisConverterGui.WIDTH)
        e3.bind("<Return>", lambda e:self.check_infile_qa())
        e3.pack(side=tkinter.constants.LEFT, padx=5, fill=tkinter.constants.BOTH, expand=1)
        tkinter.Button(f3, text="Browse", command=self.askopeninfile_qa).pack(side=tkinter.constants.RIGHT, padx=5)
        f3.pack(fill=tkinter.constants.BOTH, expand=1)
        _infileqa = glob.glob(os.path.join(default_dir, "*.csv"))[0]
        self.infile_qa.set(_infileqa)

        # Output Directory frame
        self.outdir = tkinter.StringVar()
        f2 = tkinter.LabelFrame(root, text="Output Directory", pady=5)
        e2 = tkinter.Entry(f2, textvariable=self.outdir, width=ActrisConverterGui.WIDTH)
        e2.bind("<Return>", lambda e:self.check_outdir())
        e2.pack(side=tkinter.constants.LEFT, padx=5, fill=tkinter.constants.BOTH, expand=1)
        tkinter.Button(f2, text="Browse", command=self.askdirectory).pack(side=tkinter.constants.RIGHT, padx=5)
        f2.pack(fill=tkinter.constants.BOTH, expand=1)
        self.outdir.set(home_dir)

        # Convert button
        self.b1 = tkinter.Button(root, text="Generate", command=self.process, state=tkinter.constants.DISABLED)
        self.b1.pack(side=tkinter.constants.TOP, padx=5)

        # log text frame
        self.log = tkinter.Text(root)
        scroll=tkinter.Scrollbar(root, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tkinter.constants.RIGHT, fill=tkinter.constants.Y)
        self.log.pack(side=tkinter.constants.BOTTOM, fill=tkinter.constants.BOTH, expand=1)
        
        self.set_process_state()

    def set_process_state(self):
        """
        check if all inputs are set for running the process
        """
        if len(self.infiles.get()) and len(self.infile_qa.get()) and len(self.outdir.get()):
            self.b1.configure(state=tkinter.constants.ACTIVE)
        else:
            self.b1.configure(state=tkinter.constants.DISABLED)

    def askopeninfiles(self):
        """
        Returns a filename
        """
        # get filename
        opts = {
            "filetypes" : [("All files", "*"), ("text files", ".txt")],
            "initialdir" : default_dir,
            "parent" : self.root,
            "title" : "Input files",
            "multiple" : True,
        }
        infiles = tkinter.filedialog.askopenfilename(**opts)
        if infiles:
            self.infiles.set(infiles)
            self.check_infiles()
            self.set_process_state()

    def askopeninfile_qa(self):
        """
        Returns a filename
        """
        # get filename
        opts = {
            "filetypes" : [("All files", "*"), ("text files", ".txt")],
            "initialdir" : default_dir,
            "parent" : self.root,
            "title" : "Input file",
            "multiple" : False,

        }
        infile_qa = tkinter.filedialog.askopenfilename(**opts)
        if infile_qa:
            self.infile_qa.set(infile_qa)
            self.check_infile_qa()
            self.set_process_state()

    def askdirectory(self):
        """
        Returns a selected directoryname
        """
        opts = {
            "initialdir" : home_dir,
            "mustexist" : True,
            "parent" : self.root,
            "title" : "Output directory",
        }
        outdir = tkinter.filedialog.askdirectory(**opts)
        if outdir:
            self.outdir.set(outdir)
            self.check_outdir()
            self.set_process_state()

    def check_outdir(self):
        """
        @brief check validity of output directory
        """
        outdir = self.outdir.get()
        if not os.path.exists(outdir):
            self.add_log_text("Unexisting output directory \"" + outdir + "\"" + os.linesep, "red")
            self.outdir.set("")

    def check_infiles(self):
        """
        @brief check validity of input file
        """
        # check if filename match a supported input product pattern
        infiles = self.infiles.get()
        self.set_process_state()

    def check_infile_qa(self):
        """
        @brief check validity of input file
        """
        # check if filename match a supported input product pattern
        infile_qa = self.infile_qa.get()
        self.set_process_state()

    def add_log_text(self, s, textcolor="black"):
        """
        @brief add a text in the log frame
        """
        self.log.insert(tkinter.constants.INSERT, s, "a")
        end_index = self.log.index("end")
        begin_index = "%s-%sc" % (end_index, len(s) + 1)
        tag = str(ActrisConverterGui.NTAGS)
        self.log.tag_add(tag, begin_index, end_index)
        self.log.tag_config(tag, foreground=textcolor)
        ActrisConverterGui.NTAGS += 1
        self.log.yview(tkinter.constants.END)

    def process(self):
        """
        run process it self
        """
        sys.stdout = StdoutRedirector(self.log)
        sys.stderr = StderrRedirector(self.log)
        self.add_log_text("> Instrument:  " + self.instr_type.get() + os.linesep, "blue")
        self.add_log_text("> Input files: " + self.infiles.get() + os.linesep, "blue")
        self.add_log_text("> Flag files:  " + self.infile_qa.get() + os.linesep, "blue")
        self.add_log_text("> Out. dir.:   " + self.outdir.get() + os.linesep, "blue")
        self.add_log_text("Start processing... " + os.linesep, "blue")
        
        converter = None
        if self.instr_type.get() == "ToF-ACSM":
            converter = tof_rawto012.Application()
        else:
            raise ValueError("Unsupported instrument type " + self.self.instr_type.get())

        _infiles = self.infiles.get()
        if isinstance(_infiles, str) :
            _infiles = _infiles.strip()
            if _infiles.startswith("("):
                # is a tuple
                _infiles = eval(_infiles)
                _infiles = [os.path.normpath(v.strip()) for v in _infiles]
            else:
                _infiles = [os.path.normpath(v.strip()) for v in _infiles.split(" ")]

        _infile_qa = os.path.normpath(self.infile_qa.get())
        _outdir = os.path.normpath(self.outdir.get())

        converter.process(_infiles, _infile_qa, _outdir)
        self.add_log_text("...done" + os.linesep, "blue")


if __name__=="__main__":
    root = tkinter.Tk()
    ActrisConverterGui(root).pack()
    root.mainloop()
