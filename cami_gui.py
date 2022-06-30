from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo, showerror
import numpy as np
import pandas as pd
from cami import *
from PIL import ImageTk, Image
import os

#create main window
master=Tk()
master.geometry("530x600")
master.title("CaMI")
#create global vars
xfile=StringVar()
xfile.set("")
yfile=StringVar()
yfile.set("")
x_df=[]
y_df=[]
row_or_column=IntVar()
row_or_column.set(2)
sel_data_row=StringVar()
sel_data_row.set('1')
sel_data_column=StringVar()
sel_data_column.set('1')
sel_start=StringVar()
sel_start.set('1')

#functions to load data
def loadXData():
    types=(('All readable types',('*.csv','*.xlsx','*.xls','*.dta','*.xport','*.sas7bdat','*.sav','*.npy','*.json','*.sql','*.h5')),
           ('Comma-separated values','*.csv'),
           ('Excel file',('*.xlsx','*.xls')),
           ('Stata file','*.dta'),
           ('SAS file',('*.xport','*.sas7bdat')),
           ('SPSS file','*.sav'),
           ('Numpy array','*.npy'),
           ('JavaScript Object Notation (JSON)','*.json'),
           ('Hierarchical Data Format (HDF5)','*.h5'))
    xfile.set(fd.askopenfilename(title='Load Data',filetypes=types))
    global x_df
    errorcode=0
    if xfile.get()[-3:]=='csv':
        x_df=pd.read_csv(xfile.get(),header=None)
    elif (xfile.get()[-3:]=='xls') or (xfile.get()[-4:]=='xlsx'):
        x_df=pd.read_excel(xfile.get(),header=None)
    elif xfile.get()[-3:]=='dta':
        x_df=pd.read_stata(xfile.get())
    elif (xfile.get()[-5:]=='xport') or (xfile.get()[-8:]=='sas7bdat'):
        x_df=pd.read_sas(xfile.get())
    elif xfile.get()[-3:]=='sav':
        x_df=pd.read_spss(xfile.get())
    elif xfile.get()[-3:]=='npy':
        a=np.load(xfile.get())
        x_df=pd.DataFrame(a)
    elif xfile.get()[-4:]=='json':
        x_df=pd.read_json(xfile.get())
    elif xfile.get()[-2:]=='h5':
        x_df=pd.read_hdf(xfile.get())
    else:
        showinfo(title="Error", message="No data given or data type not supported")
        errorcode=1
    if errorcode==0:
        popTable(x_df,'x')
    
        
def loadYData():
    types=(('All readable types',('*.csv','*.xlsx','*.xls','*.dta','*.xport','*.sas7bdat','*.sav','*.npy','*.json','*.sql','*.h5')),
           ('Comma-separated values','*.csv'),
           ('Excel file',('*.xlsx','*.xls')),
           ('Stata file','*.dta'),           
           ('SAS file',('*.xport','*.sas7bdat')),
           ('SPSS file','*.sav'),
           ('Numpy array','*.npy'),
           ('JavaScript Object Notation (JSON)','*.json'),
           ('Structured Query Language (SQL)','*.sql'),
           ('Hierarchical Data Format (HDF5)','*.h5'))
    yfile.set(fd.askopenfilename(title='Load Data',filetypes=types))
    global y_df
    errorcode=0
    if yfile.get()[-3:]=='csv':
        y_df=pd.read_csv(yfile.get(),header=None)
    elif (yfile.get()[-3:]=='xls') or (yfile.get()[-4:]=='xlsx'):
        y_df=pd.read_excel(yfile.get(),header=None)        
    elif yfile.get()[-3:]=='dta':
        y_df=pd.read_stata(yfile.get())
    elif (yfile.get()[-5:]=='xport') or (yfile.get()[-8:]=='sas7bdat'):
        y_df=pd.read_sas(yfile.get())
    elif yfile.get()[-3:]=='sav':
        y_df=pd.read_spss(yfile.get())
    elif yfile.get()[-3:]=='npy':
        a=np.load(yfile.get())
        y_df=pd.DataFrame(a)
    elif yfile.get()[-4:]=='json':
        y_df=pd.read_json(yfile.get())
    elif yfile.get()[-2:]=='h5':
        y_df=pd.read_hdf(yfile.get())
    else:
        showinfo(title="Error", message="No data given or data type not supported")
        errorcode=1
    if errorcode==0:
        popTable(y_df,'y')

#function to create a new window
def popTable(df,x_or_y):
    newWindow=Toplevel(master)
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
    table=[]
    for n in rows:
        to_add=[n]
        for i in cols:
            if i!="Rows":
                to_add.append(df.iat[n-1,int(i)-1])
        table.append(to_add)
    for n in table:
        tree.insert('',END,values=n)
    yscrollbar=Scrollbar(newWindow,orient=VERTICAL,command=tree.yview)
    tree.configure(yscroll=yscrollbar.set)
    tree.grid(row=0,column=0,columnspan=5,sticky='nsew',padx=(10,0),pady=10)
    yscrollbar.grid(row=0,column=5,sticky='ns',pady=10)
    Label(newWindow,text="").grid(row=1,column=0,sticky=W)
    #ask where data is
    Label(newWindow,text="The data runs along: ").grid(row=2,column=0,sticky=W,padx=10)
    Radiobutton(newWindow,text="column ",variable=row_or_column,value=2).grid(row=2,column=1,sticky=W)
    Entry(newWindow,textvariable=sel_data_column,width=3).grid(row=2,column=2,sticky=W)
    Radiobutton(newWindow,text="row ",variable=row_or_column,value=1).grid(row=3,column=1,sticky=W)
    Entry(newWindow,textvariable=sel_data_row,width=3).grid(row=3,column=2,sticky=W)
    Label(newWindow,text="").grid(row=4,column=0,sticky=W)
    #ask where values start 
    Label(newWindow,text="The numerical values start at row/column: ").grid(row=5,column=0,columnspan=2,sticky=W,padx=10)
    Entry(newWindow,textvariable=sel_start,width=3).grid(row=5,column=2,sticky=W)
    Label(newWindow,text="").grid(row=6,column=0,sticky=W)
    #functions to update data after OK button is pressed
    def processXdata():
        global x_df
        if row_or_column==1:
            x_df=x_df.transpose[int(sel_start.get())-1:][int(sel_data_row.get())-1]
        else:
            x_df=x_df[int(sel_start.get())-1:][int(sel_data_column.get())-1]
        newWindow.destroy()
    def processYdata():
        global y_df
        if row_or_column==1:
            y_df=y_df.transpose[int(sel_start.get())-1:][int(sel_data_row.get())-1]
        else:
            y_df=y_df[int(sel_start.get())-1:][int(sel_data_column.get())-1]
        newWindow.destroy()
    #OK button: update data
    if x_or_y=='x':
        Button(newWindow,text="OK",command=processXdata).grid(row=7,column=2)
    elif x_or_y=='y':
        Button(newWindow,text="OK",command=processYdata).grid(row=7,column=2)

#function that calculates CaMI
def calcCami():
    #Cami calculation
    if div_type.get()==1:
        symb_type='equal-divs'
        x_divs,y_divs=None,None
    elif div_type.get()==2:
        symb_type='equal-points'
        x_divs,y_divs=None,None
    elif div_type.get()==3:
        symb_type='equal-divs' #wont be used, but needed to avoid error
        x_divs=[float(i) for i in xdiv_vals.get().split(sep=',')]
        y_divs=[float(i) for i in ydiv_vals.get().split(sep=',')]

    try:
        cami_xy,cami_yx=cami(x_df.values,y_df.values,symbolic_type=symb_type,n_symbols=int(ns.get()),
                             symbolic_length=(int(lxp.get()),int(lyp.get()),int(lyf.get())),
                             x_divs=x_divs,y_divs=y_divs,delay=int(delay.get()),units=unit.get(),tau=int(tau.get()),
                             two_sided=True)
        mi=mutual_info(x_df.values,y_df.values,symbolic_type=symb_type,n_symbols=int(ns.get()),
                             symbolic_length=(int(lxp.get()),int(lyp.get())),x_divs=x_divs,y_divs=y_divs,tau=int(tau.get()),
                             delay=int(delay.get()),units=unit.get())
        
        te_xy=cami_xy-mi
        te_yx=cami_yx-mi
        dir_idx=cami_xy-cami_yx
        #Display results in new window
        resWindow=Toplevel(master)
        resWindow.title("Results")
        resWindow.geometry("260x390")
        Label(resWindow,text="CaMI Results").grid(row=0,column=0,padx=10,pady=10)
        Label(resWindow,text="").grid(row=1,column=0)
        Label(resWindow,text="Mutual Information").grid(row=2,column=0,padx=10)
        Label(resWindow,text=f"{mi:10.4f}").grid(row=3,column=0,padx=10)
        Label(resWindow,text="").grid(row=4,column=0)
        Label(resWindow,text="Causal Mutual Information (CaMI)").grid(row=5,column=0,padx=10)
        Label(resWindow,text=f"X\u2192 Y: {cami_xy:10.4f} \t Y\u2192 X: {cami_yx:10.4f}").grid(row=6,column=0,padx=10)
        Label(resWindow,text="").grid(row=7,column=0)
        Label(resWindow,text="Transfer Entropy").grid(row=8,column=0,padx=10)
        Label(resWindow,text=f"X\u2192 Y: {te_xy:10.4f} \t Y\u2192 X: {te_yx:10.4f}").grid(row=9,column=0,padx=10)
        Label(resWindow,text="").grid(row=10,column=0)
        Label(resWindow,text="Directionality Index X\u2192 Y").grid(row=11,column=0,padx=10)
        Label(resWindow,text=f"{dir_idx:10.4f}").grid(row=12,column=0,padx=10)
        Label(resWindow,text="").grid(row=13,column=0)
        Button(resWindow,text="OK",command=resWindow.destroy).grid(row=14,column=0,padx=10)
    except:
        showerror(title="Error",message="Error when calculating CaMI.\n Usual cause is diferent lengths between time-series, please check. \n X length: "+str(len(x_df))+"\n Y length: "+str(len(x_df)))  

#setting main window widgets
img = ImageTk.PhotoImage(Image.open("cami_ico.gif"))
label=Label(master,image=img)
x_loadbtn=Button(master,text='Load first variable data (X)',command=loadXData)
labelx=Label(master,textvariable=xfile)
y_loadbtn=Button(master,text='Load second variable data (Y)',command=loadYData)
labely=Label(master,textvariable=yfile)

#positioning main window widgets
label.grid(row=0,column=0, rowspan=4,sticky=W,padx=10,pady=10)
x_loadbtn.grid(row=0,column=1,columnspan=4,sticky=W,pady=(10,0))
labelx.grid(row=1,column=1,columnspan=4,sticky=W)
y_loadbtn.grid(row=2,column=1,columnspan=4,sticky=W)
labely.grid(row=3,column=1,columnspan=4,sticky=W)

#items for CaMI calculation
ns=StringVar()
ns.set('2')
div_type=IntVar()
div_type.set(1)
xdiv_vals=StringVar()
xdiv_vals.set('0.5')
ydiv_vals=StringVar()
ydiv_vals.set('0.5')
lxp=StringVar()
lxp.set('1')
lxp=StringVar()
lxp.set('1')
lyp=StringVar()
lyp.set('1')
lyf=StringVar()
lyf.set('1')
tau=StringVar()
tau.set('1')
delay=StringVar()
delay.set('0')
unit=StringVar()
optionlist=['bits','nat','ban']
Label(master,text="").grid(row=4,column=0,padx=10)
Label(master,text="Number of symbols:").grid(row=5,column=0,sticky=W,padx=10)
Entry(master,textvariable=ns,width=3).grid(row=5,column=1,sticky=W)
Label(master,text="").grid(row=6,column=0,padx=10)
Label(master,text="Partition divisions:").grid(row=7,column=0,sticky=W,padx=10)
Radiobutton(master,text="equal-sized divisions",variable=div_type,value=1).grid(row=7,column=1,sticky=W)
Radiobutton(master,text="divisions with same number of points",variable=div_type,value=2).grid(row=8,column=1,columnspan=4,sticky=W)
Radiobutton(master,text="other (separate with commas):",variable=div_type,value=3).grid(row=9,column=1,sticky=W)
Label(master,text=" X divisions:").grid(row=9,column=2,sticky=W)
Entry(master,textvariable=xdiv_vals,width=10).grid(row=9,column=3,sticky=W)
Label(master,text=" Y divisions:").grid(row=10,column=2,sticky=W)
Entry(master,textvariable=ydiv_vals,width=10).grid(row=10,column=3,sticky=W)
Label(master,text="").grid(row=11,column=0)
Label(master,text="Symbolic length:").grid(row=12,column=0,sticky=W,padx=10)
Label(master,text="Past of X:").grid(row=12,column=1,sticky=W)
Entry(master,textvariable=lxp,width=3).grid(row=12,column=2,sticky=W)
Label(master,text="Past of Y:").grid(row=13,column=1,sticky=W)
Entry(master,textvariable=lyp,width=3).grid(row=13,column=2,sticky=W)
Label(master,text="Future of Y:").grid(row=14,column=1,sticky=W)
Entry(master,textvariable=lyf,width=3).grid(row=14,column=2,sticky=W)
Label(master,text="").grid(row=15,column=0)
Label(master,text="Tau:").grid(row=16,column=0,sticky=W,padx=10)
Entry(master,textvariable=tau,width=3).grid(row=16,column=1,sticky=W)
Label(master,text="").grid(row=17,column=0)
Label(master,text="Transmission delay:").grid(row=18,column=0,sticky=W,padx=10)
Entry(master,textvariable=delay,width=3).grid(row=18,column=1,sticky=W)
Label(master,text="").grid(row=19,column=0)
Label(master,text="Units:").grid(row=20,column=0,sticky=W,padx=10)
OptionMenu(master,unit,*optionlist).grid(row=20,column=1,sticky=W)
Label(master,text="").grid(row=21,column=0)
Button(master,text="Calculate",command=calcCami).grid(row=22,column=1,columnspan=2)


#running program
master.mainloop()
