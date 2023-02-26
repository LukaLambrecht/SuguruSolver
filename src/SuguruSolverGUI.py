# -*- coding: utf-8 -*-

# imports
import sys
import os
import numpy as np
import random
import matplotlib
from SuguruLayout import SuguruLayout
from Suguru import Suguru
from SuguruImageReader import SuguruImageReader
try:
	import Tkinter as tk
	import ScrolledText as scrtxt
	import tkFileDialog as fldlg
except ImportError: 
	import tkinter as tk
	import tkinter.scrolledtext as scrtxt
	import tkinter.filedialog as fldlg

class StdOutRedirector:
	### helper class to redirect print output to GUI widget
	# use as follows:
	#   stdout = sys.stdout
	#   sys.stdout = StdOutRedirector(<some widget>)
	#   ... <some code execution containing print statements>
	#   sys.stdout = stdout

	def __init__(self, tk_text_widget, tk_root_object):
		self.text_dump = tk_text_widget
		self.root = tk_root_object

	def write(self, text):
		self.text_dump.insert(tk.INSERT, text)
		self.text_dump.see(tk.END)
		self.root.update()

class SuguruSolverGUI:
	
	def __init__(self, master):
		self.master = master
		master.title("SuguruSolver GUI")

		# set global geometry parameters
		self.bwidth = 30 # button width
		self.bheight = 10 # button height
		
		# define a frame for the suguru layout cells	  
		self.layout_frame = tk.Frame(master, width=200)
		self.layout_frame.grid(row=0, column=0, padx=10, pady=10)
		
		# define a frame for the layout buttons
		self.layout_buttons_frame = tk.Frame(master, width=200)
		self.layout_buttons_frame.grid(row=0, column=1)
		# add a button to update the dimension
		self.change_dim_button = tk.Button(self.layout_buttons_frame,
									 text='Change size',
									 command=self.open_change_dim_window)
		self.change_dim_button.grid(row=0, column=0, 
						ipadx=self.bwidth, ipady=self.bheight)
		# add a button to clear the layout
		self.clear_layout_button = tk.Button(self.layout_buttons_frame,
									 text='Clear',
									 command=self.clear_layout)
		self.clear_layout_button.grid(row=1, column=0, 
						ipadx=self.bwidth, ipady=self.bheight)
		# add a button to update the grid with the layout
		self.update_layout_to_grid_button = tk.Button(self.layout_buttons_frame,
												text='Update',
												command=self.update_layout_to_grid)
		self.update_layout_to_grid_button.grid(row=2, column=0, 
											   ipadx=self.bwidth, ipady=self.bheight)
		# add a button to upload an image
		self.load_image_button = tk.Button(self.layout_buttons_frame,
									 text='Upload image',
									 command=self.load_image)
		self.load_image_button.grid(row=3, column=0, ipadx=self.bwidth, ipady=self.bheight)

		# define a frame for the suguru grid cells	  
		self.grid_frame = tk.Frame(master, width=200)
		self.grid_frame.grid(row=0, column=2, padx=10, pady=10)
		
		# define a frame for the candidate cells
		self.candidate_frame = tk.Frame(master, height=30, width=200)
		self.candidate_frame.grid(row=1, column=2, padx=10, pady=10)
		
		# initialize the grid with default size
		self.initgrid()
		
		# define a frame for the buttons and fill it				
		self.buttons_frame = tk.Frame(master, width=200)
		self.buttons_frame.grid(row=0, column=3, rowspan=2)

		# define mode button 
		self.mode = tk.StringVar()
		self.mode.set("A")
		#self.auto_button = tk.Radiobutton(self.buttons_frame,
		#							text='Automatic',indicatoron=False,
		#							variable=self.mode,value="A",command=self.setmode)
		#self.auto_button.grid(row=0, column=0, ipadx=self.bwidth, ipady=self.bheight)
		#self.inter_button = tk.Radiobutton(master,text='Interactive',indicatoron=False,
		#						variable=self.mode,value="I",command=self.setmode)
		#self.inter_button.grid(row=0,column=3,ipadx=self.bwidth,ipady=self.bheight)
		
		self.solve_button = tk.Button(self.buttons_frame, text='Solve',command=self.solve)
		self.solve_button.grid(row=1, column=0, columnspan=2, ipadx=self.bwidth, ipady=self.bheight)
		
		self.load_button = tk.Button(self.buttons_frame,text='Load',command=self.load)
		self.load_button.grid(row=2,column=0,ipadx=self.bwidth,ipady=self.bheight)
		
		self.save_button = tk.Button(self.buttons_frame, text='Save', command=self.save)
		self.save_button.grid(row=2, column=1,ipadx=self.bwidth, ipady=self.bheight)
		
		self.clear_button = tk.Button(self.buttons_frame, text='Clear', command=self.clear)
		self.clear_button.grid(row=3, column=0, ipadx=self.bwidth, ipady=self.bheight)
		
		self.abort_button = tk.Button(self.buttons_frame, text='Abort', command=self.abort)
		self.abort_button.grid(row=3, column=1, ipadx=self.bwidth, ipady=self.bheight)
		
		self.close_button = tk.Button(self.buttons_frame, text='Close', command=master.destroy)
		self.close_button.grid(row=4, column=0, columnspan=2, ipadx=self.bwidth, ipady=self.bheight)

		self.hint_button = tk.Button(self.buttons_frame, text='Hint', command=self.hint)

		self.reduce_button = tk.Button(self.buttons_frame, text='Reduce', command=self.reduce)
		
		self.messages_text = scrtxt.ScrolledText(master, width=75, height=25)
		self.messages_text.grid(row=2, column=0, columnspan=4)
		initstring = 'Welcome to the Suguru Solver!\n'
		initstring += '- Click on the cells in the grid above to set the intial values \n'
		initstring += '  or press "Load" to load a previously saved grid.\n'
		initstring += '- (Optional:) Save the grid you filled in by pressing "Save" \n'
		initstring += '  (this will overwrite any previously saved grid)\n'
		initstring += '- Solve your suguru by pressing "Solve"!\n\n'
		self.messages_text.insert(tk.INSERT,initstring)
		
		# other settings
		self.logfilename = 'logs/currentlog.txt'
		
	def initgrid(self, nrows=6, ncols=6, maxgroupsize=5):
		### (re-) initialize the grid with specified parameters
		# the parameters to specify are:
		# - nrows: number of rows in the grid
		# - ncols: number of columns in the grid
		# - maxgroupsize: maximum size of a group
		
		# delete previous grid widgets
		for child in self.layout_frame.winfo_children():
			child.destroy()
		for child in self.grid_frame.winfo_children():
			child.destroy()
		for child in self.candidate_frame.winfo_children():
			child.destroy()
			
		# initializations
		self.gridnrows = nrows
		self.gridncols = ncols
		self.maxgroupsize = maxgroupsize
		self.gridcells = []
		self.layoutcells = []
		self.candidatecells = []
		
		# make layout entries
		for i in range(self.gridnrows):
			self.layoutcells.append([])
			for j in range(self.gridncols):
				cell_entry = tk.Entry(self.layout_frame, font="Calibri 20", 
									  justify='center',width=2)
				cell_entry.grid(row=i, column=j)
				self.layoutcells[i].append(cell_entry)
		
		# make grid entries
		for i in range(self.gridnrows):
			self.gridcells.append([])
			for j in range(self.gridncols):
				cell_entry = tk.Entry(self.grid_frame, font="Calibri 20", 
									  justify='center',width=2)
				cell_entry.grid(row=i, column=j)
				self.gridcells[i].append(cell_entry)
				self.gridcells[i][j].bind("<1>",lambda event,row=i,col=j : 
											self.showcandidates(event,row,col))

		# make candidate entries
		for i in range(self.gridnrows):
			self.candidatecells.append([])
			for j in range(self.gridncols):
				self.candidatecells[i].append([])
				for k in range(self.maxgroupsize):
					var = tk.IntVar(value=1)
					candidate_rbutton = tk.Checkbutton(self.candidate_frame,text=str(k+1),
							font="Calibri 20",justify='center',width=2,indicatoron=False,
							var=var,background="red",selectcolor='green')
					self.candidatecells[i][j].append({'button':candidate_rbutton,'var':var})

		# set focus to (0,0) and show corresponding candidates
		#self.gridcells[0][0].focus()
		#for k in range(self.maxgroupsize): 
		#	self.candidatecells[0][0][k]['button'].grid(row=0,column=k)
		
	def open_change_dim_window(self):
		### change the size of the layout and grid
		self.clear_layout()
		# create a self.changedimpopup window
		self.changedimpopup = tk.Toplevel(self.master)
		self.changedimpopup.title('Change the size of the grid')
		# define the widgets
		nrowslabel = tk.Label(self.changedimpopup, text='Number of rows')
		self.nrows_text = tk.Entry(self.changedimpopup)
		ncolslabel = tk.Label(self.changedimpopup, text='Number of columns')
		self.ncols_text = tk.Entry(self.changedimpopup)
		ok_button = tk.Button(self.changedimpopup, text='Ok', command=self.change_dim)
		cancel_button = tk.Button(self.changedimpopup, text='Cancel', command=self.cancel_change_dim)
		# pack the widgets
		nrowslabel.grid(row=0, column=0)
		self.nrows_text.grid(row=0, column=1)
		ncolslabel.grid(row=1, column=0)
		self.ncols_text.grid(row=1, column=1)
		ok_button.grid(row=2, column=0)
		cancel_button.grid(row=2, column=1)
		
	def change_dim(self):
		### read the content of the change dim self.changedimpopup and change the layout
		nrows = self.nrows_text.get()
		ncols = self.ncols_text.get()
		self.changedimpopup.destroy()
		try:
			nrows = int(nrows)
			ncols = int(ncols)
		except:
			print('ERROR: could not convert to integers.')
			return
		self.initgrid(nrows=nrows, ncols=ncols)
		
	def cancel_change_dim(self):
		self.changedimpopup.destroy()
		
	def clear_layout(self):
		### clear the layout
		
		# first clear the grid
		# (as clearing layout but keeping grid is senseless)
		self.clear()
		# delete cell content and color in both layout and grid
		for i in range(self.gridnrows):
			for j in range(self.gridncols):
				self.gridcells[i][j].config({'background':'white'})
				self.layoutcells[i][j].config({'background':'white'})
				self.layoutcells[i][j].delete(0,tk.END)

	def setmode(self):
		### set the mode of the GUI (automatic versus interactive)
		mode = self.mode.get()
		if mode=='A':
			try:
				self.hint_button.grid_forget()
				self.reduce_button.grid_forget()
				for wid in self.candidate_frame.grid_slaves():
					wid.grid_forget()
			except: pass
			self.solve_button.grid(row=0,column=0,columnspan=2,ipadx=self.bwidth,ipady=self.bheight)
		elif mode=='I':
			try:
				self.solve_button.grid_forget()
			except: pass
			self.hint_button.grid(row=0,column=0,ipadx=self.bwidth,ipady=self.bheight)
			self.reduce_button.grid(row=0,column=1,ipadx=self.bwidth,ipady=self.bheight)
			self.gridcells[0][0].focus()
			for k in range(self.maxgroupsize): self.candidatecells[0][0][k]['button'].grid(row=0,column=k)

	def showcandidates(self,event,i,j):
		### show the candidates for a given cell
		if self.mode.get()=='A': return None
		for wid in self.candidate_frame.grid_slaves():
			wid.grid_forget()
		for k,buttondict in enumerate(self.candidatecells[i][j]):
			buttondict['button'].grid(row=0,column=k)

	def readgrid(self):
		### return the grid currently entered in the GUI cells
		# return type: 2D numpy array
		grid = np.zeros((self.gridnrows,self.gridncols),dtype=int)
		for i in range(self.gridnrows):
			for j in range(self.gridncols):
				val = self.gridcells[i][j].get()
				if(val==''): continue
				if(val=='_'): continue
				message =  '[notification:] ERROR: invalid value found in input grid: '+str(val)+'\n\n'
				try:
					intval = int(val)
				except:
					self.messages_text.insert(tk.INSERT,message)
					self.messages_text.see(tk.END)
					return None
				if(intval<1 or intval>self.maxgroupsize):
					self.messages_text.insert(tk.INSERT,message)
					self.messages_text.see(tk.END)
					return None
				grid[i,j] = intval
		return grid
				
	def readlayout(self):
		### return the layout grid currently entered in the GUI cells
		# return type: 2D numpy array
		layout = np.zeros((self.gridnrows,self.gridncols),dtype=int)
		for i in range(self.gridnrows):
			for j in range(self.gridncols):
				val = self.layoutcells[i][j].get()
				if(val==''): continue
				if(val=='_'): continue
				message =  '[notification:] ERROR: invalid value found in input layout: '+str(val)+'\n\n'
				try:
					intval = int(val)
				except:
					self.messages_text.insert(tk.INSERT,message)
					self.messages_text.see(tk.END)
					return None
				if(intval<0):
					self.messages_text.insert(tk.INSERT,message)
					self.messages_text.see(tk.END)
					return None
				layout[i,j] = intval
		return layout
				
	def update_layout_to_grid(self):
		### update the layout currently entered in the GUI to the grid in the GUI
		layout = self.readlayout()
		slayout = SuguruLayout()
		slayout.initfromgrid(layout)
		self.setlayout(slayout)

	def getcandidates(self):
		### get the candidates as currently stored in the GUI cells
		# return type: 3D list with integer values (remaining candidates for each cell)
		candidates = []
		for i in range(self.gridnrows):
			candidates.append([])
			for j in range(self.gridncols):
				candidates[i].append([])
				for k in range(self.maxgroupsize):
					if self.candidatecells[i][j][k]['var'].get() == 1: candidates[i][j].append(k+1)
		return candidates

	def updategrid(self, grid, markfilled=False, markunfilled=False):
		### update the GUI grid using an externally provided array
		# input arguments:
		# - grid: 2D numpy array with integers (0 for unknown values)
		# - markfilled: mark newly filled cells
		# - markunfilled: mark remaining unfilled cells
		for i in range(self.gridnrows):
			for j in range(self.gridncols):
				val = self.gridcells[i][j].get()
				if(val==''):
					newval = int(grid[i,j])
					if newval==0:
						if markunfilled:
							self.gridcells[i][j].insert(0,'_')
							self.gridcells[i][j].config(foreground='red')
					else:
						self.gridcells[i][j].insert(0,str(newval))
						if markfilled: self.gridcells[i][j].config(foreground='green')

	def updatecandidates(self, candidates):
		### update the GUI candidates using an externally provided list
		# input arguments:
		# - candidates: 3D list with integers
		for i in range(self.gridnrows):
			for j in range(self.gridncols):
				for k in range(self.maxgroupsize):
					if(not k+1 in candidates[i][j] and self.candidatecells[i][j][k]['var'].get() == 1):
						self.candidatecells[i][j][k]['var'].set(0)
						
	def setlayout(self, slayout):
		### set the layout of the GUI grid using an externally provided SuguruLayout instance
		
		# check dimensions
		if(slayout.layout.shape != (self.gridnrows,self.gridncols)):
			msg = 'ERROR in setlayout: shapes do not match:'
			msg += ' provided layout: {},'.format(slayout.layout.shape)
			msg += ' current layout: {}'.format((self.ngridrows,self.ngridcols))
			raise Exception(msg)
		# define colors
		crgba = matplotlib.cm.get_cmap('rainbow', slayout.ngroups)
		chex = []
		for i in range(crgba.N):
			rgba = crgba(i)
			chex.append( matplotlib.colors.rgb2hex(rgba) )
		random.shuffle(chex)
		# set cell colors and values
		for i in range(self.gridnrows):
			for j in range(self.gridncols):
				color = chex[slayout.layout[i,j]]
				self.gridcells[i][j].config({'background':color})
				self.layoutcells[i][j].config({'background':color})
				self.layoutcells[i][j].delete(0,tk.END)
				self.layoutcells[i][j].insert(0,str(slayout.layout[i,j]))
		# set layout
		self.layout = slayout.layout
		
	def solve(self):
		### read the suguru currently stored in the GUI and solve it
		
		# read the suguru
		layout = self.readlayout()
		grid = self.readgrid()
		suguru = Suguru()
		suguru.initfromgrids(layout, grid)
		
		# display a message that solving will start
		message =  '[notification:] Now solving...\n'
		message += '				You can find the full log file below when done.\n\n'
		self.messages_text.insert(tk.INSERT,message)
		self.messages_text.see(tk.END)
		self.master.update() # needed for displaying text synchronously
		self.makelog()
		# redirect sys.stdout to text widget
		stdout = sys.stdout
		sys.stdout = StdOutRedirector(self.messages_text, self.master)
		# solve the suguru
		(resultcode, resultmessage) = suguru.solve(verbose=True)
		# reset sys.stdout
		sys.stdout = stdout
		#self.readlog()
		# print info message
		message = '\n\n[notification:] '+resultmessage+'\n\n'
		self.messages_text.insert(tk.INSERT,message)
		self.messages_text.see(tk.END)
		# update the GUI grid cells
		self.updategrid(suguru.grid, markfilled=True, markunfilled=True)
		
	def abort(self):
		pass # not yet implemented
 
	def save(self):
		abspath = os.path.abspath(os.path.dirname(__file__))
		fullpath = os.path.join(abspath,'../examples')
		filename = fldlg.asksaveasfilename(initialdir=fullpath,
					title='Save suguru as',
					defaultextension='.txt')
		if filename is None:
			message = '[notification:] Saving suguru canceled.\n\n'
			self.messages_text.insert(tk.INSERT,message)
			self.messages_text.see(tk.END)
			return
		#try:
		if(2>1):
			# read the suguru
			layout = self.readlayout()
			grid = self.readgrid()
			suguru = Suguru()
			suguru.initfromgrids(layout, grid)
			# save the suguru instance to the selected file
			suguru.savetotxt(filename)
			message =  '[notification:] Suguru saved successfully.\n\n'
			self.messages_text.insert(tk.INSERT,message)
			self.messages_text.see(tk.END)
		#except:
		else:
			message = '[notification:] ERROR: Suguru could not be saved to file.\n\n'
			self.messages_text.insert(tk.INSERT,message)
			self.messages_text.see(tk.END)
			return None
		
	def load(self):
		abspath = os.path.abspath(os.path.dirname(__file__))
		fullpath = os.path.join(abspath,'../examples')
		filename = fldlg.askopenfilename(initialdir=fullpath,
					title='Select suguru to load',
					filetypes=(('txt files','*.txt'),('all files','*.*')))
		if filename is None: 
			message = '[notification:] Loading suguru canceled.\n\n'
			self.messages_text.insert(tk.INSERT,message)
			self.messages_text.see(tk.END)
			return
		try:
			# load a Suguru instance from the selected file
			self.suguru = Suguru()
			self.suguru.initfromtxt(filename)
			nrows, ncols = self.suguru.layout.layout.shape
			maxgroupsize = self.suguru.layout.maxgroupsize()
			# re-initialize the GUI grid and layout with correct shape
			self.clear_layout()
			self.initgrid( nrows=nrows, ncols=ncols, maxgroupsize=maxgroupsize )
			self.updategrid(self.suguru.grid)
			self.setlayout(self.suguru.layout)
			message =  '[notification:] Suguru loaded successfully.\n\n'
			self.messages_text.insert(tk.INSERT,message)
			self.messages_text.see(tk.END)
		except:
			message = '[notification:] ERROR: Suguru could not be loaded from file.\n\n'
			self.messages_text.insert(tk.INSERT,message)
			self.messages_text.see(tk.END)
			return None
		
	def load_image(self):
		abspath = os.path.abspath(os.path.dirname(__file__))
		fullpath = os.path.join(abspath,'../images')
		filename = fldlg.askopenfilename(initialdir=fullpath,
					title='Select image to load',
					filetypes=(('png images','*.png'),('all files','*.*')))
		if filename is None: 
			message = '[notification:] Loading image canceled.\n\n'
			self.messages_text.insert(tk.INSERT,message)
			self.messages_text.see(tk.END)
			return
		try:
			# reconstruct a Suguru instance from the selected image
			reader = SuguruImageReader()
			reader.loadimage(filename)
			reader.findsuguru(doplot=True)
			self.suguru = Suguru()
			self.suguru.initfromgrids(reader.layout, reader.grid)
			nrows, ncols = self.suguru.layout.layout.shape
			maxgroupsize = self.suguru.layout.maxgroupsize()
			# re-initialize the GUI grid and layout with correct shape
			self.clear_layout()
			self.initgrid( nrows=nrows, ncols=ncols, maxgroupsize=maxgroupsize )
			self.updategrid(self.suguru.grid)
			self.setlayout(self.suguru.layout)
			message =  '[notification:] Suguru loaded successfully.\n\n'
			self.messages_text.insert(tk.INSERT,message)
			self.messages_text.see(tk.END)
		except:
			message = '[notification:] ERROR: Suguru could not be loaded from image.\n\n'
			self.messages_text.insert(tk.INSERT,message)
			self.messages_text.see(tk.END)
			return None
	
	def clear(self):
		### clear the current grid (but keep layout)
		for i in range(self.gridnrows):
			for j in range(self.gridncols):
				# delete the value from the grid cell
				# and set the text color back to default black
				self.gridcells[i][j].delete(0,tk.END)
				self.gridcells[i][j].config(foreground='black')
				# set all candidates as allowed
				for k in range(self.maxgroupsize):
					self.candidatecells[i][j][k]['var'].set(1)
		message = '[notification:] Current grid cleared. \n\n'
		self.messages_text.insert(tk.INSERT,message)
		self.messages_text.see(tk.END)

	def makelog(self):
		abspath = os.path.abspath(os.path.dirname(__file__))
		fullpath = os.path.join(abspath,self.logfilename)
		if os.path.exists(fullpath): os.system('rm '+fullpath)
		fname = fullpath[fullpath.rfind('/')+1:]
		dirname = fullpath[:fullpath.rfind('/')]
		if not os.path.exists(dirname): os.makedirs(dirname)
		os.chdir(dirname)
		lf = open(fname,'w')
		lf.close()
		os.chdir(abspath)	

	def readlog(self):
		lf = open(self.logfilename,'r')
		message = lf.read()
		self.messages_text.insert(tk.INSERT,message)
		self.messages_text.see(tk.END)

	def hint(self):
		pass # not yet implemented

	def reduce(self):
		pass # not yet implemented