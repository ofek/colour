#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dominant Wavelength and Purity
==============================

Defines objects to compute the *dominant wavelength* and *purity* of a colour
and related quantities:

-   :func:`dominant_wavelength`
-   :func:`complementary_wavelength`
-   :func:`excitation_purity`
-   :func:`colorimetric_purity`

See Also
--------
`Dominant Wavelength and Purity Notebook
<http://nbviewer.jupyter.org/github/colour-science/colour-notebooks/\
blob/master/notebooks/colorimetry/dominant_wavelength.ipynb>`_

References
----------
.. [1]  CIE TC 1-48. (2004). 9.1 Dominant wavelength and purity. In CIE
        015:2004 Colorimetry, 3rd Edition (pp. 32–33). ISBN:978-3-901-90633-6
.. [2]  Erdogan, T. (n.d.). How to Calculate Luminosity, Dominant Wavelength,
        and Excitation Purity, 7. Retrieved from http://www.semrock.com/Data/\
Sites/1/semrockpdfs/whitepaper_howtocalculateluminositywavelengthandpurity.pdf
"""

from __future__ import division, unicode_literals

import numpy as np
import scipy.spatial.distance

from colour.algebra import (euclidean_distance, extend_line_segment,
                            intersect_line_segments)
from colour.colorimetry import CMFS
from colour.models import XYZ_to_xy

__author__ = 'Colour Developers'
__copyright__ = 'Copyright (C) 2013-2017 - Colour Developers'
__license__ = 'New BSD License - http://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Colour Developers'
__email__ = 'colour-science@googlegroups.com'
__status__ = 'Production'

__all__ = [
    'closest_spectral_locus_wavelength', 'dominant_wavelength',
    'complementary_wavelength', 'excitation_purity', 'colorimetric_purity'
]


def closest_spectral_locus_wavelength(xy, xy_n, xy_s, reverse=False):
    """
    Returns the coordinates and closest spectral locus wavelength index to the
    point where the line defined by the given achromatic stimulus :math:`xy_n`
    to colour stimulus :math:`xy_n` *xy* chromaticity coordinates intersects
    the spectral locus.

    Parameters
    ----------
    xy : array_like
        Colour stimulus *xy* chromaticity coordinates.
    xy_n : array_like
        Achromatic stimulus *xy* chromaticity coordinates.
    xy_s : array_like
        Spectral locus *xy* chromaticity coordinates.
    reverse : bool, optional
        The intersection will be computed using the colour stimulus :math:`xy`
        to achromatic stimulus :math:`xy_n` reverse direction.

    Returns
    -------
    tuple
        Closest wavelength index, intersection point *xy* chromaticity
        coordinates.

    Raises
    ------
    ValueError
        If no closest spectral locus wavelength index and coordinates found.

    Examples
    --------
    >>> xy = np.array([0.26415, 0.37770])
    >>> xy_n = np.array([0.31270, 0.32900])
    >>> xy_s = XYZ_to_xy(CMFS['CIE 1931 2 Degree Standard Observer'].values)
    >>> closest_spectral_locus_wavelength(xy, xy_n, xy_s)  # doctest: +ELLIPSIS
    (array(144), array([ 0.0036969...,  0.6389577...]))
    """

    xy = np.asarray(xy)
    xy_n = np.resize(xy_n, xy.shape)
    xy_s = np.asarray(xy_s)

    xy_e = (extend_line_segment(xy, xy_n)
            if reverse else extend_line_segment(xy_n, xy))

    # Closing horse-shoe shape to handle line of purples intersections.
    xy_s = np.vstack((xy_s, xy_s[0, :]))

    xy_wl = intersect_line_segments(
        np.concatenate((xy_n, xy_e), -1),
        np.hstack((xy_s, np.roll(xy_s, 1, axis=0)))).xy
    xy_wl = xy_wl[~np.isnan(xy_wl).any(axis=-1)]
    if not len(xy_wl):
        raise ValueError(
            'No closest spectral locus wavelength index and coordinates found '
            'for "{0}" colour stimulus and "{1}" achromatic stimulus "xy" '
            'chromaticity coordinates!'.format(xy, xy_n))

    i_wl = np.argmin(scipy.spatial.distance.cdist(xy_wl, xy_s), axis=-1)

    i_wl = np.reshape(i_wl, xy.shape[0:-1])
    xy_wl = np.reshape(xy_wl, xy.shape)

    return i_wl, xy_wl


def dominant_wavelength(xy,
                        xy_n,
                        cmfs=CMFS['CIE 1931 2 Degree Standard Observer'],
                        reverse=False):
    """
    Returns the *dominant wavelength* :math:`\lambda_d` for given colour
    stimulus :math:`xy` and the related :math:`xy_wl` first and :math:`xy_{cw}`
    second intersection coordinates with the spectral locus.

    In the eventuality where the :math:`xy_wl` first intersection coordinates
    are on the line of purples, the *complementary wavelength* will be
    computed in lieu.

    The *complementary wavelength* is indicated by a negative sign
    and the :math:`xy_{cw}` second intersection coordinates which are set by
    default to the same value than :math:`xy_wl` first intersection coordinates
    will be set to the *complementary dominant wavelength* intersection
    coordinates with the spectral locus.

    Parameters
    ----------
    xy : array_like
        Colour stimulus *xy* chromaticity coordinates.
    xy_n : array_like
        Achromatic stimulus *xy* chromaticity coordinates.
    cmfs : XYZ_ColourMatchingFunctions, optional
        Standard observer colour matching functions.
    reverse : bool, optional
        Reverse the computation direction to retrieve the
        *complementary wavelength*.

    Returns
    -------
    tuple
        *Dominant wavelength*, first intersection point *xy* chromaticity
        coordinates, second intersection point *xy* chromaticity coordinates.

    See Also
    --------
    complementary_wavelength

    Examples
    --------
    *Dominant wavelength* computation:

    >>> from pprint import pprint
    >>> xy = np.array([0.26415, 0.37770])
    >>> xy_n = np.array([0.31270, 0.32900])
    >>> cmfs = CMFS['CIE 1931 2 Degree Standard Observer']
    >>> pprint(dominant_wavelength(xy, xy_n, cmfs))  # doctest: +ELLIPSIS
    (array(504...),
     array([ 0.0036969...,  0.6389577...]),
     array([ 0.0036969...,  0.6389577...]))

    *Complementary dominant wavelength* is returned if the first intersection
    is located on the line of purples:

    >>> xy = np.array([0.35000, 0.25000])
    >>> pprint(dominant_wavelength(xy, xy_n, cmfs))  # doctest: +ELLIPSIS
    (array(-520...),
     array([ 0.4133314...,  0.1158663...]),
     array([ 0.0743553...,  0.8338050...]))
    """

    xy = np.asarray(xy)
    xy_n = np.resize(xy_n, xy.shape)

    xy_s = XYZ_to_xy(cmfs.values)

    i_wl, xy_wl = closest_spectral_locus_wavelength(xy, xy_n, xy_s, reverse)
    xy_cwl = xy_wl
    wl = cmfs.wavelengths[i_wl]

    xy_e = (extend_line_segment(xy, xy_n)
            if reverse else extend_line_segment(xy_n, xy))
    intersect = intersect_line_segments(
        np.concatenate((xy_n, xy_e), -1), np.hstack((xy_s[0],
                                                     xy_s[-1]))).intersect
    intersect = np.reshape(intersect, wl.shape)

    i_wl_r, xy_cwl_r = closest_spectral_locus_wavelength(
        xy, xy_n, xy_s, not reverse)
    wl_r = -cmfs.wavelengths[i_wl_r]

    wl = np.where(intersect, wl_r, wl)
    xy_cwl = np.where(intersect[..., np.newaxis], xy_cwl_r, xy_cwl)

    return wl, np.squeeze(xy_wl), np.squeeze(xy_cwl)


def complementary_wavelength(xy,
                             xy_n,
                             cmfs=CMFS['CIE 1931 2 Degree Standard Observer']):
    """
    Returns the *complementary wavelength* :math:`\lambda_c` for given colour
    stimulus :math:`xy` and the related :math:`xy_wl` first and :math:`xy_{cw}`
    second intersection coordinates with the spectral locus.

    In the eventuality where the :math:`xy_wl` first intersection coordinates
    are on the line of purples, the *dominant wavelength* will be computed in
    lieu.

    The *dominant wavelength* is indicated by a negative sign and the
    :math:`xy_{cw}` second intersection coordinates which are set by default to
    the same value than :math:`xy_wl` first intersection coordinates will be
    set to the *dominant wavelength* intersection coordinates with the spectral
    locus.

    Parameters
    ----------
    xy : array_like
        Colour stimulus *xy* chromaticity coordinates.
    xy_n : array_like
        Achromatic stimulus *xy* chromaticity coordinates.
    cmfs : XYZ_ColourMatchingFunctions, optional
        Standard observer colour matching functions.

    Returns
    -------
    tuple
        *Complementary wavelength*, first intersection point *xy* chromaticity
        coordinates, second intersection point *xy* chromaticity coordinates.

    See Also
    --------
    dominant_wavelength

    Examples
    --------
    *Complementary wavelength* computation:

    >>> from pprint import pprint
    >>> xy = np.array([0.35000, 0.25000])
    >>> xy_n = np.array([0.31270, 0.32900])
    >>> cmfs = CMFS['CIE 1931 2 Degree Standard Observer']
    >>> pprint(complementary_wavelength(xy, xy_n, cmfs))  # doctest: +ELLIPSIS
    (array(520...),
     array([ 0.0743553...,  0.8338050...]),
     array([ 0.0743553...,  0.8338050...]))

    *Dominant wavelength* is returned if the first intersection is located on
    the line of purples:

    >>> xy = np.array([0.26415, 0.37770])
    >>> pprint(complementary_wavelength(xy, xy_n, cmfs))  # doctest: +ELLIPSIS
    (array(-504...),
     array([ 0.4897494...,  0.1514035...]),
     array([ 0.0036969...,  0.6389577...]))
    """

    return dominant_wavelength(xy, xy_n, cmfs, True)


def excitation_purity(xy,
                      xy_n,
                      cmfs=CMFS['CIE 1931 2 Degree Standard Observer']):
    """
    Returns the *excitation purity* :math:`P_e` for given colour stimulus
    :math:`xy`.

    Parameters
    ----------
    xy : array_like
        Colour stimulus *xy* chromaticity coordinates.
    xy_n : array_like
        Achromatic stimulus *xy* chromaticity coordinates.
    cmfs : XYZ_ColourMatchingFunctions, optional
        Standard observer colour matching functions.

    Returns
    -------
    numeric or array_like
        *Excitation purity* :math:`P_e`.

    Examples
    --------
    >>> xy = np.array([0.28350, 0.68700])
    >>> xy_n = np.array([0.31270, 0.32900])
    >>> cmfs = CMFS['CIE 1931 2 Degree Standard Observer']
    >>> excitation_purity(xy, xy_n, cmfs)  # doctest: +ELLIPSIS
    0.9386035...
    """

    wl, xy_wl, xy_cwl = dominant_wavelength(xy, xy_n, cmfs)

    P_e = euclidean_distance(xy_n, xy) / euclidean_distance(xy_n, xy_wl)

    return P_e


def colorimetric_purity(xy,
                        xy_n,
                        cmfs=CMFS['CIE 1931 2 Degree Standard Observer']):
    """
    Returns the *colorimetric purity* :math:`P_c` for given colour stimulus
    :math:`xy`.

    Parameters
    ----------
    xy : array_like
        Colour stimulus *xy* chromaticity coordinates.
    xy_n : array_like
        Achromatic stimulus *xy* chromaticity coordinates.
    cmfs : XYZ_ColourMatchingFunctions, optional
        Standard observer colour matching functions.

    Returns
    -------
    numeric or array_like
        *Colorimetric purity* :math:`P_c`.

    Examples
    --------
    >>> xy = np.array([0.28350, 0.68700])
    >>> xy_n = np.array([0.31270, 0.32900])
    >>> cmfs = CMFS['CIE 1931 2 Degree Standard Observer']
    >>> colorimetric_purity(xy, xy_n, cmfs)  # doctest: +ELLIPSIS
    0.9705976...
    """

    xy = np.asarray(xy)

    wl, xy_wl, xy_cwl = dominant_wavelength(xy, xy_n, cmfs)
    P_e = excitation_purity(xy, xy_n, cmfs)

    P_c = P_e * xy_wl[..., 1] / xy[..., 1]

    return P_c
