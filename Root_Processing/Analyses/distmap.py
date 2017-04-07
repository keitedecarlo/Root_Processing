import numpy as np
from astropy.io import fits
import time
import scipy.ndimage as imp
import datetime

from scipy import ndimage
from skimage.morphology import skeletonize
import scipy.misc
from scipy.signal import medfilt
from PIL import Image
import os

from timer import timer
from windowrange import windowrange
from remove import remove

def distmap(parameters):
    '''
    SUMMARY: 
    'distmap': associates every soil pixel with an associated root diameter.
    
    USING CODE:
    From the binary root image located in 'image_filename', a contour image (using 
    RootProcess.remove) and a skeletonized radius image will be made.  The skeletonized
    radius image is made by creating a medial axis transform (i.e. skeleton) of the 
    binary image.
    
    Processing is conducted in two stages: in stage one, every contour pixel is associated
    with a radius pixel via closest distance.  In stage two, every soil pixel is then
    associated with a contour pixel via closest distance.  Due to possibly very large sizes and 
    lack of interest in far away soil pixels, a 'maxval' which sets the maximum distance of the
    soil pixel from the root to be evaluated.
        
        
    PARAMETERS:
    1. image_filename: filename of evaluated image.  
    2. output_filename: filename where image is to be saved.
    3. maxval: maximum soil-pixel/root edge-pixel distance, beyond which soil pixels will not 
    be calculated.
    
    '''
    
    image_filename = parameters['image_filename']
    output_filename = parameters['output_filename']
    maxval = parameters['maxval']
    
    
    starttime = time.time()
    scriptname = 'distmap: contours'
    
    timer.start(scriptname)
    
    #image = fits.open(image_filename)[0].data
    #image = Image.open(image_filename)
    image = Image.open(image_filename)
    image = np.array(image)
    image = image > 0
    
    #1. Find edge/contour of roots
    contour_img = remove(image)
    
    #2. ID all non-root pixels
    soilmap = image < 1
    
    #3. Create radius-labeled skeleton (medial axis) of root
    skel = skeletonize(image)
    skel = skel > 0
    rootdist = ndimage.morphology.distance_transform_edt(image)
    rootdist[~skel] = 0
    
    #4. ID position of all contour pixels
    contourpos = np.where(contour_img)
    contourpos_y = contourpos[0]
    contourpos_x = contourpos[1]
    
    #5. ID position of all skeleton pixels
    skelpos = np.where(skel)
    skelpos_y = skelpos[0]
    skelpos_x = skelpos[1]
    
    #6. Contour map where each contour pixel corresponds to closest medial axis
    contour_skel_map = np.zeros(np.shape(image))
    
    #9. ID all soil pixels
    pixelpos = np.where(soilmap)
    pixelpos_y = pixelpos[0]
    pixelpos_x = pixelpos[1]
    
    distmapvals = ndimage.morphology.distance_transform_edt(~image)
    
    
    #9. ID all soil pixels
    if maxval == 'all':
        pixelpos = np.where(soilmap == True)
    else:
        pixelpos = np.where((distmapvals < maxval) & (soilmap == True))
    
    pixelpos_y = pixelpos[0]
    pixelpos_x = pixelpos[1]        

    imdim = np.shape(image)
    
    counter = 0
    pctval = 0
    totalcount = np.shape(contourpos_y)[0]
    
    
    #7. Loop through all contour pixels
    for i in range(np.shape(contourpos_y)[0]):
        [pctval,counter] = timer.progress(counter,pctval,totalcount)

        y = contourpos_y[i]
        x = contourpos_x[i]
    
        #Find distance between pixel and all skeleton pixels
        check = np.sqrt((skelpos_y-y)*(skelpos_y-y)+(skelpos_x-x)*(skelpos_x-x))
        minpos = np.where(check == check.min())
        #ID closest skeleton pixel
        yc = skelpos_y[minpos[0][0]]
        xc = skelpos_x[minpos[0][0]]

        #place in contour-skel map
        contour_skel_map[y,x] = rootdist[yc,xc]
    
    #8. Soil map where each soil pixel corresponds to closest medial axis
    soil_contour_map = np.zeros(np.shape(image))
    
    timer.end(starttime)

    
    starttime = time.time()
    scriptname = 'distmap: soil dist'
    
    timer.start(scriptname)
    
    
    
    counter = 0
    pctval = 0
    totalcount = np.shape(pixelpos_y)[0]
    
    
    for i in range(np.shape(pixelpos_y)[0]):
        [pctval,counter] = timer.progress(counter,pctval,totalcount)

        y = pixelpos_y[i]
        x = pixelpos_x[i]
        
        
        distval = distmapvals[y,x]
        windowsize = 2*(np.floor(distval)+1)

        [y1,y2,x1,x2] = windowrange(y,x,windowsize,imdim)


        contour_w = contour_skel_map[y1:y2,x1:x2]

        contourpos_w = np.where(contour_w)
        contourpos_w_y = contourpos_w[0]
        contourpos_w_x = contourpos_w[1]

        check = np.sqrt((contourpos_w_y-y)*(contourpos_w_y-y)+(contourpos_w_x-x)*(contourpos_w_x-x))
        minpos = np.where(check == check.min())
        yc = contourpos_w_y[minpos[0][0]]
        xc = contourpos_w_x[minpos[0][0]]

        val = contour_w[yc,xc]

        soil_contour_map[y,x] = val
        
    soil_contour_map = Image.fromarray(soil_contour_map)
    soil_contour_map.save(output_filename)
  
    #imghdu = fits.PrimaryHDU(soil_contour_map)
    #hdulist = fits.HDUList([imghdu])
    #hdulist.writeto(output_filename)
    
    timer.end(starttime)