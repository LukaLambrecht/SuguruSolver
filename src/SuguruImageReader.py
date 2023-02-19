# -*- coding: utf-8 -*-

# imports
import os
import numpy as np
import cv2
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt



class SuguruImageReader(object):
	### class for reading a suguru grid from an image.
	# For now, focus on 'nice' images, i.e.:
	# - good and uniform lighting
	# - horizontal and vertical orientation of straight lines
	# - equal thickness of all lines
	# - digital written numbers
	
	def __init__(self):
		self.image = None
		self.gridlines = None
		self.grid = None
		self.layout = None
	
	def loadimage(self, imagefile, targetsize=None):
		### load an image and perform preprocessing.
		# preprocessing includes:
		# - convert to 2D grayscale array
		# - project values to 0 or 1
		#   (note: high values = white will be projected to 0,
		#    low values = black will be projected to 1!)
		# - type conversion to numpy uint8
		# - resizing (optional)
		self.image = cv2.imread(imagefile)
		self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
		self.image = np.where(self.image>128,0,1)
		self.image = self.image.astype(np.uint8)
		if targetsize is not None:
			self.image = cv2.resize(self.image, targetsize)
			self.image = np.where(self.image>128,0,1)
		
	def drawimage(self):
		### draw the currently loaded image for visual inspection
		(fig,ax) = plt.subplots()
		ax.imshow(self.image, cmap='gray')
		ax.set_title('Loaded grid image')
		ax.set_xticks([])
		ax.set_yticks([])
		plt.show(block=False)
		
	def drawgridlines(self, extralines=None):
		### draw currently loaded image with reconstructed grid lines
		# input arguments:
		# - lines: list of objects of the form (x1,y1,x2,y2)
		#   (to be drawn in addition to grid lines)
		
		# convert self.image to colored image
		cselfimage = np.dstack((self.image,self.image,self.image))
		cselfimage = np.where(cselfimage>0.5,255,0)
		cselfimage = cselfimage.astype(np.uint8)
		# plot self.image
		(fig,ax) = plt.subplots()
		ax.imshow(cselfimage)
		# draw all lines
		thickness = 2
		color = 'r'
		style = '--'
		plt.autoscale(enable=False)
		if extralines is not None:
			for line in extralines:
				x1,y1,x2,y2 = line
				ax.plot(x1, y1, x2, y2, linewidth=thickness, color=color, linestyle=style)
		if self.gridlines is not None:
			xmin = 0
			xmax = self.image.shape[1]
			for y in self.gridlines[0]:
				ax.plot([xmin, xmax], [y, y], linewidth=thickness, color=color, linestyle=style)
			ymin = 0
			ymax = self.image.shape[0]
			for x in self.gridlines[1]:
				ax.plot([x, x], [ymin, ymax], linewidth=thickness, color=color, linestyle=style)
		ax.set_title('Loaded grid image with reconstructed grid lines')
		#ax.set_xticks([])
		#ax.set_yticks([])
		plt.show(block=False)
		
	def findgridlines(self, nprobes=7, threshold=0.5):
		### find the position of row and column lines
		# returns:
		# tuple of two lists, y-positions of horizontal lines and x-position of vertical lines
		# (including outer lines)
		if self.image is None:
			raise Exception('Current image is None')
		(imgheight,imgwidth) = self.image.shape
		# define horizontal and vertical probe positions
		horprobes = np.linspace(imgheight/4, imgheight*3/4, num=nprobes)
		verprobes = np.linspace(imgwidth/4, imgwidth*3/4, num=nprobes)
		# initialize masks
		horlines = (self.image[:,0]>-1).nonzero()
		verlines = (self.image[0,:]>-1).nonzero()
		# make intersection with probes
		for verprobe in verprobes:
			horlines = np.intersect1d( horlines, (self.image[:,int(verprobe)]>threshold).nonzero() )
		for horprobe in horprobes:
			verlines = np.intersect1d( verlines, (self.image[int(horprobe),:]>threshold).nonzero() )
		# reduce lines of non-unitiy thickness to single lines
		filtered_horlines = []
		filtered_verlines = []
		for i in horlines:
			if( i<imgheight/2.1 and i+1 in horlines ): continue
			if( i>=imgheight/2.1 and i-1 in horlines): continue
			filtered_horlines.append(i)
		for i in verlines:
			if( i<imgwidth/2.1 and i+1 in verlines ): continue
			if( i>=imgwidth/2.1 and i-1 in verlines): continue
			filtered_verlines.append(i)
		# set and return the result
		self.gridlines = (filtered_horlines, filtered_verlines)
		return self.gridlines
	
	def findlayout(self):
		### find the layout of the grid by checking line thickness
		# returns:
		# numpy grid with layout
		if self.image is None:
			raise Exception('Current image is None')
		if self.gridlines is None:
			raise Exception('Current gridlines is None')
		horlines = self.gridlines[0]
		verlines = self.gridlines[1]
		nrows = len(horlines)-1
		ncols = len(verlines)-1
		# make grids of edge thicknesses
		horedges = np.zeros((nrows-1,ncols))
		for j in range(ncols):
			xcoord = int((verlines[j]+verlines[j+1])/2.)
			for i in range(nrows-1):
				ycoord = horlines[i+1]
				section = self.image[ycoord-5:ycoord+5,xcoord]
				horedges[i,j] = np.sum(section)
		veredges = np.zeros((nrows,ncols-1))
		for i in range(nrows):
			ycoord = int((horlines[i]+horlines[i+1])/2.)
			for j in range(ncols-1):
				xcoord = verlines[j+1]
				section = self.image[ycoord,xcoord-5:xcoord+5]
				veredges[i,j] = np.sum(section)
		# find thickness threshold
		# to do later, use hard-coded for now
		#threshold = 1.5
		widths = np.array(list(horedges.flatten()) + list(veredges.flatten()))
		threshold = findthreshold(widths)
		# make edge structure
		edges = np.zeros((nrows,ncols,4))
		for i in range(nrows):
			for j in range(ncols):
				upedge = 1
				if( i>0 and horedges[i-1,j]<threshold ): upedge = 0
				rightedge = 1
				if( j<ncols-1 and veredges[i,j]<threshold ): rightedge = 0
				lowedge = 1
				if( i<nrows-1 and horedges[i,j]<threshold ): lowedge = 0
				leftedge = 1
				if( j>0 and veredges[i,j-1]<threshold ): leftedge = 0
				thisedges = np.array([upedge,rightedge,lowedge,leftedge])
				edges[i,j,:] = thisedges
				# printouts for testing
				#print('row {}, column {}: {}'.format(i,j,thisedges))
		# fill the layout
		layout = filllayout(edges)
		self.layout = layout
		return layout
	
	def finddigits(self):
		### find filled digits
		# returns:
		# numpy grid with digits (0 for no digit)
		if self.image is None:
			raise Exception('Current image is None')
		if self.gridlines is None:
			raise Exception('Current gridlines is None')
		horlines = self.gridlines[0]
		verlines = self.gridlines[1]
		nrows = len(horlines)-1
		ncols = len(verlines)-1
		grid = np.zeros((nrows,ncols), dtype=int)
		# read digit images
		dimages = []
		for digit in [1,2,3,4,5]:
			abspath = os.path.abspath(os.path.dirname(__file__))
			dimage = '../res/number_{}.png'.format(digit)
			dimage = os.path.join(abspath,dimage)
			darray = cv2.imread(dimage)
			darray = cv2.cvtColor(darray, cv2.COLOR_BGR2GRAY)
			darray = np.where(darray>128,0,1)
			darray = darray.astype(np.uint8)
			dimages.append(darray)
		# loop over individual cells
		for i in range(nrows):
			for j in range(ncols):
				margin = 5
				imgcell = self.image[horlines[i]+margin:horlines[i+1]-margin, verlines[j]+margin:verlines[j+1]-margin]
				fillfrac = np.sum(imgcell)/(imgcell.shape[0]*imgcell.shape[1])
				# check if not filled
				if fillfrac < 0.05: continue
				# else try overlap with other digits
				overlaps = np.zeros(5)
				for dindex, dimage in enumerate(dimages):
					dimage = cv2.resize(dimage, (imgcell.shape[1],imgcell.shape[0]))
					overlaps[dindex] = np.sum(np.multiply(imgcell,dimage))
				digit = np.argmax(overlaps)+1
				grid[i,j] = digit
		self.grid = grid
		return self.grid
	
	def findsuguru(self):
		### summary function of all the above, reconstructing the full suguru
		# returns:
		# tuple of (grid array, layout array)
		_ = self.findgridlines()
		_ = self.finddigits()
		_ = self.findlayout()
		return (self.grid, self.layout)
	

def filllayout(edges):
	### fill a suguru layout grid
	# input arguments:
	# - edges: np array of shape (nrows,ncols,4),
	#   where the last dimension encodes the edges and openings
	#   (0 for opening, 1 for edge) in the order up, right, down, left
	# returns:
	# array of shape (nrows,ncols) with group numbers
	nrows = edges.shape[0]
	ncols = edges.shape[1]
	layout = np.zeros((nrows,ncols), dtype=int)
	currentcell = (0,0)
	currentgroup = 1
	while True:
		layout[currentcell] = currentgroup
		added = [currentcell]
		while len(added)>0:
			toadd = []
			for cell in added:
				row = cell[0]
				col = cell[1]
				if( edges[row,col,0]==0 and layout[row-1,col]==0 ): toadd.append((row-1, col))
				if( edges[row,col,1]==0 and layout[row,col+1]==0 ): toadd.append((row, col+1))
				if( edges[row,col,2]==0 and layout[row+1,col]==0 ): toadd.append((row+1, col))
				if( edges[row,col,3]==0 and layout[row,col-1]==0 ): toadd.append((row, col-1))
			for cell in toadd:
				row = cell[0]
				col = cell[1]
				layout[row,col] = currentgroup
			added = toadd
		currentgroup += 1
		# find unfilled layout cells
		temp = np.where(layout<0.5)
		# if no unfilled layout cells, break the loop
		if( len(temp[0])==0 ): break
		# else start new iteration from first unfilled cell
		currentcell = (temp[0][0], temp[1][0])
		continue
	# for use in Suguru class, need to start group numbers from 0
	layout = layout - 1
	return layout

def findthreshold(widths):
	### find thickness threshold
	# input arguments:
	# - widths: a 1D array with values for widths
	# returns:
	# threshold value separating small from big widths
	#plt.figure()
	#plt.hist(widths)
	kmeans = KMeans(n_clusters=2).fit(widths.reshape(len(widths),1))
	centers = kmeans.cluster_centers_
	return np.mean(centers)

	
		
if __name__=='__main__':
	# testing section
	
	filename = '../images/example_2.png'
	
	SIR = SuguruImageReader()
	SIR.loadimage(filename)
	SIR.findsuguru()
	print(SIR.grid)
	print(SIR.layout)
	SIR.drawimage()
	SIR.drawgridlines()