# -*- coding: utf-8 -*-

import sys
sys.path.append('src')

import tkinter as tk
from SuguruSolverGUI import SuguruSolverGUI


if __name__=='__main__':
	
	root = tk.Tk() 
	gui = SuguruSolverGUI(root) 
	root.mainloop()