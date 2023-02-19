# -*- coding: utf-8 -*-

import numpy as np


class SuguruLayout(object):
	### layout of a suguru field, defining the number groups
	
	def __init__(self):
		### empty initializer
		self.layout = None
		self.ngroups = 0
		
	def initfromgrid(self, grid):
		### initializer from a numpy array
		# input arguments:
		# - grid: 2D numpy array of integers (0 to n),
		#   identifying the layout of the number groups
		
		# do some checks on the input grid
		if not isinstance(grid, np.ndarray):
			msg = 'ERROR in SuguruLayout.initfromgrid:'
			msg += ' expected a np array but found {}.'.format(type(grid))
			raise Exception(msg)
		if not len(grid.shape)==2:
			msg = 'ERROR in SuguruLayout.initfromgrid:'
			msg += ' expected a 2D np array'
			msg += ' but found a {}D array.'.format(len(grid.shape))
			raise Exception(msg)
		try:
			grid = grid.astype(int, casting='safe')
		except:
			msg = 'ERROR in SuguruLayout.initfromgrid:'
			msg += ' expected dtype int but casting failed.'
			raise Exception(msg)
		if np.amin(grid)!=0:
			msg = 'ERROR in SuguruLayout.initfromgrid:'
			msg += ' the array is supposed to hold integers starting from 0'
			msg += ' but found {} as minimum value.'.format(np.amin(grid))
			raise Exception(msg)
		# set the instance attributes
		self.layout = grid
		self.ngroups = np.amax(grid)+1
		
	def initfromtxt(self, txtfile):
		### initializer from a txt file name
		# input arguments:
	    # - txtfile: path to a txt file holding a valid grid;
		#   the columns should be separated by spaces and the rows by newlines
		
		# read the file
		with open(txtfile,'r') as f:
			lines = f.readlines()	
		# make a grid from the read lines
		grid = []
		for line in lines:
			line = line.strip(' \n\t')
			grid.append([])
			for el in line.split(' '): grid[-1].append(int(el))
		grid = np.array(grid)
		# initialize this instance
		self.initfromgrid(grid)
		
	def groupmask(self, groupid):
		### get a mask array for a given group
		# input arguments:
		# - groupid: group identifier; following cases are allowed:
		#   - group number (integer)
		#   - list, array or tuple of cell indices
		if not isinstance(groupid, int):
			groupid = self.layout[groupid[0],groupid[1]] 
		if(groupid >= self.ngroups):
			msg = 'ERROR in SuguruLayout.getmask:'
			msg += ' provided group number {}'.format(groupid)
			msg += ' is larger than number of groups ({}).'.format(self.ngroups)
			raise Exception(msg)
		return self.layout == groupid
	
	def groupindices(self, groupid):
		### get a collection of indices for a given group
		return np.argwhere(self.groupmask(groupid))
	
	def groupsize(self, groupid):
		### get the size (number of cells) for a given group
		return len(self.groupindices(groupid))
	
	def maxgroupsize(self):
		### get the maximum group size (in number of cells)
		groupsizes = [self.groupsize(groupid) for groupid in range(self.ngroups)]
		return max(groupsizes)
	
	def neighbours(self, row, column):
		### get a collection of indices of neighbouring cells
		neighbours = []
		(nrows,ncols) = self.layout.shape
		for i in range(row-1,row+2):
			for j in range(column-1, column+2):
				# remove invalid cells (outside of grid range)
				if i < 0: continue
				if i >= nrows: continue
				if j < 0: continue
				if j >= ncols: continue
				# remove center cell
				if( i==row and j==column ): continue
				neighbours.append((i,j))
		return neighbours
	
	def nneighbours(self, row, column):
		### get number of neighbours of a given cell
		return len(self.neighbours(row, column))
	
	def commonneighbours(self, cells):
		### get a collection of indices of cells neighbouring all cells in the provided list
		neighbours = []
		if len(cells)==0: return neighbours
		firstcell = cells[0]
		othercells = cells[1:]
		for cell in self.neighbours(firstcell[0], firstcell[1]):
			allneighbour = True
			for othercell in othercells:
				if tuple(cell)==tuple(othercell): 
					allneighbour = False
					break
				if abs(cell[0]-othercell[0])>1:
					allneighbour = False
					break
				if abs(cell[1]-othercell[1])>1:
					allneighbour = False
					break
			if allneighbour: 
				neighbours.append(cell)
		return neighbours
	
	def __str__(self):
		### return string representation
		lines = []
		(nrows,ncols) = self.layout.shape
		for i in range(nrows):
			lines.append( ' '.join( str(self.layout[i,j]) for j in range(ncols) ) )
		return '\n'.join(lines)