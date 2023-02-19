# -*- coding: utf-8 -*-

import numpy as np
from SuguruLayout import SuguruLayout


class Suguru(object):
	### main object holding the number grid and solver methods
	
	def __init__(self):
		### empty initializer
		self.layout = None
		self.grid = None
		self.candidates = None
		
	def initlayout(self, layout):
		### set the layout with a given SuguruLayout instance
		
		if not isinstance(layout, SuguruLayout):
			msg = 'ERROR in Suguru.initlayout:'
			msg += ' expected a SuguruLayout instance'
			msg += ' but found {}'.format(type(layout))
			raise Exception(msg)
		self.layout = layout
		
	def initfromgrid(self, grid):
		### set the grid and candidates from a provided grid
		# input arguments:
		# - grid: 2D numpy array of integers,
		#   holding known numbers (and 0 for unknown numbers)
		
		# do some checks on provided grid
		if not isinstance(grid, np.ndarray):
			msg = 'ERROR in Suguru.initfromgrid:'
			msg += ' expected a np array but found {}.'.format(type(grid))
			raise Exception(msg)
		if not len(grid.shape)==2:
			msg = 'ERROR in Suguru.initfromgrid:'
			msg += ' expected a 2D np array'
			msg += ' but found a {}D array.'.format(len(grid.shape))
			raise Exception(msg)
		try:
			grid = grid.astype(int, casting='safe')
		except:
			msg = 'ERROR in Suguru.initfromgrid:'
			msg += ' expected dtype int but casting failed.'
			raise Exception(msg)
		# do checks on layout
		if self.layout is None:
			msg = 'ERROR in Suguru.initfromgrid:'
			msg += ' cannot initialize grid before layout.'
			raise Exception(msg)
		# set the grid
		self.grid = grid
		# set the candidates
		(nrows, ncols) = self.grid.shape
		self.candidates = []
		for i in range(nrows):
			self.candidates.append([])
			for j in range(ncols):
				self.candidates[i].append([])
				value = self.grid[i,j]
				# if the value is known, use [value] as candidates
				if value!=0: 
					self.candidates[i][j] = [value]
				# else, use [1, .., group size] as candidates
				else:
					groupsize = self.layout.groupsize((i,j))
					self.candidates[i][j] = list(range(1,groupsize+1))
					
	def initfromgrids(self, layout, grid):
		### combination of initlayout and initfromgrid with two provided grids
		slayout = SuguruLayout()
		slayout.initfromgrid(layout)
		self.initlayout(slayout)
		self.initfromgrid(grid)
		
	def initfromtxt(self, txtfile):
		### initialization from a txt file
		# check examples for required format of the txt file
		# read the file
		with open(txtfile,'r') as f:
			lines = f.readlines()
		# find the newline dividing the layout and grid
		split = lines.index('\n')
		layoutlines = lines[:split]
		gridlines = lines[split+1:]
		# make a layout from the first part of the read lines
		layout = []
		for line in layoutlines:
			line = line.strip(' \n\t')
			layout.append([])
			for el in line.split(' '): layout[-1].append(int(el))
		layout = np.array(layout)
		# make a layout from the first part of the read lines
		grid = []
		for line in gridlines:
			line = line.strip(' \n\t')
			grid.append([])
			for el in line.split(' '): grid[-1].append(int(el))
		grid = np.array(grid)
		self.initfromgrids(layout, grid)
		
	def totxt(self):
		### get a string representation that can be stored in a txt file
		res = str(self.layout)
		res += '\n'
		res += '\n'
		for row in self.grid:
			res += ' '.join(str(el) for el in row)+'\n'
		return res
	
	def savetotxt(self, txtfile):
		### save current instance to txt file
		selftxt = self.totxt()
		with open(txtfile, 'w') as f:
			f.write(selftxt)
		
	def check_valid_move(self, value, row, column):
		### check if filling a given value at a given position is a valid move
		
		# check if the position is already filled
		if( self.grid[row, column]!=0 ): return False
		# check if the value is still missing in the group
		if( value not in self.missing_values_in_group((row,column)) ): return False
		# check if the value is already present in one of the neighbours
		if( value in self.values_in_neighbours(row, column) ): return False
		# else true
		return True
	
	def check_valid(self, row=None, column=None):
		### check if current grid is valid
		if( row is None or column is None ):
			(nrows, ncols) = self.grid.shape
			for i in range(nrows):
				for j in range(ncols):
					if not self.check_valid(row=i, column=j): return False
			return True
		value = self.grid[row, column]
		# check if the position is already filled
		if( value==0 ): return True
		# check the neighbours
		if( value in self.values_in_neighbours(row, column) ): return False
		# check the group
		if( value in self.other_values_in_group((row, column)) ): return False
		# else true
		return True		
	
	def check_complete(self):
		if 0 in self.grid: return False
		return True
		
	def values_in_neighbours(self, row, column):
		### get all known values in the neighbours of a given cell
		values = []
		neighbours = self.layout.neighbours(row, column)
		for cell in neighbours:
			value = self.grid[cell[0],cell[1]]
			if value!=0: values.append(value)
		return values
		
	def values_in_group(self, groupid):
		### get all known values in a group
		values = []
		group_indices = self.layout.groupindices(groupid)
		for cell in group_indices:
			value = self.grid[cell[0],cell[1]]
			if value!=0: values.append(value)
		return values
	
	def other_values_in_group(self, cellid):
		### get all known values in a group excluding a specific cell
		# input argument: tuple with (row index, column index)
		values = []
		group_indices = self.layout.groupindices(cellid)
		for cell in group_indices:
			if tuple(cell)==tuple(cellid): continue
			value = self.grid[cell[0],cell[1]]
			if value!=0: values.append(value)
		return values
	
	def missing_values_in_group(self, groupid):
		### get all missing values in a group
		values = self.values_in_group(groupid)
		missing_values = list(range(1,self.layout.groupsize(groupid)+1))
		for value in values: missing_values.remove(value)
		return missing_values
	
	def knowns_in_group(self, groupid):
		### get all filled cell indices in a group
		inds = []
		group_indices = self.layout.groupindices(groupid)
		for cell in group_indices:
			value = self.grid[cell[0],cell[1]]
			if value!=0: inds.append(cell)
		return inds
	
	def unknowns_in_group(self, groupid):
		### get all unfilled cell indices in a group
		inds = []
		group_indices = self.layout.groupindices(groupid)
		for cell in group_indices:
			value = self.grid[cell[0],cell[1]]
			if value==0: inds.append(cell)
		return inds
		
	def reduceneighbours(self, cell=None, verbose=False):
		### basic solving method: remove values from neighbouring candidates
		# input arguments:
		# - cell: tuple of cell indices for which to reduce the neighbours
		#   (default: all cells with known values)
		removedcandidate = False
		if cell is None:
			cells = np.argwhere(self.grid)
			for cell in cells: 
				removedcandidate = removedcandidate or self.reduceneighbours(cell, verbose=verbose)
			return removedcandidate
		row = cell[0]
		column = cell[1]
		value = self.grid[row,column]
		if value==0: return False
		for neighbour in self.layout.neighbours(row,column):
			nrow = neighbour[0]
			ncolumn = neighbour[1]
			if value in self.candidates[nrow][ncolumn]:
				self.candidates[nrow][ncolumn].remove(value)
				removedcandidate = True
				if verbose:
					msg = 'Removed candidate {} from position ({},{})'.format(value,nrow,ncolumn)
					msg += ' because of neighbouring value.'
					print(msg)
		return removedcandidate
				
	def reducegroups(self, groupid=None, verbose=False):
		### basic solving method: remove values from candidates in same group
		# input arguments:
		# - groupid: group number
		#   (default: all groups)
		removedcandidate = False
		if groupid is None:
			ngroups = self.layout.ngroups
			for groupid in range(ngroups):
				removedcandidate = removedcandidate or self.reducegroups(groupid, verbose=verbose)
			return removedcandidate
		gvalues = self.values_in_group(groupid)
		gunknowns = self.unknowns_in_group(groupid)
		for cell in gunknowns:
			row = cell[0]
			column = cell[1]
			for value in gvalues:
				if value in self.candidates[row][column]:
					self.candidates[row][column].remove(value)
					removedcandidate = True
					if verbose:
						msg = 'Removed candidate {} from position ({},{})'.format(value,row,column)
						msg += ' because of same value in group.'
						print(msg)
		return removedcandidate
					
	def fillsingles(self, verbose=False):
		### basic solving method: fill all cells with only one candidate
		filledvalue = False
		(nrows, ncols) = self.grid.shape
		for i in range(nrows):
			for j in range(ncols):
				if( self.grid[i,j]==0 and len(self.candidates[i][j])==1 ):
					value = self.candidates[i][j][0]
					self.grid[i,j] = value
					filledvalue = True
					if verbose:
						msg = 'Filled value {} on position ({},{})'.format(value,i,j)
						msg += ' because it is the only remaining candidate.'
						print(msg)
		return filledvalue
	
	def fillgroups(self, groupid=None, verbose=False):
		### basic solving method: fill values that can only go in one place in a group
		# input arguments:
		# - groupid: group number
		#   (default: all groups)
		filledcandidate = False
		if groupid is None:
			ngroups = self.layout.ngroups
			for groupid in range(ngroups):
				filledcandidate = filledcandidate or self.fillgroups(groupid, verbose=verbose)
			return filledcandidate
		gmvalues = self.missing_values_in_group(groupid)
		gunknowns = self.unknowns_in_group(groupid)
		for value in gmvalues:
			ncandidatespots = 0
			for cell in gunknowns:
				row = cell[0]
				column = cell[1]
				if value in self.candidates[row][column]:
					ncandidatespots += 1
					fixedrow, fixedcolumn = row, column
			if ncandidatespots == 1:
				self.grid[fixedrow,fixedcolumn] = value
				self.candidates[fixedrow][fixedcolumn] = [value]
				filledcandidate = True
				if verbose:
					msg = 'Filled value {} on position ({},{})'.format(value,fixedrow,fixedcolumn)
					msg += ' because it is the only place in the group it can go.'
					print(msg)
		return filledcandidate
	
	def reducetuples(self, groupid=None, verbose=False):
		### intermediate solving method: 
		# if any tuples exist of n cells with the same n candidates,
		# remove these candidates from all cells that are adjacent to all the tuple cells.
		removedcandidate = False
		if groupid is None:
			ngroups = self.layout.ngroups
			for groupid in range(ngroups):
				removedcandidate = removedcandidate or self.reducetuples(groupid, verbose=verbose)
			return removedcandidate
		gmvalues = self.missing_values_in_group(groupid)
		gunknowns = self.unknowns_in_group(groupid)
		if len(gmvalues)!=len(gunknowns): return False
		if len(gmvalues)==0: return False
		# (todo: generalize the above for the case the tuple is a subset of the unknowns,
		# rather than the whole set of unknowns within a group)
		for cell in self.layout.commonneighbours(gunknowns):
			row, column = cell[0], cell[1]
			for value in gmvalues:
				if value in self.candidates[row][column]:
					self.candidates[row][column].remove(value)
					removedcandidate = True
					if verbose:
						msg = 'Removed candidate {} from position ({},{})'.format(value,row,column)
						msg += ' because of tuple reduction.'
						print(msg)
		return removedcandidate
					
	def solve(self, verbose=False):
		### total solving method grouping all submethods
		# return type: 
		#   tuple of (int, info string)
		#   with following convention:
		#   - -1 = invalid suguru (either invalid input or bug in solver) 
		#   - 0 = suguru valid and solved completely
		#   - 1 = suguru valid but not solved completely (solver not powerful enough)
		
		# solve as far as possible
		donext = True
		while donext:
			removedneighbour = self.reduceneighbours(verbose=verbose)
			removedgroup = self.reducegroups(verbose=verbose)
			filledsingle = self.fillsingles(verbose=verbose)
			filledgroup = self.fillgroups(verbose=verbose)
			reducedtuple = self.reducetuples(verbose=verbose)
			donext = (
			  removedneighbour 
			  or removedgroup 
			  or filledsingle 
			  or filledgroup
			  or reducedtuple
		    )
		# return info on result
		valid = self.check_valid()
		complete = self.check_complete()
		if not valid: return (-1, 'Suguru invalid')
		if not complete: return (1, 'Suguru incomplete')
		return (0, 'Suguru solved')