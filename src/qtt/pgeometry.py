# -*- coding: utf-8 -*-
"""

pgeometry
---------

A collection of usefull functions.

For additional options also see
`numpy <http://numpy.scipy.org/>`_ and `matplotlib <http://matplotlib.sourceforge.net/>`_.

:platform: Unix, Windows


Additions:
    Copyright 2012-2016   TNO
Original code:
    Copyright 2011 Pieter Eendebak <pieter.eendebak@gmail.com>

@author: eendebakpt
"""

# %% Load necessary packages
import os
import sys
import tempfile
import math
import time
import warnings
import pickle
import subprocess
import re
import logging
import pkgutil

import numpy as np
import Polygon as polygon3
import scipy.io
import numpy
import scipy.ndimage.morphology as morphology
import scipy.ndimage.filters as filters

from functools import wraps

__version__ = '0.7.0'

# %% Load qt functionality


def qtModules(verbose=0):
    """ Return list of Qt modules loaded """
    _ll = sys.modules.keys()
    qq = [x for x in _ll if x.startswith('Py')]
    if verbose:
        print('qt modules: %s' % str(qq))
    return qq


try:
    _applocalqt = None

    try:
        # by default use qtpy to import Qt
        import qtpy
        _haveqtpy = True

        import qtpy.QtCore as QtCore
        import qtpy.QtGui as QtGui
        import qtpy.QtWidgets as QtWidgets
        from qtpy.QtCore import QObject
        from qtpy.QtCore import Slot
        from qtpy.QtCore import Signal
    except ImportError:
        _haveqtpy = False
        warnings.warn('could not import qtpy, not all functionality available')
        pass

    _ll = sys.modules.keys()
    _pyside = len([_x for _x in _ll if _x.startswith('PySide.QtGui')]) > 0
    _pyqt4 = len([_x for _x in _ll if _x.startswith('PyQt4.QtGui')]) > 0
    _pyqt5 = len([_x for _x in _ll if _x.startswith('PyQt5.QtGui')]) > 0

    def slotTest(txt):
        """ Helper function for Qt slots """
        class slotObject(QtCore.QObject):

            def __init__(self, txt):
                QObject.__init__(self)
                self.txt = txt

            @Slot()
            def slot(self, v=None):
                if v is None:
                    print('slotTest: %s' % self.txt)
                else:
                    print('slotTest: %s: %s' % (self.txt, str(v)))
        s = slotObject(txt)
        return s.slot

    class signalTest(QObject):

        """ Helper function for Qt signals """
        s = Signal()

        def __init__(self):
            QObject.__init__(self)

        def go(self):
            self.s.emit()

except Exception as ex:
    logging.info('pgeometry: load qt: %s' % ex)
    print(ex)
    print('pgeometry: no Qt found')

# %% Load other modules
try:
    import pylab
    import pylab as p

except Exception as inst:
    print(inst)
    print('could not import pylab, not all functionality available...')
    pass

try:
    import matplotlib.pyplot as plt
    import matplotlib
    # needed for 3d plot points, do not remove!
    try:
        from mpl_toolkits.mplot3d import Axes3D
    except BaseException:
        pass
except ModuleNotFoundError as ex:
    warnings.warn(
        'could not find matplotlib, not all functionality available...')
    plt = None
    pass

try:
    import skimage.filters
except ModuleNotFoundError as ex:
    warnings.warn(
        'could not find skimage.filters, not all functionality is available')
    pass


try:
    import cv2
    _haveOpenCV = True
except ModuleNotFoundError:
    _haveOpenCV = False
    warnings.warn('could not find OpenCV, not all functionality is available')
    pass

# %% Utils

try:
    import resource

    def memUsage():
        """ Prints the memory usage in MB

        Uses the resource module

        """
        # http://chase-seibert.github.io/blog/2013/08/03/diagnosing-memory-leaks-python.html
        print('Memory usage: %s (mb)' %
              ((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024., ))
except BaseException:
    def memUsage():
        print('Memory usage: ? (mb)')


def memory():
    """ Return the memory usage in MB

    Returns:
            float: memory usage in mb
    """
    import psutil
    import os
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024. * 1024.)
    return mem


def list_objects(objectype=None, objectclassname='__123', verbose=1):
    """ List all objects in memory of a specific type or with a specific class name

    Args:
        objectype (None or class)
        objectclassname (str)
    Returns:
        ll (list): list of objects found
    """
    import gc
    ll = []
    for ii, obj in enumerate(gc.get_objects()):
        if ii > 1000000:
            break
        valid = False
        if hasattr(obj, '__class__'):
            valid = getattr(obj.__class__, '__name__', 'none').startswith(objectclassname)
        if objectype is not None and not valid:
            if isinstance(obj, objectype):
                valid = True
        if valid:
            if verbose:
                print('list_objects: object %s' % (obj, ))
            ll.append(obj)
    return ll


def package_versions(verbose=1):
    """ Report package versions installed """
    print('numpy.__version__ %s' % numpy.__version__)
    print('scipy.__version__ %s' % scipy.__version__)
    print('matplotlib.__version__ %s' % matplotlib.__version__)
    try:
        import cv2
        print('cv2.__version__ %s' % cv2.__version__)
    except BaseException:
        pass
    try:
        import qtpy
        import qtpy.QtCore
        print('qtpy.API_NAME %s' % (qtpy.API_NAME))
        print('qtpy.QtCore %s' % (qtpy.QtCore))
        print('qtpy.QtCore.__version__ %s' % (qtpy.QtCore.__version__))
    except BaseException:
        pass
    try:
        import sip
        print('sip %s' % sip.SIP_VERSION_STR)
    except BaseException:
        pass


def freezeclass(cls):
    """ Decorator to freeze a class

    This means that no attributes can be added to the class after instantiation.
    """
    cls.__frozen = False

    def frozensetattr(self, key, value):
        if self.__frozen and not hasattr(self, key):
            print("Class {} is frozen. Cannot set {} = {}"
                  .format(cls.__name__, key, value))
        else:
            object.__setattr__(self, key, value)

    def init_decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self.__frozen = True
        return wrapper

    cls.__setattr__ = frozensetattr
    cls.__init__ = init_decorator(cls.__init__)

    return cls


def static_var(varname, value):
    """ Helper function to create a static variable

    Args:
        varname (str)
        value (anything)
    """
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate


@static_var("time", {'default': 0})
def tprint(string, dt=1, output=False, tag='default'):
    """ Print progress of a loop every dt seconds

    Args:
        string (str): text to print
        dt (float): delta time in seconds
        output (bool): if True return whether output was printed or not
        tag (str): optional tag for time
    Returns:
        output (bool)

    """
    if (time.time() - tprint.time.get(tag, 0)) > dt:
        print(string)
        tprint.time[tag] = time.time()
        if output:
            return True
        else:
            return
    else:
        if output:
            return False
        else:
            return


def partiala(method, **kwargs):
    """ Function to perform functools.partial on named arguments """
    raise Exception('Use functools.partial instead')

    def t(x):
        return method(x, **kwargs)
    return t


def setFontSizes(labelsize=20, fsize=17, titlesize=None, ax=None,):
    """ Update font sizes for a matplotlib plot """
    if ax is None:
        ax = plt.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(fsize)
    for tick in ax.yaxis.get_major_ticks():
        tick.label.set_fontsize(fsize)

    for x in [ax.xaxis.label, ax.yaxis.label]:  # ax.title,
        x.set_fontsize(labelsize)

    plt.tick_params(axis='both', which='major', labelsize=fsize)

    if titlesize is not None:
        ax.title.set_fontsize(titlesize)

    plt.draw()


def plotCostFunction(fun, x0, fig=None, marker='.', scale=1, c=None):
    """ Plot a cost function on specified data points

    Example with variation of Booth's function:

    >>> fun = lambda x: 2*(x[0]+2*x[1]-7)**2 + (2*x[0]+x[1]-5)**2
    >>> plotCostFunction(fun, np.array([1,3]), fig=100, marker='-')

    """
    x0 = np.array(x0).astype(float)
    nn = x0.size
    if fig is not None:
        plt.figure(fig)

    scale = np.array(scale)
    if scale.size == 1:
        scale = scale * np.ones(x0.size)
    tt = np.arange(-1, 1, 5e-2)

    for ii in range(nn):
        val = np.zeros(tt.size)
        for jj in range(tt.size):
            x = x0.copy()
            x[ii] += scale[ii] * tt[jj]
            val[jj] = fun(x)
        if c is None:
            plt.plot(tt, val, marker)
        else:
            plt.plot(tt, val, marker, color=c[ii])
    plt.xlabel('Scaled variables')
    plt.ylabel('Value of cost function')


class fps_t:

    def __init__(self, nn=40):
        """ Class for framerate measurements

        Args:
            nn (int): number of time measurements to store
        Example usage:

        >>> fps = fps_t(nn=8)
        >>> for kk in range(12):
        ...       fps.addtime(.2*kk )
        >>> fps.show()
        framerate: 5.000
        """
        self.n = nn
        self.tt = np.zeros(self.n)
        self.x = np.zeros(self.n)
        self.ii = 0

    def __repr__(self):
        ss = 'fps_t: buffer size %d, framerate %.3f [fps]' % (
            self.n, self.framerate())
        return ss

    def addtime(self, t, x=0):
        """ Add a timestamp to the object """
        self.ii = self.ii + 1
        iim = self.ii % self.n
        self.tt[iim] = t
        self.x[iim] = x

    def value(self):
        """ Return mean of current values """
        return self.x.mean()

    def iim(self):
        """ Return index modulo number of elements """
        return self.ii % self.n

    def framerate(self):
        """ Return the current framerate """
        iim = self.ii % self.n
        iimn = (self.ii + 1) % self.n
        dt = self.tt[iim] - self.tt[iimn]
        if dt == 0:
            return np.NaN
        fps = float(self.n - 1) / dt
        return fps

    def loop(self, s=''):
        """ Helper function """
        self.addtime(time.time())
        self.showloop(s='')

    def showloop(self, dt=2, s=''):
        """ Print current framerate """
        fps = self.framerate()
        if len(s) == 0:
            tprint('loop %d: framerate: %.1f [fps]' % (self.ii, fps), dt=dt)
        else:
            tprint(
                '%s: loop %d: framerate: %.1f [fps]' % (s, self.ii, fps), dt=dt)

    def show(self):
        """ Print the current framerate """
        fps = self.framerate()
        print('framerate: %.3f' % fps)


def mkdirc(d):
    """ Similar to mkdir, but no warnings if the directory already exists """
    try:
        os.mkdir(d)
    except BaseException:
        pass
    return d


def projectiveTransformation(H, x):
    """ Apply a projective transformation to a kxN array

    >>> y = projectiveTransformation( np.eye(3), np.random.rand( 2, 10 ))
    """
    k = x.shape[0]
    kout = H.shape[0] - 1
    xx = x.transpose().reshape((-1, 1, k))

    if (xx.dtype is np.integer or xx.dtype == 'int64'):
        xx = xx.astype(np.float32)
    if xx.size > 0:
        ww = cv2.perspectiveTransform(xx, H)
        ww = ww.reshape((-1, kout)).transpose()
        return ww
    else:
        return copy.copy(x)


def rottra2mat(rot, tra):
    """ create 4x4 matrix from 3x3 rot and 1x3 tra """
    out = np.eye(4)
    out[0:3, 0:3] = rot
    out[0:3, 3] = tra.transpose()
    return out


def breakLoop(wk=None, dt=0.001, verbose=0):
    """ Break a loop using OpenCV image feedback """
    if wk is None:
        wk = cv2.waitKey(1)
    time.sleep(dt)

    wkm = wk % 256
    if wkm == 27 or wkm == ord('q') or wk == 1048689:
        if verbose:
            print('breakLoop: key q pressed, quitting loop')
        return True
    return False


def hom(x):
    """ Create affine to homogeneous coordinates

    Args:
        x (kxN array): affine coordinates
    Returns:
        h ( (k+1xN) array): homogeneous coordinates
    """
    nx = x.shape[1]
    return np.vstack((x, np.ones(nx)))


def dehom(x):
    """ Convert homogeneous points to affine coordinates """
    return x[0:-1, :] / x[-1, :]


def null(a, rtol=1e-5):
    """ Calculate null space of a matrix """
    u, s, v = np.linalg.svd(a)
    rank = (s > rtol * s[0]).sum()
    return rank, v[rank:].T.copy()


def intersect2lines(l1, l2):
    """ Calculate intersection between 2 lines

    Args:
        l1 (array): first line in homogeneous format
        l2 (array): first line in homogeneous format
    Returns:
        array: intersection in homogeneous format. To convert to affine coordinates use `dehom`
    """
    r = null(np.vstack((l1, l2)))
    return r[1]


def runcmd(cmd, verbose=0):
    """ Run command and return output """
    output = subprocess.check_output(cmd, shell=True)
    return output

# %% Geometry functions


def angleDiff(x, y):
    """ Return difference between two angles in radians modulo 2* pi

    >>> d=angleDiff( 0.01, np.pi+0.02)
    >>> d=angleDiff( 0.01, 2*np.pi+0.02)
    """
    return np.abs(((x - y + np.pi) % (2 * np.pi)) - np.pi)


def angleDiffOri(x, y):
    """ Return difference between two angles in radians modulo pi

    >>> d=angleDiff( 0.01, np.pi+0.02)
    >>> d=angleDiff( 0.01, 2*np.pi+0.02)
    """
    return np.abs(((x - y + np.pi / 2) % (np.pi)) - np.pi / 2)


def opencvpose2attpos(rvecs, tvecs):
    tvec = np.array(tvecs).flatten()
    rvec = np.array(rvecs).flatten()
    R, tmp = cv2.Rodrigues(rvec)
    att = RBE2euler(R)
    pos = -R.transpose().dot(np.array(tvec.reshape((3, 1))))
    return att, pos


def opencv2TX(rvecs, tvecs):
    """ Convert OpenCV pose to homogenous transform """
    T = np.array(np.eye(4))
    R = cv2.Rodrigues(rvecs)[0]
    T[0:3, 0:3] = R
    T[0:3, 3:4] = tvecs
    return T


def opencv2T(rvec, tvec):
    """ Convert OpenCV pose to homogenous transform """
    T = np.array(np.eye(4))
    T[0:3, 0:3] = cv2.Rodrigues(rvec)[0]
    T[0:3, 3] = tvec
    return T


def T2opencv(T):
    """ Convert transformation to OpenCV rvec, tvec pair

    Example
    -------
    >>> rvec, tvec = T2opencv(np.eye(4))

    """
    rvec = cv2.Rodrigues(T[0:3, 0:3])[0]
    tvec = T[0:3, 3]
    return rvec, tvec


def euler2RBE(theta):
    """ Convert Euler angles to rotation matrix

      Example
      -------
      >>> np.set_printoptions(precision=4, suppress=True)
      >>> euler2RBE( [0,0,np.pi/2] )
      array([[ 0., -1.,  0.],
             [ 1.,  0.,  0.],
             [-0.,  0.,  1.]])

    """
    cr = math.cos(theta[0])
    sr = math.sin(theta[0])
    cp = math.cos(theta[1])
    sp = math.sin(theta[1])
    cy = math.cos(theta[2])
    sy = math.sin(theta[2])

    out = np.array([cp * cy, sr * sp * cy - cr * sy, cr * sp * cy + sr * sy,
                    cp * sy, sr * sp * sy + cr * cy, cr * sp * sy - sr * cy, -sp, sr * cp, cr * cp])
    return out.reshape((3, 3))


def RBE2euler(Rbe):
    """ Convert rotation matrix to Euler angles """
    out = np.zeros([3, 1])
    out[0, 0] = math.atan2(Rbe[2, 1], Rbe[2, 2])
    out[1, 0] = -math.asin(Rbe[2, 0])
    out[2, 0] = math.atan2(Rbe[1, 0], Rbe[0, 0])
    return out

# %% Helper functions


def pg_rotation2H(R):
    """ Convert rotation matrix to homogenous transform matrix """
    X = np.array(np.eye((R.shape[0] + 1)))
    X[0:-1, 0:-1] = R
    return X


def directionMean(vec):
    """ Calculate the mean of a set of directions

    The initial direction is determined using the oriented direction. Then a non-linear optimization is done.

    >>> vv=np.array( [[1,0],[1,0.1], [-1,.1]])
    >>> a=directionMean(vv)

    """
    def dist(a, vec):
        phi = np.arctan2(vec[:, 0], vec[:, 1])
        x = a - phi
        x = np.mod(x + np.pi / 2, np.pi) - np.pi / 2
        cost = np.linalg.norm(x)
        return cost
    Nfeval = 1

    def callbackF(Xi):
        global Nfeval
        print(Xi)
        print('{0:4d}   {1: 3.6f}'.format(Nfeval, Xi[0], dist(Xi[0], vec)))
        Nfeval += 1

    m = vec.mean(axis=0)
    a0 = np.arctan2(m[0], m[1])

    def ff(a): return dist(a, vec)

    r = scipy.optimize.minimize(
        ff, a0, callback=None, options=dict({'disp': False}))
    a = r.x
    return a


def circular_mean(weights, angles):
    """ Calculate circular mean of a set of 2D vectors """
    x = y = 0.
    for angle, weight in zip(angles, weights):
        x += math.cos(math.radians(angle)) * weight
        y += math.sin(math.radians(angle)) * weight

    mean = math.degrees(math.atan2(y, x))
    return mean


def dir2R(d, a=None):
    """ Convert direction to rotation matrix

    Note: numerically not stable near singular points!

    Arguments:
        d (numpy array of size 3): direction to rotation to a
        a (numpy array of size 3): target direction
    Returns:
        R (3x3 numpy array): matrix R such that R*a = d

    Example:

    >>> d = np.array([0, 1, 0]); a = np.array([0, -1, 0])
    >>> R = dir2R(d, a)

    Pieter Eendebak <pieter.eendebak@tno.nl>
    """

    # set target vector
    if a is None:
        a = np.array([0, 0, 1])

    # normalize
    b = d.reshape((3, 1)) / np.linalg.norm(d)
    a = a.reshape((3, 1))

    c = np.cross(a.flat, b.flat)

    if np.linalg.norm(c) < 1e-12 and a.T.dot(b) < .01:
        #  deal with singular case
        if(np.linalg.norm(a[1:]) < 1e-4):
            R0 = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
        else:
            R0 = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
        a = R0.dot(a)
        bt = (a + b) / np.linalg.norm(a + b)
        R = np.eye(3) - 2 * a.dot(a.T) - 2 * \
            (bt.dot(bt.T)).dot(np.eye(3) - 2 * a.dot(a.T))
        R = R.dot(R0)
    else:
        bt = (a + b) / np.linalg.norm(a + b)

        R = np.eye(3) - 2 * a.dot(a.T) - 2 * \
            (bt.dot(bt.T)).dot(np.eye(3) - 2 * a.dot(a.T))

    return R


def frame2T(f):
    """ Convert frame into 4x4 transformation matrix """
    T = np.array(np.eye(4))
    T[0:3, 0:3] = euler2RBE(f[3:7])
    T[0:3, 3] = f[0:3].reshape(3, 1)
    return T


@static_var("b", np.array(np.zeros((2, 2))))
def rot2D(phi):
    """ Return 2x2 rotation matrix from angle

    Arguments
    ---------
    phi : float
        Angle in radians
    Returns
    -------
        R : array
            The 2x2 rotation matrix

    Examples
    --------
    >>> R = rot2D(np.pi)

    """
    r = rot2D.b.copy()
    c = math.cos(phi)
    s = math.sin(phi)
    r.itemset(0, c)
    r.itemset(1, -s)
    r.itemset(2, s)
    r.itemset(3, c)
    return r


def pg_rotx(phi):
    """ Rotate around the x-axis with angle """
    c = math.cos(phi)
    s = math.sin(phi)
    R = np.zeros((3, 3))
    R.flat = [1, 0, 0, 0, c, -s, 0, s, c]
    return R


def pcolormesh_centre(x, y, im, *args, **kwargs):
    """ Wrapper for pcolormesh to plot pixel centres at data points """
    dx = np.diff(x)
    dy = np.diff(y)
    dx = np.hstack((dx[0], dx, dx[-1]))
    dy = np.hstack((dy[0], dy, dy[-1]))
    xx = np.hstack((x, x[-1] + dx[-1])) - dx / 2
    yy = np.hstack((y, y[-1] + dy[-1])) - dy / 2
    plt.pcolormesh(xx, yy, im, *args, **kwargs)


def imshowz(im, *args, **kwargs):
    """ Show image with interactive z-values """
    plt.imshow(im, *args, **kwargs)

    sz = im.shape
    numrows, numcols = sz[0], sz[1]

    def format_coord(x, y):
        col = int(x + 0.5)
        row = int(y + 0.5)
        if col >= 0 and col < numcols and row >= 0 and row < numrows:
            z = im[row, col]
            try:
                if len(z) == 1:
                    return 'x=%1.4f, y=%1.4f, z=%1.4f' % (x, y, z)
                else:
                    return 'x=%1.4f, y=%1.4f, z=%s' % (x, y, str(z))
            except BaseException:
                return 'x=%1.4f, y=%1.4f, z=%s' % (x, y, str(z))
        else:
            return 'x=%1.4f, y=%1.4f' % (x, y)

    ax = plt.gca()
    ax.format_coord = format_coord


def pg_scaling(scale, cc=None):
    """ Create scaling with specified centre


    Example
    -------
    >>> pg_scaling( [1.,2])
    array([[ 1.,  0.,  0.],
           [ 0.,  2.,  0.],
           [ 0.,  0.,  1.]])

    """
    scale = np.array(scale)
    scale = np.hstack((scale, 1))
    H = np.diag(scale)
    if cc is not None:
        cc = np.array(cc).flatten()
        H = pg_transl2H(cc).dot(H).dot(pg_transl2H(-cc))

    return H


def pg_transl2H(tr):
    """ Convert translation to homogeneous transform matrix

    >>> pg_transl2H( [1,2])
    array([[ 1.,  0.,  1.],
            [ 0.,  1.,  2.],
            [ 0.,  0.,  1.]])

    """
    sh = np.array(tr)
    H = np.eye(sh.size + 1)
    H[0:-1, -1] = sh.flatten()
    H = np.array(H)
    return H


def setregion(im, subim, pos, mask=None, clip=False):
    """ Set region in Numpy image

    Arguments
    ---------
        im : Numpy array
            image to fill region in
        subim : Numpy array
            subimage
        pos: array
            position to place image
        mask (None or array): mask to use for the subimage
        clip (bool): if True clip the subimage where necessary to fit
    """
    h = subim.shape[0]
    w = subim.shape[1]
    x1 = int(pos[0])
    y1 = int(pos[1])
    x2 = int(pos[0]) + w
    y2 = int(pos[1]) + h
    if clip:
        x1 = max(x1, 0)
        y1 = max(y1, 0)
        x2 = min(x2, im.shape[1])
        y2 = min(y2, im.shape[0])
        w = max(0, x2 - x1)
        h = max(0, y2 - y1)
    if mask is None:
        if len(im.shape) == len(subim.shape):
            im[y1:y2, x1:x2, ...] = subim[0:h, 0:w]
        else:
            im[y1:y2, x1:x2, ...] = subim[0:h, 0:w, np.newaxis]
    else:

        if len(im.shape) > len(mask.shape):
            im[y1:y2, x1:x2] = im[y1:y2, x1:x2] * \
                (1 - mask[:, :, np.newaxis]) + (subim * mask[:, :, np.newaxis])
        else:
            if len(im.shape) == len(subim.shape):
                im[y1:y2, x1:x2, ...] = im[y1:y2, x1:x2, ...] * \
                    (1 - mask[:, :]) + (subim * mask[:, :])
            else:
                im[y1:y2, x1:x2, ...] = im[y1:y2, x1:x2, ...] * \
                    (1 - mask[:, :]) + (subim[:, :, np.newaxis] * mask[:, :])

    return im


def region2poly(rr):
    """ Convert a region (bounding box xxyy) to polygon """
    if isinstance(rr, tuple) or isinstance(rr, list):
        # x,y,x2,y2 format
        rr = np.array(rr).reshape((2, 2)).transpose()
        poly = np.array([rr[:, 0:1], np.array([[rr[0, 1]], [rr[1, 0]]]), rr[
                        :, 1:2], np.array([[rr[0, 0]], [rr[1, 1]]]), rr[:, 0:1]]).reshape((5, 2)).T
        return poly
    poly = rr.flat[[0, 1, 1, 0, 0, 2, 2, 3, 3, 2]].reshape((2, 5))

    return poly


def plotLabels(xx, *args, **kwargs):
    """ Plot labels next to points

    Args:
        xx (2xN array): points to plot
        *kwargs: arguments past to plotting function
    Example:
    >>> xx=np.random.rand(2, 10)
    >>> fig=plt.figure(10); plt.clf()
    >>> _ = plotPoints(xx, '.b'); _ = plotLabels(xx)
    """

    if len(np.array(xx).shape) == 1 and xx.shape[0] == 2:
        xx = xx.reshape((2, 1))
    if xx.shape[0] > 2 and xx.shape[1] == 2:
        xx = xx.T
    if len(args) == 0:
        v = range(0, xx.shape[1])
        lbl = ['%d' % i for i in v]
    else:
        lbl = args[0]
        if isinstance(lbl, int):
            lbl = [str(lbl)]
        elif isinstance(lbl, str):
            lbl = [str(lbl)]
    nn = xx.shape[1]
    ax = plt.gca()
    th = [None] * nn
    for ii in range(nn):
        lbltxt = str(lbl[ii])
        th[ii] = ax.annotate(lbltxt, xx[:, ii], **kwargs)
    return th


def plotPoints(xx, *args, **kwargs):
    """ Plot 2D or 3D points

    Args:
        xx (array): array of points to plot
        *args: arguments passed to the plot function of matplotlib
        **kwargs:  arguments passed to the plot function of matplotlib
    Example:
    >>> plotPoints(np.random.rand(2,10), '.-b')

    """
    if xx.shape[0] == 2:
        h = plt.plot(xx[0, :], xx[1, :], *args, **kwargs)
    elif xx.shape[0] == 3:
        h = plt.plot(xx[0, :], xx[1, :], xx[2, :], *args, **kwargs)
    if xx.shape[0] == 1:
        h = plt.plot(xx[0, :], *args, **kwargs)
    else:
        h = None
    return h


def plot2Dline(line, *args, **kwargs):
    """ Plot a 2D line in a matplotlib figure

    Args:
        line (3x1 array): line to plot

    >>> plot2Dline([-1,1,0], 'b')
    """
    if np.abs(line[1]) > .001:
        xx = plt.xlim()
        xx = np.array(xx)
        yy = (-line[2] - line[0] * xx) / line[1]
        plt.plot(xx, yy, *args, **kwargs)
    else:
        yy = np.array(plt.ylim())
        xx = (-line[2] - line[1] * yy) / line[0]
        plt.plot(xx, yy, *args, **kwargs)


# %%

def scaleImage(image, display_min=None, display_max=None):
    """ Scale any image into uint8 range

    Args:
        image (numpy array): input image
        display_min (float): value to map to min output range
        display_max (float): value to map to max output range
    Returns:
        image (numpy array): the scaled image

    Example:
        >>> im=scaleImage(255*np.random.rand( 30,40), 40, 100)

    Code modified from: https://stackoverflow.com/questions/14464449/using-numpy-to-efficiently-convert-16-bit-image-data-to-8-bit-for-display-with?noredirect=1&lq=1
    """
    image = np.array(image, copy=True)

    if display_min is None:
        display_min = np.percentile(image, .15)
    if display_max is None:
        display_max = np.percentile(image, 99.85)
        if display_max == display_min:
            display_max = np.max(image)
    image.clip(display_min, display_max, out=image)
    if image.dtype == np.uint8:
        image -= int(display_min)
        image = image.astype(np.float)
        image //= (display_max - display_min) / 255.
    else:
        image -= display_min
        image //= (display_max - display_min) / 255.
    image = image.astype(np.uint8)
    return image


def auto_canny(image, sigma=0.33):
    """ Canny edge detection with automatic parameter detection

    >>> imc=auto_canny(np.zeros( (200,300)).astype(np.uint8))

    Arguments
    ---------
        image : array
            input image
    Returns
    -------
        edged : array
            detected edges

    Code from: http://www.pyimagesearch.com/2015/04/06/zero-parameter-automatic-canny-edge-detection-with-python-and-opencv/
    """
    # compute the median of the single channel pixel intensities
    v = np.median(image)
    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)
    return edged

# %% Plotting functions


def orthogonal_proj(zfront, zback):
    """ see http://stackoverflow.com/questions/23840756/how-to-disable-perspective-in-mplot3d """
    a = (zfront + zback) / (zfront - zback)
    b = -2 * (zfront * zback) / (zfront - zback)
    return numpy.array([[1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, a, b],
                        [0, 0, -1e-9, zback]])


def plotPoints3D(xx, *args, **kwargs):
    """ Plot 3D points

    Arguments
    ---------
    xx: 3xN array
        the 3D data points

    Example
    -------
    >> ax=plotPoints3D(np.random.rand(3, 1) ,'.r', markersize=10, fig=12)

    """

    fig = kwargs.get('fig', None)
    verbose = kwargs.get('verbose', 0)
    if 'fig' in kwargs.keys():
        kwargs.pop('fig')
    if 'verbose' in kwargs.keys():
        kwargs.pop('verbose')

    if verbose:
        print('plotPoints3D: using fig %s' % fig)
        print('plotPoints3D: using args %s' % args)
    if fig is None:
        ax = p.gca()
    else:
        fig = p.figure(fig)
        ax = fig.gca(projection='3d')
    r = ax.plot(np.ravel(xx[0, :]), np.ravel(xx[1, :]),
                np.ravel(xx[2, :]), *args, **kwargs)
    p.draw()
    return ax

# %%


def polyarea(p):
    """ Return signed area of polygon

    Arguments
    ---------
        p : Nx2 numpy array or list of vertices
            vertices of polygon
    Returns
    -------
        area : float
            area of polygon

    >>> polyarea( [ [0,0], [1,0], [1,1], [0,2]] )
    1.5
    """
    if len(p) <= 1:
        return 0
    if isinstance(p, numpy.ndarray):
        val = 0
        for x in range(len(p)):
            x0 = p[x, 0]
            y0 = p[x, 1]
            xp = x + 1
            if xp >= len(p):
                xp = 0
            x1 = p[xp, 0]
            y1 = p[xp, 1]
            val += 0.5 * (x0 * y1 - x1 * y0)
        return val

    def polysegments(p):
        """ Helper functions """
        if isinstance(p, list):
            return zip(p, p[1:] + [p[0]])
        else:
            return zip(p, np.vstack((p[1:], p[0:1])))
    return 0.5 * abs(sum(x0 * y1 - x1 * y0 for ((x0, y0), (x1, y1)) in polysegments(p)))


def polyintersect(x1, x2):
    """ Intersection of two polygons

    >>> x1=np.array([(0, 0), (1, 1), (1, 0)] )
    >>> x2=np.array([(1, 0), (1.5, 1.5), (.5, 0.5)])
    >>> x=polyintersect(x1, x2)
    >>> _=plt.figure(10); plt.clf()
    >>> plotPoints(x1.T, '.-r' )
    >>> plotPoints(x2.T, '.-b' )
    >>> plotPoints(x.T, '.-g' , linewidth=2)

    """

    p1 = polygon3.Polygon(x1)
    p2 = polygon3.Polygon(x2)
    p = p1 & p2
    x = np.array(p)
    x = x.reshape((-1, 2))
    return x

# %%


def opencv_draw_points(bgr, imgpts, drawlabel=True, radius=3, color=(255, 0, 0), thickness=-1, copyimage=True):
    """ Draw points on image with opencv

    Arguments
    ---------
        bgr : numpy array
            image to draw points into
        impts : array
            locations of points to plot

    """
    if copyimage:
        out = bgr.copy()
    else:
        out = bgr
    fscale = .5 + .5 * (radius * 0.2)
    fthickness = int(fscale + 1)
    for i, pnt in enumerate(imgpts):
        tpnt = tuple(pnt.ravel())
        cv2.circle(out, tpnt, radius, color, thickness)
        if(drawlabel):
            cv2.putText(
                out, '%d' % (i + 1), tpnt, cv2.FONT_HERSHEY_SIMPLEX, fscale, color, fthickness)
    return out


def enlargelims(factor=1.05):
    """ Enlarge the limits of a plot
    Example:
      >>> enlargelims(1.1)

    """
    xl = plt.xlim()
    d = (factor - 1) * (xl[1] - xl[0]) / 2
    xl = (xl[0] - d, xl[1] + d)
    plt.xlim(xl)
    yl = plt.ylim()
    d = (factor - 1) * (yl[1] - yl[0]) / 2
    yl = (yl[0] - d, yl[1] + d)
    plt.ylim(yl)


def finddirectories(p, patt):
    """ Get a list of files """
    lst = os.listdir(p)
    rr = re.compile(patt)
    lst = [l for l in lst if re.match(rr, l)]
    lst = [l for l in lst if os.path.isdir(os.path.join(p, l))]
    return lst


def _walk_calc_progress(progress, root, dirs):
    """ Helper function """
    prog_start, prog_end, prog_slice = 0.0, 1.0, 1.0

    current_progress = 0.0
    parent_path, current_name = os.path.split(root)
    data = progress.get(parent_path)
    if data:
        prog_start, prog_end, subdirs = data
        i = subdirs.index(current_name)
        prog_slice = (prog_end - prog_start) / len(subdirs)
        current_progress = prog_slice * i + prog_start

        if i == (len(subdirs) - 1):
            del progress[parent_path]

    if dirs:
        progress[root] = (current_progress, current_progress + prog_slice, dirs)

    return current_progress


def findfilesR(p, patt, show_progress=False):
    """ Get a list of files (recursive)

    Args:

        p (string): directory
        patt (string): pattern to match
        show_progress (bool)
    Returns:
        lst (list of str)
    """
    lst = []
    rr = re.compile(patt)
    progress = {}
    for root, dirs, files in os.walk(p, topdown=True):
        frac = _walk_calc_progress(progress, root, dirs)
        if show_progress:
            tprint('findfilesR: %s: %.1f%%' % (p, 100 * frac))
        lst += [os.path.join(root, f) for f in files if re.match(rr, f)]
    return lst


def signedsqrt(val):
    """ Signed square root function

    >>> signedsqrt([-4.,4,0])
    array([-2.,  2.,  0.])
    >>> signedmin(-10, 5)
    -5
    """
    val = np.sign(val) * np.sqrt(np.abs(val))
    return val


def signedmin(val, w):
    """ Signed minimum value function

    >>> signedmin(-3, 5)
    -3
    >>> signedmin(-10, 5)
    -5
    """
    val = np.minimum(val, abs(w))
    val = np.maximum(val, -abs(w))
    return val


def smoothstep(x, x0=0, alpha=1):
    """ Smooth step function

    >>> t=np.arange(0,600,1.)
    >>> _ = plt.plot(t, smoothstep(t, 300, alpha=1./100),'.b')

    """
    x = alpha * (x - x0)
    f = ((x / np.sqrt(1 + x * x)) + 1) / 2
    return f


def logistic(x, x0=0, alpha=1):
    """ Simple logistic function

    Args:
        x (float or array)

    >>> t=np.arange(0,600,1.)
    >>> _ = plt.plot(t, logistic(t, 300, alpha=1./100),'.b')

    """
    f = 1 / (1 + np.exp(-2 * alpha * (x - x0)))
    return f


def findfiles(p, patt, recursive=False):
    """ Get a list of files """
    if recursive:
        return findfilesR(p, patt)
    lst = os.listdir(p)
    rr = re.compile(patt)
    lst = [l for l in lst if re.match(rr, l)]
    return lst

# %%


def blur_measure(im, verbose=0):
    """ Calculate bluriness for an image

    Args:
        im (array): input image
    """

    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    # compute the variance of laplacian
    fm = cv2.Laplacian(gray, cv2.CV_64F).var()
    if verbose:
        print('calculate_blur: %.3f' % fm)
    return fm


def gaborFilter(ksize, sigma, theta, Lambda=1, psi=0, gamma=1, cut=None):
    """ Create a Gabor filter of specified size

    Parameters
    -----
    ksize : integer
        kernel size in pixels
    sigma, theta, Lambda, psi: float
        parameters of Gabor function
    cut: boolean
        if True cut off the angular component after specified distance (in radians)

    Returns
    ------

    g : array
        constructed kernel

    Example
    -------

    >>> g = gaborFilter(ksize=15, sigma=2,theta=2,Lambda=1, gamma=1)

    """
    h = ((ksize - 1) // 2)
    x, y = np.meshgrid(range(-h, h + 1), range(-h, h + 1))
    sigma_x = sigma
    # print('gamma %s' % gamma)
    sigma_y = float(sigma) / gamma
    # Rotation
    x_theta = x * np.cos(theta) + y * np.sin(theta)
    y_theta = -x * np.sin(theta) + y * np.cos(theta)

    xt = 2 * np.pi / Lambda * x_theta
    if cut is not None:
        pass
        xt = np.minimum(xt, cut)
        xt = np.maximum(xt, -cut)

    gb = np.exp(-.5 * (x_theta**2 / sigma_x**2 + y_theta**2 / sigma_y**2)) * np.cos(xt + psi)
    return gb

# %%


def detect_local_minima(arr, thr=None):
    """
    Takes an array and detects the troughs using the local maximum filter.
    Returns a boolean mask of the troughs (i.e. 1 when
    the pixel's value is the neighborhood maximum, 0 otherwise)

    Args:
        arr (array): input array

    """
    # http://stackoverflow.com/questions/3684484/peak-detection-in-a-2d-array/3689710#3689710

    # define an connected neighborhood
    # http://www.scipy.org/doc/api_docs/SciPy.ndimage.morphology.html#generate_binary_structure
    neighborhood = morphology.generate_binary_structure(len(arr.shape), 2)
    # apply the local minimum filter; all locations of minimum value
    # in their neighborhood are set to 1
    # http://www.scipy.org/doc/api_docs/SciPy.ndimage.filters.html#minimum_filter
    local_min = (filters.minimum_filter(arr, footprint=neighborhood) == arr)
    # local_min is a mask that contains the peaks we are
    # looking for, but also the background.
    # In order to isolate the peaks we must remove the background from the mask.
    #
    # we create the mask of the background
    background = (arr == 0)
    #
    # a little technicality: we must erode the background in order to
    # successfully subtract it from local_min, otherwise a line will
    # appear along the background border (artifact of the local minimum filter)
    # http://www.scipy.org/doc/api_docs/SciPy.ndimage.morphology.html#binary_erosion
    eroded_background = morphology.binary_erosion(
        background, structure=neighborhood, border_value=1)
    #
    # we obtain the final mask, containing only peaks,
    # by removing the background from the local_min mask
    detected_minima = local_min - eroded_background
    if thr is not None:
        detected_minima[arr > thr] = 0
    return np.where(detected_minima)


# %% Matlab compatibility functions

def fullpath(*args):
    """ Return full path from a list """
    p = os.path.join(*args)
    return p


def ginput(n=1, drawmode='', **kwargs):
    """ Select points from figure

    Press middle mouse button to stop selection

    Arguments:
        n - number of points to select
        drawmode - style to plot selected points
        kwargs : arguments passed to plot function
    """
    xx = np.zeros((2, 0))
    for ii in range(0, n):
        x = pylab.ginput(1)
        if len(x) == 0:
            break
        x = np.array(x).T
        xx = np.hstack((xx, x))
        if drawmode is not None:
            plt.plot(xx[0, :].T, xx[1, :].T, drawmode, **kwargs)
            plt.draw()
    plt.pause(1e-3)
    return xx


def save(pkl_file, *args):
    """ Save objects to file

    Arguments
    ---------
    pkl_file : string
         filename
    *args : anything
         Python objects to save
    """

    # save data to disk
    # pdb.set_trace()
    output = open(pkl_file, 'wb')
    pickle.dump(args, output, protocol=2)
    output.close()


def load(pkl_file):
    """ Load objects from file """
    try:
        output = open(pkl_file, 'rb')
        data2 = pickle.load(output)
        output.close()
    except BaseException:
        if sys.version_info.major >= 3:
            # if pickle file was saved in python2 we might fix issues with a different encoding
            output = open(pkl_file, 'rb')
            data2 = pickle.load(output, encoding='latin')
            # pickle.load(pkl_file, fix_imports=True, encoding="ASCII", errors="strict")
            output.close()
        else:
            data2 = None
    return data2


def cd(dd=''):
    """ Change current working directory """
    w = os.getcwd()
    if len(dd) < 1:
        return w
    os.chdir(dd)
    return


def choose(n, k):
    """ Binomial coefficients
    Return the n!/((n-k)!k!)

    Arguments:
        n -- Integer
        k -- Integer

    Returns:
        The bionomial coefficient n choose k

    Example:
      >>> choose(6,2)
      15

    """
    ntok = 1
    for t in range(min(k, n - k)):
        ntok = ntok * (n - t) // (t + 1)
    return ntok


# %%


def deprecation(message):
    """ Issue a deprecation warning message """
    raise Exception('Method has been removed from this module. Use the warnings package directly.')
    warnings.warn(message, DeprecationWarning, stacklevel=2)


# %%
try:
    import PIL
    from PIL import ImageFont
    from PIL import Image
    from PIL import ImageDraw

    def writeTxt(im, txt, pos=(10, 10), fontsize=25, color=(0, 0, 0), fonttype=None):
        """ Write text on image using PIL """
        if fonttype is None:
            try:
                fonttype = r'c:\Windows\Fonts\Verdana.ttf'
                font = ImageFont.truetype(fonttype, fontsize)
            except BaseException:
                fonttype = '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf'
                font = ImageFont.truetype(fonttype, fontsize)
        else:
            font = ImageFont.truetype(fonttype, fontsize)
        im1 = Image.fromarray(im)
        # Drawing the text on the picture
        draw = ImageDraw.Draw(im1)
        draw.text(pos, txt, fill=color, font=font)
        return np.array(im1)
except BaseException:
    def writeTxt(im, txt, pos=(10, 10), fontsize=25, color=(0, 0, 0), fonttype=None):
        """ Dummy function """
        warnings.warn('writeTxt: could not find PIL')
        return None
    pass


# %% Copy mplimage to clipboard

try:
    _usegtk = 0
    try:
        import matplotlib.pyplot
        _usegtk = 0
    except BaseException:
        import pygtk
        pygtk.require('2.0')
        import gtk
        _usegtk = 1
        pass

    def mpl2clipboard(event=None, verbose=1, fig=None):
        """ Copy current Matplotlib figure to clipboard """
        if verbose:
            print('copy current Matplotlib figure to clipboard')
        if fig is None:
            fig = matplotlib.pyplot.gcf()
        else:
            print('mpl2clipboard: figure %s' % fig)
        w, h = fig.canvas.get_width_height()
        buf = np.fromstring(fig.canvas.tostring_argb(), dtype=np.uint8)
        buf.shape = (h, w, 4)
        im = np.roll(buf, 3, axis=2)
        im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)

        if _usegtk:
            r, tmpfile = tempfile.mkstemp(suffix='.png')
            cv2.imwrite(tmpfile, im)
            image = gtk.gdk.pixbuf_new_from_file(tmpfile)
            clipboard = gtk.clipboard_get()
            clipboard.set_image(image)
            clipboard.store()
        else:
            cb = QtWidgets.QApplication.clipboard()
            r, tmpfile = tempfile.mkstemp(suffix='.bmp')
            cv2.imwrite(tmpfile, im)
            qim = QtGui.QPixmap(tmpfile)
            cb.setPixmap(qim)

except BaseException:
    def mpl2clipboard(event=None, verbose=1, fig=None):
        """ Copy current Matplotlib figure to clipboard

        Dummy implementation
        """
        if verbose:
            print('copy current Matplotlib figure to clipboard not available')

    pass


def addfigurecopy(fig=None):
    """ Add callback to figure window

    By pressing the 'c' key figure is copied to the clipboard

    """
    if fig is None:
        Fig = plt.gcf()
    else:
        Fig = plt.figure(fig)

    def ff(xx, figx=Fig): return mpl2clipboard(fig=figx)
    Fig.canvas.mpl_connect('key_press_event', ff)  # mpl2clipboard)

# %%


class plotCallback:

    def __init__(self, func=None, xdata=None, ydata=None, scale=[1, 1], verbose=0):
        """ Object to facilitate matplotlib figure callbacks

        Args:
            func (function): function to be called
            xdata, ydata (arrays): datapoints to respond to
            verbose (int): output level
        Returns:
            pc (object): plot callback

        Example:
            >>> xdata=np.arange(4); ydata = np.random.rand( xdata.size)/2 + xdata
            >>> f = lambda plotidx, *args, **kwargs: print('point %d clicked' % plotidx)
            >>> pc = plotCallback(func=f, xdata=xdata, ydata=ydata)
            >>> fig = plt.figure(1); plt.clf(); _ = plt.plot(xdata, ydata, '.-b')
            >>> cid = fig.canvas.mpl_connect('button_press_event', pc)

        """

        self.func = func
        self.xdata = xdata
        self.ydata = ydata
        self.verbose = verbose
        if scale is None:
            # automatically determine scale
            scale = [1 / (1e-8 + np.ptp(xdata)), 1 / (1e-8 + np.ptp(ydata))]
        self.scale = scale
        self.connection_ids = []
        
    def __call__(self, event):
        if self.verbose:
            print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                  (event.button, event.x, event.y, event.xdata, event.ydata))
            print('callback function: %s' % self.func)

        # pick data point
        idx = None
        self._last_event = event

        try:
            if self.xdata is not None:
                xdata = np.array(self.xdata)
                
                if isinstance(xdata[0], numpy.datetime64):
                    xdata=matplotlib.dates.date2num(xdata)

                ydata = np.array(self.ydata)
                pt = np.array([event.xdata, event.ydata])
                xx = np.vstack((xdata.flat, ydata.flat)).T
                dd = xx - pt
                dd = np.multiply(np.array(self.scale).reshape((1, 2)), dd)
                d = np.linalg.norm(dd, axis=1)
                idx = np.argmin(d)
                distance = d[idx]
                if self.verbose:
                    print('point %d: distance %.3f' % (idx, distance))
            else:
                if self.verbose:
                    print('no xdata')

            # call the function
            self.func(plotidx=idx, button=event.button)
        except Exception as ex:
            print(ex)
        if self.verbose:
            print('plot callback complete')

    def connect(self, fig):
        if isinstance(fig, int):
            fig = plt.figure(fig)
        cid = fig.canvas.mpl_connect('button_press_event', self)
        self.connection_ids.append(cid)
        return cid

def cfigure(*args, **kwargs):
    """ Create Matplotlib figure with copy to clipboard functionality

    By pressing the 'c' key figure is copied to the clipboard

    """
    if 'facecolor' in kwargs:
        fig = plt.figure(*args, **kwargs)
    else:
        fig = plt.figure(*args, facecolor='w', **kwargs)

    def ff(xx, figx=fig): return mpl2clipboard(fig=figx)
    fig.canvas.mpl_connect('key_press_event', ff)  # mpl2clipboard)
    return fig

# %%


try:
    def monitorSizes(verbose=0):
        """ Return monitor sizes """
        _qd = QtWidgets.QDesktopWidget()
        if sys.platform == 'win32' and _qd is None:
            import ctypes
            user32 = ctypes.windll.user32
            wa = [
                [0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]]
        else:
            _applocalqt = QtWidgets.QApplication.instance()

            if _applocalqt is None:
                _applocalqt = QtWidgets.QApplication([])
                _qd = QtWidgets.QDesktopWidget()
            else:
                _qd = QtWidgets.QDesktopWidget()

            nmon = _qd.screenCount()
            wa = [_qd.screenGeometry(ii) for ii in range(nmon)]
            wa = [[w.x(), w.y(), w.width(), w.height()] for w in wa]

        if verbose:
            for ii, w in enumerate(wa):
                print('monitor %d: %s' % (ii, str(w)))
        return wa
except BaseException:
    def monitorSizes(verbose=0):
        """ Dummy function for monitor sizes """
        return [[0, 0, 1600, 1200]]
    pass

# %%


def getWindowRectangle():
    """ Return current matplotlib window rectangle """
    x, y, w, h = None, None, None, None
    mngr = plt.get_current_fig_manager()
    be = matplotlib.get_backend()
    if be == 'WXAgg':
        (x, y) = mngr.canvas.manager.window.GetPosition(x, y)
        (w, h) = mngr.canvas.manager.window.GetSize()
    elif be == 'TkAgg':
        print('getWindowRectangle: not implemented...')
        #_=mngr.canvas.manager.window.wm_geometry("%dx%d+%d+%d" % (w,h,x,y))
    elif be == 'module://IPython.kernel.zmq.pylab.backend_inline':
        pass
    else:
        # assume Qt canvas
        g = mngr.canvas.manager.window.geometry()
        x, y, w, h = g.left(), g.top(), g.width(), g.height()
        # mngr.window.setGeometry(x,y,w,h)
    return (x, y, w, h)


def setWindowRectangle(x, y=None, w=None, h=None, fig=None, mngr=None):
    """ Position the current Matplotlib figure at the specified position

    Args:
        x: position in format (x,y,w,h)
        fig (None or int): specification of figure window. Use None for the current active window

    Usage: setWindowRectangle([x,y,w,h])
    """
    if y is None:
        y = x[1]
        w = x[2]
        h = x[3]
        x = x[0]
    if mngr is None:
        mngr = plt.get_current_fig_manager()
    be = matplotlib.get_backend()
    if be == 'WXAgg':
        mngr.canvas.manager.window.SetPosition((x, y))
        mngr.canvas.manager.window.SetSize((w, h))
    elif be == 'TkAgg':
        _ = mngr.canvas.manager.window.wm_geometry("%dx%d+%d+%d" % (w, h, x, y))
    elif be == 'module://IPython.kernel.zmq.pylab.backend_inline':
        pass
    else:
        # assume Qt canvas
        mngr.canvas.manager.window.move(x, y)
        mngr.canvas.manager.window.resize(w, h)
        mngr.canvas.manager.window.setGeometry(x, y, w, h)


try:
    # http://forums.xkcd.com/viewtopic.php?f=11&t=99890
    import msvcrt

    def getkey():
        """ Cross-platform get key function """
        if msvcrt.kbhit():
            k = msvcrt.getch()
            return k
        return None
except BaseException:
    pass


def raiseWindow(fig):
    """ Raise a matplotlib window to to front """
    plt.figure(fig)  # plt.show()
    w = pylab.get_current_fig_manager().window
    w.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    w.show()


# %%


@static_var('monitorindex', -1)
def tilefigs(lst, geometry=[2, 2], ww=None, raisewindows=False, tofront=False,
             verbose=0, monitorindex=None):
    """ Tile figure windows on a specified area

    Arguments
    ---------
        lst : list
                list of figure handles or integers
        geometry : 2x1 array
                layout of windows
        monitorindex (None or int): index of monitor to use for output
        ww (None or list): monitor sizes

    """
    mngr = plt.get_current_fig_manager()
    be = matplotlib.get_backend()
    if monitorindex is None:
        monitorindex = tilefigs.monitorindex

    if ww is None:
        ww = monitorSizes()[monitorindex]

    w = ww[2] / geometry[0]
    h = ww[3] / geometry[1]

    # wm=plt.get_current_fig_manager()

    if isinstance(lst, int):
        lst = [lst]
    if isinstance(lst, numpy.ndarray):
        lst = lst.flatten().astype(int)

    if verbose:
        print('tilefigs: ww %s, w %d h %d' % (str(ww), w, h))
    for ii, f in enumerate(lst):
        if isinstance(f, matplotlib.figure.Figure):
            fignum = f.number
        elif isinstance(f, (int, numpy.int32, numpy.int64)):
            fignum = f
        else:
            # try
            try:
                fignum = f.fig.number
            except BaseException:
                fignum = -1
        if not plt.fignum_exists(fignum):
            if verbose >= 2:
                print('tilefigs: f %s fignum: %s' % (f, str(fignum)))
            continue
        fig = plt.figure(fignum)
        iim = ii % np.prod(geometry)
        ix = iim % geometry[0]
        iy = np.floor(float(iim) / geometry[0])
        x = ww[0] + ix * w
        y = ww[1] + iy * h
        if verbose:
            print('ii %d: %d %d: f %d: %d %d %d %d' %
                  (ii, ix, iy, fignum, x, y, w, h))
            if verbose >= 2:
                print('  window %s' % mngr.get_window_title())
        if be == 'WXAgg':
            fig.canvas.manager.window.SetPosition((x, y))
            fig.canvas.manager.window.SetSize((w, h))
        if be == 'WX':
            fig.canvas.manager.window.SetPosition((x, y))
            fig.canvas.manager.window.SetSize((w, h))
        if be == 'agg':
            fig.canvas.manager.window.SetPosition((x, y))
            fig.canvas.manager.window.resize(w, h)
        if be == 'Qt4Agg' or be == 'QT4' or be == 'QT5Agg' or be == 'Qt5Agg':
            # assume Qt canvas
            try:
                fig.canvas.manager.window.move(x, y)
                fig.canvas.manager.window.resize(w, h)
                fig.canvas.manager.window.setGeometry(x, y, w, h)
                # mngr.window.setGeometry(x,y,w,h)
            except Exception as e:
                print('problem with window manager: ', )
                print(be)
                print(e)
                pass
        if raisewindows:
            mngr.window.raise_()
        if tofront:
            plt.figure(f)

# %%


def robustCost(x, thr, method='L1'):
    """ Robust cost function

    Args:
       x (array): data to be transformed
       thr (float or 'auto' or None): threshold. If None then the input x is returned unmodified. If 'auto' then use automatic detection (at 95th percentile)
       method (str): method to be used. use 'show' to show the options

    Example
    -------
    >>> robustCost([2,3,4],thr=2.5)
    array([ 2. ,  2.5,  2.5])
    >>> robustCost(2, thr=1)
    1
    >>> methods=robustCost(np.arange(-5,5,.2), thr=2, method='show')
    """
    if thr is None:
        return x
    if thr is 'auto':
        ax = np.abs(x)
        thr = np.percentile(ax, 95.)
        p50 = np.percentile(ax, 50)
        if thr == p50:
            thr = np.percentile(ax, 99.)
        if thr <= 0:
            warnings.warn('estimation of robust cost threshold failed (p50 %f, thr %f' % (p50, thr))

        if method == 'L2' or method == 'square':
            thr = thr * thr

    if method == 'L1':
        y = np.minimum(np.abs(x), thr)
    elif method == 'L2' or method == 'square':
        y = np.minimum(x * x, thr)
    elif method == 'BZ':
        alpha = thr * thr
        epsilon = np.exp(-alpha)
        y = -np.log(np.exp(-x * x) + epsilon)
    elif method == 'BZ0':
        # print('BZ0')
        alpha = thr * thr
        epsilon = np.exp(-alpha)
        y = -np.log(np.exp(-x * x) + epsilon) + np.log(1 + epsilon)
    elif method == 'cauchy':
        b2 = thr * thr
        d2 = x * x
        y = np.log(1 + d2 / b2)
    elif method == 'cg':
        delta = x
        delta2 = delta * delta
        w = 1 / thr  # ratio of std.dev
        w2 = w * w
        A = .1  # fraction of outliers
        y = -np.log(A * np.exp(-delta2) + (1 - A) * np.exp(-delta2 / w2) / w)
        y = y + np.log(A + (1 - A) * 1 / w)
    elif method == 'huber':
        d2 = x * x
        d = 2 * thr * np.abs(x) - thr * thr
        y = d2
        idx = np.abs(y) >= thr * thr
        y[idx] = d[idx]
    elif method == 'show':
        plt.figure(10)
        plt.clf()
        mm = ['L1', 'L2', 'BZ', 'cauchy', 'huber', 'cg']
        for m in mm:
            plt.plot(x, robustCost(x, thr, m), label=m)
        plt.legend()
        # print('robustCost: %s'  % mm)
        y = mm
    else:
        raise Exception('no such method')
    return y


def findImageHandle(fig, verbose=0, otype=matplotlib.image.AxesImage):
    """ Search for specific type of object in Matplotlib figure """
    cc = fig.get_children()
    if verbose:
        print('findImageHandle: %s: %d children' % (str(fig), len(cc)))
    for c in cc:
        if isinstance(c, otype):
            return c
        p = findImageHandle(c, verbose=verbose, otype=otype)
        if p is not None:
            return p
        if verbose >= 2:
            print(type(c))
    return None


def otsu(im, fig=None):
    """ Calculate threshold on data using Otsu's method

    Arguments
    ---------
    im : array
        data to be processed
    fig : number, optional
        If set to a number show results in a histogram

    Returns
    -------
    thr : float
        The threshold value

    Examples
    --------

    >>> thr = otsu(np.random.rand( 2000), fig=100)

    """
    thr = skimage.filters.threshold_otsu(im)

    if fig is not None:
        plt.figure(fig)
        plt.clf()
        hist, bin_edges = np.histogram(im.flatten(), bins=36)
        bwidth = np.mean(np.diff(bin_edges))
        plt.bar(bin_edges[:-1], hist, width=bwidth)

        plt.xlabel('Value')
        plot2Dline([-1, 0, thr], '--g', linewidth=2, label='Otsu')
        plt.title('Otsu: threshold')
        plt.xlim(min(bin_edges), max(bin_edges))
    return thr

# %%


def histogram(x, nbins=30, fig=1):
    """ Return histogram of data

    >>> _=histogram(np.random.rand(1,100))
    """
    nn, bin_edges = np.histogram(x, bins=nbins)
    bwidth = np.mean(np.diff(bin_edges))

    if fig:
        plt.figure(fig)
        plt.clf()
        h = plt.bar(bin_edges[:-1:], nn, color='b', width=bwidth)
        plt.ylabel('Frequency')
        return nn, bin_edges, h
    return nn, bin_edges, None


# %%
def decomposeProjectiveTransformation(H, verbose=0):
    """ Decompose projective transformation
    H is decomposed as H = Hs*Ha*Hp with

     Hs = [sR t]
          [0  1]

     Ha = [K 0]
          [0 1]

     Hp = [I 0]
          [v' eta]

    If H is 3-dimensional, then R = [ cos(phi) -sin(phi); sin(phi) cos(phi)];

    For more information see "Multiple View Geometry", paragraph 1.4.6.

    >>> Ha, Hs, Hp, rest = decomposeProjectiveTransformation( np.eye(3) )
    """
    H = np.array(H)
    k = H.shape[0]
    km = k - 1

    eta = H[k - 1, k - 1]
    Hp = np.array(np.vstack((np.eye(km, k), H[k - 1, :])))
    A = H[0:km, 0:km]
    t = H[0:km, -1]
    v = H[k - 1, 0:km].T

    eps = 1e-10
    if np.abs(np.linalg.det(A)) < 4 * eps:
        print('decomposeProjectiveTransformation: part A of matrix is (near) singular')

    sRK = A - np.array(t).dot(np.array(v.T))
    # upper left block of H*inv(Hp)
    R, K = np.linalg.qr(sRK)
    K = np.array(K)
    R = np.array(R)

    s = (np.abs(np.linalg.det(K)))**(1. / km)
    K = K / s

    if k == 2 and K[0, 0] < 0:  # in 3-dimensional case normalize sign
        K = np.diag([-1, 1]) * K
        R = R.dot(np.diag([-1, 1]))
    else:
        # primitive...
        sc = np.sign(np.diag(K))
        K = np.diag(sc).dot(K)
        R = R.dot(np.diag(sc))
    br = np.hstack((np.zeros((1, km)), np.ones((1, 1))))
    Hs = np.array(np.vstack((np.hstack((s * R, t.reshape((-1, 1)))), br)))
    Ha = np.array(np.vstack((np.hstack((K, np.zeros((km, 1)))), br)))

    phi = np.arctan2(R[1, 0], R[0, 0])

    if verbose:
        print('decomposeProjectiveTransformation: size %d' % k)
    rest = (s, phi, t, v, )
    return Ha, Hs, Hp, rest

# %% Geometry


def points_in_polygon(pts, pp):
    """ Return all points contained in a polygon

    Args:
        pt (Nx2 array): points
        pp (Nxk array): polygon
    Returns:
        rr (bool array)
    """
    rr = np.zeros(len(pts))
    for i, pt in enumerate(pts):
        r = cv2.pointPolygonTest(np.array(pp).astype(np.float32), (pt[0], pt[1]), measureDist=False)
        rr[i] = r
    return rr


def point_in_polygon(pt, pp):
    """ Return True if point is in polygon

    Args:
        pt (1x2 array): point
        pp (Nx2 array): polygon
    Returns:
        r (float): 1.0 if point is inside 1.0, otherwise -1.0
    """
    r = cv2.pointPolygonTest(pp, (pt[0], pt[1]), measureDist=False)
    return r


def minAlg_5p4(A):
    """ Algebraic minimization function

    Function computes the vector x that minimizes ||Ax|| subject to the
    condition ||x||=1.
    Implementation of Hartley and Zisserman A5.4 on p593 (2nd Ed)

    Usage:   [x,V] = minAlg_5p4(A)
    Arguments:
             A (numpy array) : The constraint matrix, ||Ax|| to be minimized
    Returns:
              x - The vector that minimizes ||Ax|| subject to the
                  condition ||x||=1

    """

    # Compute the SVD of A
    (_, _, V) = np.linalg.svd(A)

    # Take last vector in V
    x = V[-1, :]
    return x


def fitPlane(X):
    """ Determine plane going through a set of points

    Args:
        X (array): aray of size Nxk. Points in affine coordinates
    Returns:
        array: fitted plane in homogeneous coordinates

    Example:
       >>> X=np.array([[1,0,0 ], [0,1,0], [1,1,0], [2,2,0]])
       >>> t=fitPlane(X)

    """
    AA = np.vstack((X.T, np.ones(X.shape[0]))).T
    t = minAlg_5p4(AA)
    return t


def modulepath(m):
    """ Return path for module

    Args:
        m (str or module): module to return path
    Returns:
        str: path of module
    """
    package = pkgutil.get_loader(m)
    if package is None:
        return None
    return package.get_filename()


def checkmodule(module_name, verbose=1):
    """ Return location of module based on module name

    Args:
        module_name (str): name of module to inspect
    Returns
        obj: module specification
    """
    import importlib
    module_spec = importlib.util.find_spec(module_name)
    if verbose:
        print(module_spec)
    return module_spec
