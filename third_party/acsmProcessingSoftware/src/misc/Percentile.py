# -*- coding: utf-8 -*-
"""
Description :
-------------
    Percentile computing implementation. This method exists in numpy v>=1.7
    Source code directly copied from this version to be used with numpy v1.4.0

    Copied from : https://github.com/numpy/numpy/blob/v1.7.0/numpy/lib/function_base.py#L2997
"""

from numpy.core.fromnumeric import sort
from numpy.core.numeric import isscalar, array
from numpy.core.umath import add
import numpy as np


def percentile(a, q, axis=None, out=None, overwrite_input=False):
    """
    Compute the qth percentile of the data along the specified axis.

    Returns the qth percentile of the array elements.

    Parameters
    ----------
    a : array_like
    Input array or object that can be converted to an array.
    q : float in range of [0,100] (or sequence of floats)
    Percentile to compute which must be between 0 and 100 inclusive.
    axis : int, optional
    Axis along which the percentiles are computed. The default (None)
    is to compute the median along a flattened version of the array.
    out : ndarray, optional
    Alternative output array in which to place the result. It must
    have the same shape and buffer length as the expected output,
    but the type (of the output) will be cast if necessary.
    overwrite_input : bool, optional
    If True, then allow use of memory of input array `a` for
    calculations. The input array will be modified by the call to
    median. This will save memory when you do not need to preserve
    the contents of the input array. Treat the input as undefined,
    but it will probably be fully or partially a_sorted.
    Default is False. Note that, if `overwrite_input` is True and the
    input is not already an array, an error will be raised.

    Returns
    -------
    pcntile : ndarray
    A new array holding the result (unless `out` is specified, in
    which case that array is returned instead). If the input contains
    integers, or floats of smaller precision than 64, then the output
    data-type is float64. Otherwise, the output data-type is the same
    as that of the input.

    See Also
    --------
    mean, median

    Notes
    -----
    Given a vector V of length N, the qth percentile of V is the qth ranked
    value in a a_sorted copy of V. A weighted average of the two nearest
    neighbors is used if the normalized ranking does not match q exactly.
    The same as the median if ``q=50``, the same as the minimum if ``q=0``
    and the same as the maximum if ``q=100``.

    Examples
    --------
    >>> a = np.array([[10, 7, 4], [3, 2, 1]])
    >>> a
    array([[10, 7, 4],
    [ 3, 2, 1]])
    >>> np.percentile(a, 50)
    3.5
    >>> np.percentile(a, 0.5, axis=0)
    array([ 6.5, 4.5, 2.5])
    >>> np.percentile(a, 50, axis=1)
    array([ 7., 2.])

    >>> m = np.percentile(a, 50, axis=0)
    >>> out = np.zeros_like(m)
    >>> np.percentile(a, 50, axis=0, out=m)
    array([ 6.5, 4.5, 2.5])
    >>> m
    array([ 6.5, 4.5, 2.5])

    >>> b = a.copy()
    >>> np.percentile(b, 50, axis=1, overwrite_input=True)
    array([ 7., 2.])
    >>> assert not np.all(a==b)
    >>> b = a.copy()
    >>> np.percentile(b, 50, axis=None, overwrite_input=True)
    3.5

    """
    a = np.asarray(a)

    if q == 0:
        return a.min(axis=axis, out=out)
    elif q == 100:
        return a.max(axis=axis, out=out)

    if overwrite_input:
        if axis is None:
            a_sorted = a.ravel()
            a_sorted.sort()
        else:
            a.sort(axis=axis)
            a_sorted = a
    else:
        a_sorted = sort(a, axis=axis)
    if axis is None:
        axis = 0

    return _compute_qth_percentile(a_sorted, q, axis, out)

# handle sequence of q's without calling sort multiple times


def _compute_qth_percentile(a_sorted, q, axis, out):
    if not isscalar(q):
        p = [_compute_qth_percentile(a_sorted, qi, axis, None)
             for qi in q]

        if out is not None:
            out.flat = p

        return p

    q = q / 100.0
    if (q < 0) or (q > 1):
        raise ValueError("percentile must be either in the range [0,100]")

    indexer = [slice(None)] * a_sorted.ndim
    Nx = a_sorted.shape[axis]
    index = q * (Nx - 1)
    i = int(index)
    if i == index:
        indexer[axis] = slice(i, i + 1)
        weights = array(1)
        sumval = 1.0
    else:
        indexer[axis] = slice(i, i + 2)
        j = i + 1
        weights = array([(j - index), (index - i)], float)
        wshape = [1] * a_sorted.ndim
        wshape[axis] = 2
        weights.shape = wshape
        sumval = weights.sum()

    # Use add.reduce in both cases to coerce data type as well as
    # check and use out array.
    return add.reduce(a_sorted[tuple(indexer)] * weights, axis=axis, out=out) / sumval
