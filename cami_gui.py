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
        self.master=master
        master.geometry("530x600")
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
        self.tau=StringVar(value='1')
        self.delay=StringVar(value='0')
        self.unit=StringVar()
        self.build_widgets()

    def build_widgets(self):
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
        Radiobutton(master,text="equal-sized divisions",variable=self.div_type,value=1).grid(row=7,column=1,sticky=W)
        Radiobutton(master,text="divisions with same number of points",variable=self.div_type,value=2).grid(row=8,column=1,columnspan=4,sticky=W)
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
        Label(master,text="").grid(row=17,column=0)
        Label(master,text="Transmission delay:").grid(row=18,column=0,sticky=W,padx=10)
        Entry(master,textvariable=self.delay,width=3).grid(row=18,column=1,sticky=W)
        Label(master,text="").grid(row=19,column=0)
        Label(master,text="Units:").grid(row=20,column=0,sticky=W,padx=10)
        self.unit_menu=OptionMenu(master,self.unit,optionlist[0],*optionlist)
        self.unit_menu.grid(row=20,column=1,sticky=W)
        Label(master,text="").grid(row=21,column=0)
        Button(master,text="Calculate",command=self.calc_cami).grid(row=22,column=1,columnspan=2)

    #function to load data
    def load_data(self,x_or_y):
        path=fd.askopenfilename(title='Load Data',filetypes=FILE_TYPES)
        if not path:
            return
        try:
            df=core.load_table(path)
        except Exception as error:
            showerror(title="Error", message=str(error))
            return
        self.files[x_or_y].set(path)
        self.data[x_or_y]=df
        self.pop_table(df,x_or_y)

    #function to create a new window
    def pop_table(self,df,x_or_y):
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
            self.series[x_or_y]=core.select_series(self.data[x_or_y],along,int(index),int(self.sel_start.get()))
        except Exception as error:
            showerror(title="Error",message=str(error))
            return False
        return True

    #function that calculates CaMI
    def calc_cami(self):
        try:
            if self.series['x'] is None or self.series['y'] is None:
                raise ValueError('Load the X and Y data first')
            x_divs,y_divs=None,None
            symb_type={1:'equal-divs',2:'equal-points'}.get(self.div_type.get(),'equal-divs')
            if self.div_type.get()==3:
                x_divs=core.parse_divisions(self.xdiv_vals.get())
                y_divs=core.parse_divisions(self.ydiv_vals.get())
            results=core.compute_measures(self.series['x'],self.series['y'],n_symbols=int(self.n_symbols.get()),
                                          symbolic_type=symb_type,x_divs=x_divs,y_divs=y_divs,
                                          lengths=(int(self.lxp.get()),int(self.lyp.get()),int(self.lyf.get())),
                                          tau=int(self.tau.get()),delay=int(self.delay.get()),units=self.unit.get())
        except Exception as error:
            showerror(title="Error",message="Error when calculating CaMI: "+str(error))
            return
        self.show_results(results)

    #display results in new window
    def show_results(self,results):
        mi,dir_idx=results['mutual_info'],results['directionality']
        cami_xy,cami_yx,te_xy,te_yx=results['cami_xy'],results['cami_yx'],results['te_xy'],results['te_yx']
        resWindow=Toplevel(self.master)
        resWindow.title("Results")
        resWindow.geometry("260x390")
        Label(resWindow,text="CaMI Results").grid(row=0,column=0,padx=10,pady=10)
        Label(resWindow,text="").grid(row=1,column=0)
        Label(resWindow,text="Mutual Information").grid(row=2,column=0,padx=10)
        Label(resWindow,text=f"{mi:10.4f}").grid(row=3,column=0,padx=10)
        Label(resWindow,text="").grid(row=4,column=0)
        Label(resWindow,text="Causal Mutual Information (CaMI)").grid(row=5,column=0,padx=10)
        Label(resWindow,text=f"X{ARROW} Y: {cami_xy:10.4f} \t Y{ARROW} X: {cami_yx:10.4f}").grid(row=6,column=0,padx=10)
        Label(resWindow,text="").grid(row=7,column=0)
        Label(resWindow,text="Transfer Entropy").grid(row=8,column=0,padx=10)
        Label(resWindow,text=f"X{ARROW} Y: {te_xy:10.4f} \t Y{ARROW} X: {te_yx:10.4f}").grid(row=9,column=0,padx=10)
        Label(resWindow,text="").grid(row=10,column=0)
        Label(resWindow,text=f"Directionality Index X{ARROW} Y").grid(row=11,column=0,padx=10)
        Label(resWindow,text=f"{dir_idx:10.4f}").grid(row=12,column=0,padx=10)
        Label(resWindow,text="").grid(row=13,column=0)
        Button(resWindow,text="OK",command=resWindow.destroy).grid(row=14,column=0,padx=10)


def main():
    master=Tk()
    CamiApp(master)
    master.mainloop()


if __name__=='__main__':
    main()
