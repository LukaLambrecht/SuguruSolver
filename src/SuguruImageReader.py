# -*- coding: utf-8 -*-

# imports
import os
import numpy as np
import cv2
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.patches as patches


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
		print('Loaded image {}'.format(imagefile))
		if targetsize is not None:
			self.image = cv2.resize(self.image, targetsize)
			self.image = np.where(self.image>128,0,1)
			print('Converted image to size {}'.format(targetsize))
	
	def layoutimage(self):
		### get currently loaded image, but only line structures
		if self.image is None: raise Exception('Current image is None')
		if self.gridlines is None: raise Exception('Current gridlines is None')
		horlines = self.gridlines[0]
		verlines = self.gridlines[1]
		nrows = len(horlines)-1
		ncols = len(verlines)-1
		margin = int((horlines[1]-horlines[0])/10)
		lselfimage = np.copy(self.image)
		for i in range(nrows):
			for j in range(ncols):
				lselfimage[horlines[i]+margin:horlines[i+1]-margin, verlines[j]+margin:verlines[j+1]-margin] = 0
		return lselfimage
	
	def digitimage(self):
		### get currently loaded image, but only digits
		if self.image is None: raise Exception('Current image is None')
		if self.gridlines is None: raise Exception('Current gridlines is None')
		horlines = self.gridlines[0]
		verlines = self.gridlines[1]
		nrows = len(horlines)-1
		ncols = len(verlines)-1
		margin = int((horlines[1]-horlines[0])/10)
		dselfimage = np.zeros(self.image.shape)
		for i in range(nrows):
			for j in range(ncols):
				fragment = self.image[horlines[i]+margin:horlines[i+1]-margin, verlines[j]+margin:verlines[j+1]-margin]
				dselfimage[horlines[i]+margin:horlines[i+1]-margin, verlines[j]+margin:verlines[j+1]-margin] = fragment
		return dselfimage
		
	def drawimage(self, doplot=True, onlylayout=False, onlydigits=False, invert=True, title=None, ticks=False):
		### draw the currently loaded image for visual inspection
		if self.image is None: raise Exception('Current image is None')
		image = np.copy(self.image)
		if onlylayout: image = self.layoutimage()
		if onlydigits: image = self.digitimage()
		if invert: image = np.where(image>0.5,0,1)
		(fig,ax) = plt.subplots()
		ax.imshow(image, cmap='gray')
		if title is not None: ax.set_title(title)
		if not ticks:
			ax.set_xticks([])
			ax.set_yticks([])
		if doplot: plt.show(block=False)
		return (fig,ax)	
		
	def findgridlines(self, nprobes=7, threshold=0.8, doplot=False):
		### find the position of row and column lines
		# returns:
		# tuple of two lists, y-positions of horizontal lines and x-position of vertical lines
		# (including outer lines)
		if self.image is None: raise Exception('Current image is None')
		(imgheight,imgwidth) = self.image.shape
		# define horizontal and vertical probe positions
		horprobes = np.linspace(imgheight/4, imgheight*3/4, num=nprobes).astype(int)
		verprobes = np.linspace(imgwidth/4, imgwidth*3/4, num=nprobes).astype(int)
		horlines = (np.sum(self.image[:,verprobes],axis=1)/nprobes > threshold).nonzero()[0]
		verlines = (np.sum(self.image[horprobes,:],axis=0)/nprobes > threshold).nonzero()[0]
		# reduce lines of non-unitiy thickness to single lines
		filtered_horlines = reduceinds(horlines, threshold=3)
		filtered_verlines = reduceinds(verlines, threshold=3)
		gridlines = (filtered_horlines, filtered_verlines)
		# make plots
		if doplot:
			(fig,ax) = self.drawimage(doplot=False)
			# draw all lines
			thickness = 2
			color = 'r'
			style = '--'
			plt.autoscale(enable=False)
			xmin = 0
			xmax = self.image.shape[1]
			for y in gridlines[0]:
				ax.plot([xmin, xmax], [y, y], linewidth=thickness, color=color, linestyle=style)
			ymin = 0
			ymax = self.image.shape[0]
			for x in gridlines[1]:
				ax.plot([x, x], [ymin, ymax], linewidth=thickness, color=color, linestyle=style)
			ax.set_title('Image with reconstructed grid lines')
		# set and return the result
		self.gridlines = (filtered_horlines, filtered_verlines)
		return self.gridlines
	
	def findlayout(self, doplot=True):
		### find the layout of the grid by checking line thickness
		# returns:
		# numpy grid with layout
		if self.image is None: raise Exception('Current image is None')
		if self.gridlines is None: raise Exception('Current gridlines is None')
		horlines = self.gridlines[0]
		verlines = self.gridlines[1]
		nrows = len(horlines)-1
		ncols = len(verlines)-1
		# make grids of edge thicknesses
		halfwidth = int((horlines[1]-horlines[0])/10)
		horedges = np.zeros((nrows-1,ncols))
		for j in range(ncols):
			xcoord = int((verlines[j]+verlines[j+1])/2.)
			for i in range(nrows-1):
				ycoord = horlines[i+1]
				section = self.image[ycoord-halfwidth:ycoord+halfwidth,xcoord]
				horedges[i,j] = np.sum(section)
		veredges = np.zeros((nrows,ncols-1))
		for i in range(nrows):
			ycoord = int((horlines[i]+horlines[i+1])/2.)
			for j in range(ncols-1):
				xcoord = verlines[j+1]
				section = self.image[ycoord,xcoord-halfwidth:xcoord+halfwidth]
				veredges[i,j] = np.sum(section)
		# find thickness threshold
		widths = np.array(list(horedges.flatten()) + list(veredges.flatten()))
		threshold = findthreshold(widths, doplot=doplot)
		# make a plot with edge thicknesses
		if doplot:
			(fig,ax) = self.drawimage(doplot=False, onlylayout=True)
			# write thickness of horizontal lines
			for j in range(ncols):
				xcoord = int((verlines[j]+verlines[j+1])/2.)
				for i in range(nrows-1):
					ycoord = horlines[i+1]
					value = int(horedges[i,j])
					color = 'r' if value>threshold else 'g'
					ax.text(xcoord, ycoord-halfwidth, str(value), color=color,
					  horizontalalignment='center')
			# write thickness of vertical lines
			for i in range(nrows):
				ycoord = int((horlines[i]+horlines[i+1])/2.)
				for j in range(ncols-1):
					xcoord = verlines[j+1]
					value = int(veredges[i,j])
					color = 'r' if value>threshold else 'g'
					ax.text(xcoord+halfwidth, ycoord, str(value), color=color,
					 verticalalignment='center')
			ax.set_title('Reconstructed line thickness')
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
	
	def finddigits(self, doplot=True):
		### find filled digits
		# returns:
		# numpy grid with digits (0 for no digit)
		if self.image is None: raise Exception('Current image is None')
		if self.gridlines is None: raise Exception('Current gridlines is None')
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
		margin = int((horlines[1]-horlines[0])/10)
		for i in range(nrows):
			for j in range(ncols):
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
		# make plot
		if doplot:
			(fig,ax) = self.drawimage(doplot=False, onlydigits=True)
			# write thickness of horizontal lines
			for j in range(ncols):
				for i in range(nrows):
					if grid[i,j]==0: continue
					xcoord = verlines[j+1]
					ycoord = horlines[i]
					cellanchor = (verlines[j]+margin, horlines[i]+margin)
					cellwidth = verlines[j+1]-verlines[j]-2*margin
					cellheight = horlines[i+1]-horlines[i]-2*margin
					cellbox = patches.Rectangle(cellanchor, cellwidth, cellheight, 
								 linewidth=1, linestyle='--', edgecolor='r', facecolor='none')
					ax.add_patch(cellbox)
					ax.text(xcoord, ycoord, str(grid[i,j]), color='b',
					 horizontalalignment='right', verticalalignment='top')
			ax.set_title('Reconstructed digits')
		self.grid = grid
		return self.grid
	
	def findsuguru(self, doplot=False):
		### summary function of all the above, reconstructing the full suguru
		# returns:
		# tuple of (grid array, layout array)
		if doplot: _ = self.drawimage(title='Original image')
		_ = self.findgridlines(doplot=doplot)
		if doplot:
			_ = self.drawimage(onlylayout=True, title='Layout-only image')
			_ = self.drawimage(onlydigits=True, title='Digit-only image')
		_ = self.finddigits(doplot=doplot)
		_ = self.findlayout(doplot=doplot)
		return (self.grid, self.layout)
	

def reduceinds(inds, threshold=1):
	### reduce set of indices to mean of each subset
	res = []
	currentset = [inds[0]]
	currentidx = 1
	while True:
		if( abs(inds[currentidx]-inds[currentidx-1])<threshold ):
			currentset.append(inds[currentidx])
		else:
			res.append(int(np.mean(np.array(currentset))))
			currentset = [inds[currentidx]]
		if(currentidx == len(inds)-1):
			res.append(int(np.mean(np.array(currentset))))
			break
		else:
			currentidx += 1
			continue
	return res

	
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


def findthreshold(widths, doplot=False):
	### find thickness threshold
	# input arguments:
	# - widths: a 1D array with values for widths
	# returns:
	# threshold value separating small from big widths
	kmeans = KMeans(n_clusters=2).fit(widths.reshape(len(widths),1))
	centers = sorted(kmeans.cluster_centers_.flatten())
	threshold = np.mean(centers)
	if doplot:
		maxwidth = int(np.max(widths))
		bins = np.linspace(-0.5,maxwidth+0.5,num=maxwidth+2)
		fig,ax = plt.subplots()
		ax.hist(widths, bins=bins)
		ymax = ax.get_ylim()[1]
		for i, center in enumerate(centers):
			ax.axvline(x=center, color='b', linestyle='--')
			ax.text(center-0.5, ymax*0.9, 'Cluster {} ({:.2f})'.format(i+1,center),
		      color='b', verticalalignment='top', horizontalalignment='right')
		ax.axvline(x=threshold, color='r', linestyle='--')
		ax.text(threshold-0.5, ymax*0.8, 'Threshold ({:.2f})'.format(threshold),
		      color='r', verticalalignment='top', horizontalalignment='right')
		ax.set_xlabel('Line thickness (pixels)', fontsize=13)
		ax.set_ylabel('Number of lines', fontsize=13)
		ax.set_title('Line thickness thresholding', fontsize=13)
	return threshold

	
		
if __name__=='__main__':
	# testing section
	
	filename = '../images/example_4.jpg'
	
	SIR = SuguruImageReader()
	SIR.loadimage(filename)
	SIR.findsuguru(doplot=True)
	print(SIR.grid)
	print(SIR.layout)