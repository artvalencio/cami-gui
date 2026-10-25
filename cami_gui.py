from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo, showerror
import numpy as np
import pandas as pd
from cami import cami, mutual_info
from PIL import ImageTk, Image
import os

FILE_TYPES = (('All readable types',('*.csv','*.xlsx','*.xls','*.dta','*.xport','*.sas7bdat','*.sav','*.npy','*.json','*.sql','*.h5')),
              ('Comma-separated values','*.csv'),
              ('Excel file',('*.xlsx','*.xls')),
              ('Stata file','*.dta'),
              ('SAS file',('*.xport','*.sas7bdat')),
              ('SPSS file','*.sav'),
              ('Numpy array','*.npy'),
              ('JavaScript Object Notation (JSON)','*.json'),
              ('Hierarchical Data Format (HDF5)','*.h5'))


class CamiApp:
    '''Main window of the CaMI graphical user interface.'''

    def __init__(self, master):
        self.master=master
        master.geometry("530x600")
        master.title("CaMI")
        #data and file names
        self.files={'x':StringVar(value=""),'y':StringVar(value="")}
        self.data={'x':[],'y':[]}
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
        self.img = ImageTk.PhotoImage(Image.open("cami_ico.gif"))
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
        OptionMenu(master,self.unit,*optionlist).grid(row=20,column=1,sticky=W)
        Label(master,text="").grid(row=21,column=0)
        Button(master,text="Calculate",command=self.calc_cami).grid(row=22,column=1,columnspan=2)

    #function to load data
    def load_data(self,x_or_y):
        fname=self.files[x_or_y]
        fname.set(fd.askopenfilename(title='Load Data',filetypes=FILE_TYPES))
        errorcode=0
        if fname.get()[-3:]=='csv':
            df=pd.read_csv(fname.get(),header=None)
        elif (fname.get()[-3:]=='xls') or (fname.get()[-4:]=='xlsx'):
            df=pd.read_excel(fname.get(),header=None)
        elif fname.get()[-3:]=='dta':
            df=pd.read_stata(fname.get())
        elif (fname.get()[-5:]=='xport') or (fname.get()[-8:]=='sas7bdat'):
            df=pd.read_sas(fname.get())
        elif fname.get()[-3:]=='sav':
            df=pd.read_spss(fname.get())
        elif fname.get()[-3:]=='npy':
            df=pd.DataFrame(np.load(fname.get()))
        elif fname.get()[-4:]=='json':
            df=pd.read_json(fname.get())
        elif fname.get()[-2:]=='h5':
            df=pd.read_hdf(fname.get())
        else:
            showinfo(title="Error", message="No data given or data type not supported")
            errorcode=1
        if errorcode==0:
            self.data[x_or_y]=df
            self.pop_table(df,x_or_y)

    #function to create a new window
    def pop_table(self,df,x_or_y):
        newWindow=Toplevel(self.master)
        newWindow.title("Select data")
        newWindow.geometry("650x430")
        #build table
        if df.index[-1]>=50:
            rows=tuple(range(1,51))
        else:
            rows=tuple(range(1,df.index[-1]))
        cols=["Rows"]
        if len(df.columns)>=9:
            for i in range(1,11):
                cols.append(str(i))
        else:
            for i in range(1,len(df.columns)+1):
                cols.append(str(i))
        tree=Treeview(newWindow,columns=cols,show='headings')
        for i in cols:
            tree.heading(i,text=i)
            tree.column(i, minwidth=0, width=60, stretch=NO)
        for n in rows:
            to_add=[n]
            for i in cols:
                if i!="Rows":
                    to_add.append(df.iat[n-1,int(i)-1])
            tree.insert('',END,values=to_add)
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
        def process_data():
            df=self.data[x_or_y]
            if self.row_or_column==1:
                self.data[x_or_y]=df.transpose[int(self.sel_start.get())-1:][int(self.sel_data_row.get())-1]
            else:
                self.data[x_or_y]=df[int(self.sel_start.get())-1:][int(self.sel_data_column.get())-1]
            newWindow.destroy()
        Button(newWindow,text="OK",command=process_data).grid(row=7,column=2)

    #function that calculates CaMI
    def calc_cami(self):
        x_df,y_df=self.data['x'],self.data['y']
        if self.div_type.get()==1:
            symb_type='equal-divs'
            x_divs,y_divs=None,None
        elif self.div_type.get()==2:
            symb_type='equal-points'
            x_divs,y_divs=None,None
        elif self.div_type.get()==3:
            symb_type='equal-divs' #wont be used, but needed to avoid error
            x_divs=[float(i) for i in self.xdiv_vals.get().split(sep=',')]
            y_divs=[float(i) for i in self.ydiv_vals.get().split(sep=',')]
        try:
            cami_xy,cami_yx=cami(x_df.values,y_df.values,symbolic_type=symb_type,n_symbols=int(self.n_symbols.get()),
                                 symbolic_length=(int(self.lxp.get()),int(self.lyp.get()),int(self.lyf.get())),
                                 x_divs=x_divs,y_divs=y_divs,delay=int(self.delay.get()),units=self.unit.get(),tau=int(self.tau.get()),
                                 two_sided=True)
            mi=mutual_info(x_df.values,y_df.values,symbolic_type=symb_type,n_symbols=int(self.n_symbols.get()),
                                 symbolic_length=(int(self.lxp.get()),int(self.lyp.get())),x_divs=x_divs,y_divs=y_divs,tau=int(self.tau.get()),
                                 delay=int(self.delay.get()),units=self.unit.get())
            te_xy=cami_xy-mi
            te_yx=cami_yx-mi
            dir_idx=cami_xy-cami_yx
            self.show_results(mi,cami_xy,cami_yx,te_xy,te_yx,dir_idx)
        except:
            showerror(title="Error",message="Error when calculating CaMI.\n Usual cause is diferent lengths between time-series, please check. \n X length: "+str(len(x_df))+"\n Y length: "+str(len(x_df)))

    #display results in new window
    def show_results(self,mi,cami_xy,cami_yx,te_xy,te_yx,dir_idx):
        resWindow=Toplevel(self.master)
        resWindow.title("Results")
        resWindow.geometry("260x390")
        Label(resWindow,text="CaMI Results").grid(row=0,column=0,padx=10,pady=10)
        Label(resWindow,text="").grid(row=1,column=0)
        Label(resWindow,text="Mutual Information").grid(row=2,column=0,padx=10)
        Label(resWindow,text=f"{mi:10.4f}").grid(row=3,column=0,padx=10)
        Label(resWindow,text="").grid(row=4,column=0)
        Label(resWindow,text="Causal Mutual Information (CaMI)").grid(row=5,column=0,padx=10)
        Label(resWindow,text=f"X→ Y: {cami_xy:10.4f} \t Y→ X: {cami_yx:10.4f}").grid(row=6,column=0,padx=10)
        Label(resWindow,text="").grid(row=7,column=0)
        Label(resWindow,text="Transfer Entropy").grid(row=8,column=0,padx=10)
        Label(resWindow,text=f"X→ Y: {te_xy:10.4f} \t Y→ X: {te_yx:10.4f}").grid(row=9,column=0,padx=10)
        Label(resWindow,text="").grid(row=10,column=0)
        Label(resWindow,text="Directionality Index X→ Y").grid(row=11,column=0,padx=10)
        Label(resWindow,text=f"{dir_idx:10.4f}").grid(row=12,column=0,padx=10)
        Label(resWindow,text="").grid(row=13,column=0)
        Button(resWindow,text="OK",command=resWindow.destroy).grid(row=14,column=0,padx=10)


def main():
    master=Tk()
    CamiApp(master)
    master.mainloop()


if __name__=='__main__':
    main()
