'''CaMI GUI: a Tk window to compute mutual information, Causal Mutual Information,
transfer entropy and the directionality index of two time-series with cami-python.

Run with:  python cami_gui.py

The window (CamiApp) only gathers input and shows results; loading files,
selecting series and computing the measures happen in cami_gui_core, which is
independent of Tk and tested on its own. Significance tests (surrogate data)
can take seconds, so they run in a background Job while the window polls its
progress.
'''
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog as fd
from tkinter.messagebox import showerror
import os

import cami_gui_core as core
from cami_gui_core import FILE_TYPES
from PIL import ImageTk, Image

HERE = os.path.dirname(os.path.abspath(__file__))
ARROW = chr(0x2192)


class CamiApp:
    '''Main window of the CaMI graphical user interface.'''

    def __init__(self, master):
        '''Creates the window's variables and widgets inside the Tk root `master`.'''
        self.master=master
        master.title("CaMI")
        #data and file names
        self.files={'x':StringVar(value=""),'y':StringVar(value="")}
        self.data={'x':None,'y':None}    #tables as loaded
        self.series={'x':None,'y':None}  #selected time-series
        #data selection (set in the table window)
        self.row_or_column=IntVar(value=2)
        self.sel_data_row=StringVar(value='1')
        self.sel_data_column=StringVar(value='1')
        self.sel_start=StringVar(value='1')
        #items for CaMI calculation
        self.n_symbols=StringVar(value='2')
        self.div_type=IntVar(value=1)
        self.xdiv_vals=StringVar(value='0.5')
        self.ydiv_vals=StringVar(value='0.5')
        self.lxp=StringVar(value='1')
        self.lyp=StringVar(value='1')
        self.lyf=StringVar(value='1')
        self.symbolic_type=StringVar(value=core.SYMBOLIC_TYPES[0])
        self.tau=StringVar(value='1')
        self.auto_tau=BooleanVar(value=False)
        self.delay=StringVar(value='0')
        self.unit=StringVar()
        self.significance=BooleanVar(value=False)
        self.n_surrogates=StringVar(value='99')
        self.last_results=None
        self.job=None              #background calculation (with significance tests)
        self.progress_window=None
        self.build_widgets()

    def build_widgets(self):
        '''Lays out the main window: data loading, encoding, symbolic lengths, tau,
        delay, units, significance and the Calculate button (grid rows top to bottom).'''
        master=self.master
        #setting main window widgets
        self.img = ImageTk.PhotoImage(Image.open(os.path.join(HERE,"cami_ico.gif")))
        Label(master,image=self.img).grid(row=0,column=0, rowspan=4,sticky=W,padx=10,pady=10)
        Button(master,text='Load first variable data (X)',command=lambda: self.load_data('x')).grid(row=0,column=1,columnspan=4,sticky=W,pady=(10,0))
        Label(master,textvariable=self.files['x']).grid(row=1,column=1,columnspan=4,sticky=W)
        Button(master,text='Load second variable data (Y)',command=lambda: self.load_data('y')).grid(row=2,column=1,columnspan=4,sticky=W)
        Label(master,textvariable=self.files['y']).grid(row=3,column=1,columnspan=4,sticky=W)
        optionlist=['bits','nat','ban']
        Label(master,text="").grid(row=4,column=0,padx=10)
        Label(master,text="Number of symbols:").grid(row=5,column=0,sticky=W,padx=10)
        Entry(master,textvariable=self.n_symbols,width=3).grid(row=5,column=1,sticky=W)
        Label(master,text="").grid(row=6,column=0,padx=10)
        Label(master,text="Partition divisions:").grid(row=7,column=0,sticky=W,padx=10)
        Radiobutton(master,text="automatic:",variable=self.div_type,value=1).grid(row=7,column=1,sticky=W)
        Combobox(master,textvariable=self.symbolic_type,values=core.SYMBOLIC_TYPES,state='readonly',width=22).grid(row=7,column=2,columnspan=3,sticky=W)
        Radiobutton(master,text="other (separate with commas):",variable=self.div_type,value=3).grid(row=9,column=1,sticky=W)
        Label(master,text=" X divisions:").grid(row=9,column=2,sticky=W)
        Entry(master,textvariable=self.xdiv_vals,width=10).grid(row=9,column=3,sticky=W)
        Label(master,text=" Y divisions:").grid(row=10,column=2,sticky=W)
        Entry(master,textvariable=self.ydiv_vals,width=10).grid(row=10,column=3,sticky=W)
        Label(master,text="").grid(row=11,column=0)
        Label(master,text="Symbolic length:").grid(row=12,column=0,sticky=W,padx=10)
        Label(master,text="Past of X:").grid(row=12,column=1,sticky=W)
        Entry(master,textvariable=self.lxp,width=3).grid(row=12,column=2,sticky=W)
        Label(master,text="Past of Y:").grid(row=13,column=1,sticky=W)
        Entry(master,textvariable=self.lyp,width=3).grid(row=13,column=2,sticky=W)
        Label(master,text="Future of Y:").grid(row=14,column=1,sticky=W)
        Entry(master,textvariable=self.lyf,width=3).grid(row=14,column=2,sticky=W)
        Label(master,text="").grid(row=15,column=0)
        Label(master,text="Tau:").grid(row=16,column=0,sticky=W,padx=10)
        Entry(master,textvariable=self.tau,width=3).grid(row=16,column=1,sticky=W)
        Checkbutton(master,text="automatic (first zero of autocorrelation)",variable=self.auto_tau).grid(row=16,column=2,columnspan=3,sticky=W)
        Label(master,text="").grid(row=17,column=0)
        Label(master,text="Transmission delay:").grid(row=18,column=0,sticky=W,padx=10)
        Entry(master,textvariable=self.delay,width=3).grid(row=18,column=1,sticky=W)
        Label(master,text="").grid(row=19,column=0)
        Label(master,text="Units:").grid(row=20,column=0,sticky=W,padx=10)
        self.unit_menu=OptionMenu(master,self.unit,optionlist[0],*optionlist)
        self.unit_menu.grid(row=20,column=1,sticky=W)
        Label(master,text="").grid(row=21,column=0)
        Label(master,text="Significance:").grid(row=22,column=0,sticky=W,padx=10)
        Checkbutton(master,text="surrogate test with",variable=self.significance).grid(row=22,column=1,sticky=W)
        Entry(master,textvariable=self.n_surrogates,width=5).grid(row=22,column=2,sticky=W)
        Label(master,text="surrogates").grid(row=22,column=3,sticky=W)
        Label(master,text="").grid(row=23,column=0)
        Button(master,text="Calculate",command=self.calc_cami).grid(row=24,column=1,columnspan=2)

    #function to load data
    def load_data(self,x_or_y):
        '''Asks for a data file for X or Y, keeps a preview of its first rows and opens
        the table window where the row/column holding the series is chosen.'''
        path=fd.askopenfilename(title='Load Data',filetypes=FILE_TYPES)
        if not path:
            return
        try:
            df=core.preview_table(path)  #only the first rows; the chosen series is read later
        except Exception as error:
            showerror(title="Error", message=str(error))
            return
        self.files[x_or_y].set(path)
        self.data[x_or_y]=df
        self.pop_table(df,x_or_y)

    #function to create a new window
    def pop_table(self,df,x_or_y):
        '''Shows the preview of a loaded table and asks where the series is (row or
        column, and the first numeric entry); OK reads that series from the file.'''
        newWindow=Toplevel(self.master)
        newWindow.title("Select data")
        newWindow.geometry("650x430")
        #build table
        cols,rows=core.preview(df)
        tree=Treeview(newWindow,columns=cols,show='headings')
        for i in cols:
            tree.heading(i,text=i)
            tree.column(i, minwidth=0, width=60, stretch=NO)
        for row in rows:
            tree.insert('',END,values=row)
        yscrollbar=Scrollbar(newWindow,orient=VERTICAL,command=tree.yview)
        tree.configure(yscroll=yscrollbar.set)
        tree.grid(row=0,column=0,columnspan=5,sticky='nsew',padx=(10,0),pady=10)
        yscrollbar.grid(row=0,column=5,sticky='ns',pady=10)
        Label(newWindow,text="").grid(row=1,column=0,sticky=W)
        #ask where data is
        Label(newWindow,text="The data runs along: ").grid(row=2,column=0,sticky=W,padx=10)
        Radiobutton(newWindow,text="column ",variable=self.row_or_column,value=2).grid(row=2,column=1,sticky=W)
        Entry(newWindow,textvariable=self.sel_data_column,width=3).grid(row=2,column=2,sticky=W)
        Radiobutton(newWindow,text="row ",variable=self.row_or_column,value=1).grid(row=3,column=1,sticky=W)
        Entry(newWindow,textvariable=self.sel_data_row,width=3).grid(row=3,column=2,sticky=W)
        Label(newWindow,text="").grid(row=4,column=0,sticky=W)
        #ask where values start
        Label(newWindow,text="The numerical values start at row/column: ").grid(row=5,column=0,columnspan=2,sticky=W,padx=10)
        Entry(newWindow,textvariable=self.sel_start,width=3).grid(row=5,column=2,sticky=W)
        Label(newWindow,text="").grid(row=6,column=0,sticky=W)
        #update data after OK button is pressed
        def ok():
            if self.apply_selection(x_or_y):
                newWindow.destroy()
        Button(newWindow,text="OK",command=ok).grid(row=7,column=2)

    def apply_selection(self,x_or_y):
        '''Stores the row/column chosen in the table window as the series of X or Y.'''
        try:
            if self.row_or_column.get()==1:
                along,index='row',self.sel_data_row.get()
            else:
                along,index='column',self.sel_data_column.get()
            self.series[x_or_y]=core.load_series(self.files[x_or_y].get(),along,int(index),int(self.sel_start.get()))
        except Exception as error:
            showerror(title="Error",message=str(error))
            return False
        return True

    #function that calculates CaMI
    def calc_cami(self):
        '''Reads the parameters and computes the measures: right away without
        significance tests, or in a background Job (with a progress window) with them.'''
        if self.job is not None:
            return  #a calculation is already running
        try:
            if self.series['x'] is None or self.series['y'] is None:
                raise ValueError('Load the X and Y data first')
            x_divs,y_divs=None,None
            if self.div_type.get()==3:
                x_divs=core.parse_divisions(self.xdiv_vals.get())
                y_divs=core.parse_divisions(self.ydiv_vals.get())
            n_surrogates=int(self.n_surrogates.get()) if self.significance.get() else 0
            params=dict(n_symbols=int(self.n_symbols.get()),symbolic_type=self.symbolic_type.get(),
                        x_divs=x_divs,y_divs=y_divs,
                        lengths=(int(self.lxp.get()),int(self.lyp.get()),int(self.lyf.get())),
                        tau=None if self.auto_tau.get() else int(self.tau.get()),
                        delay=int(self.delay.get()),units=self.unit.get(),n_surrogates=n_surrogates)
            if not n_surrogates:  #fast: computed right away
                results=core.compute_measures(self.series['x'],self.series['y'],**params)
        except Exception as error:
            showerror(title="Error",message="Error when calculating CaMI: "+str(error))
            return
        if n_surrogates:  #significance tests run in the background
            self.job=core.Job(core.compute_measures,self.series['x'],self.series['y'],**params)
            self.open_progress_window()
            self.master.after(100,self.poll_job)
            return
        self.last_results=results
        self.show_results(results)

    def open_progress_window(self):
        '''Small window with a progress bar and a Cancel button for the background job.'''
        window=self.progress_window=Toplevel(self.master)
        window.title("Calculating")
        Label(window,text="Significance tests (surrogate data)").grid(row=0,column=0,padx=10,pady=(10,5))
        self.progress_bar=Progressbar(window,length=260,mode='determinate',maximum=1)
        self.progress_bar.grid(row=1,column=0,padx=10)
        Button(window,text="Cancel",command=self.cancel_job).grid(row=2,column=0,pady=10)
        window.protocol("WM_DELETE_WINDOW",self.cancel_job)

    def cancel_job(self):
        '''Asks the background job to stop (it stops at its next progress report).'''
        if self.job is not None:
            self.job.cancel()

    def poll_job(self):
        '''Updates the progress bar; shows the results (or error) when the job ends.'''
        #Tk is not thread-safe: the worker never touches widgets; this method runs on the
        #GUI thread every 100 ms (master.after) and does all the updates
        job=self.job
        if job is None:
            return
        if not job.finished:
            if job.total:
                self.progress_bar.configure(maximum=job.total,value=job.done)
            self.master.after(100,self.poll_job)
            return
        self.job=None
        if self.progress_window is not None:
            self.progress_window.destroy()
            self.progress_window=None
        if isinstance(job.error,core.Cancelled):
            return
        if job.error is not None:
            showerror(title="Error",message="Error when calculating CaMI: "+str(job.error))
            return
        self.last_results=job.result
        self.show_results(job.result)

    #save the last results to a CSV file
    def export_results(self):
        '''Saves the last results (and p-values, if computed) to a CSV file.'''
        if self.last_results is None:
            showerror(title="Error",message="Calculate the measures first")
            return
        path=fd.asksaveasfilename(title='Export results',defaultextension='.csv',filetypes=(('Comma-separated values','*.csv'),))
        if path:
            core.export_results(self.last_results,path)

    #display results in new window
    def show_results(self,results):
        '''Opens the results window (with p-values when significance tests were run).'''
        p_values=results.get('p_values')

        def fmt(name):
            text=f"{results[name]:10.4f}"
            if p_values:
                text+=f" (p = {p_values[name]:.3f})"
            return text

        resWindow=Toplevel(self.master)
        resWindow.title("Results")
        Label(resWindow,text="CaMI Results").grid(row=0,column=0,padx=10,pady=10)
        Label(resWindow,text="").grid(row=1,column=0)
        Label(resWindow,text="Mutual Information").grid(row=2,column=0,padx=10)
        Label(resWindow,text=fmt('mutual_info')).grid(row=3,column=0,padx=10)
        Label(resWindow,text="").grid(row=4,column=0)
        Label(resWindow,text="Causal Mutual Information (CaMI)").grid(row=5,column=0,padx=10)
        Label(resWindow,text=f"X{ARROW} Y: {fmt('cami_xy')}").grid(row=6,column=0,padx=10)
        Label(resWindow,text=f"Y{ARROW} X: {fmt('cami_yx')}").grid(row=7,column=0,padx=10)
        Label(resWindow,text="").grid(row=8,column=0)
        Label(resWindow,text="Transfer Entropy").grid(row=9,column=0,padx=10)
        Label(resWindow,text=f"X{ARROW} Y: {fmt('te_xy')}").grid(row=10,column=0,padx=10)
        Label(resWindow,text=f"Y{ARROW} X: {fmt('te_yx')}").grid(row=11,column=0,padx=10)
        Label(resWindow,text="").grid(row=12,column=0)
        Label(resWindow,text=f"Directionality Index X{ARROW} Y").grid(row=13,column=0,padx=10)
        Label(resWindow,text=f"{results['directionality']:10.4f}").grid(row=14,column=0,padx=10)
        Label(resWindow,text="").grid(row=15,column=0)
        Button(resWindow,text="Export CSV",command=self.export_results).grid(row=16,column=0,padx=10)
        Button(resWindow,text="OK",command=resWindow.destroy).grid(row=17,column=0,padx=10,pady=(5,10))
        return resWindow


def main():
    '''Starts the GUI.'''
    master=Tk()
    CamiApp(master)
    master.mainloop()


if __name__=='__main__':
    main()
