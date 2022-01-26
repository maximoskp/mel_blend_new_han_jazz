#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 23 15:59:37 2018

@author: maximoskaliakatsos-papakostas

Functions included:
- write_stream_to_midi

"""

import music21 as m21
import copy
from itertools import chain, combinations

def blend_single_feature(f1, f2, feature_index):
    ''' puts feature with index feature_index from f1 array and puts it in f2 '''
    f = copy.deepcopy(f2)
    f[ feature_index ] = f1[ feature_index ]
    return f
# end get_minimum_pitch

def blend_all_combinations(f1, f2):
    # get set of all indexes
    idxs = powerset( range( len(f1) ) )
    all_combs = []
    for i in range(1, len(idxs)-1, 1):
        f1_copy = copy.deepcopy( f1 )
        f1_copy[ list(idxs[i]) ] = f2[ list(idxs[i]) ]
        all_combs.append( f1_copy )
    return all_combs
# end blend_all_combinations

def powerset(iterable):
    """
    powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    """
    xs = list(iterable)
    # note we return an iterator rather than a list
    return list( chain.from_iterable(combinations(xs,n) for n in range(len(xs)+1)) )
# end powerset