#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 23 18:05:00 2018

@author: maximoskaliakatsos-papakostas

Accepted feature labels:
- 'r_density'
- 'r_inhomogeneity'
- 'pcp_entropy'
- 'small_intervals'
- 'pentatonicity'
- 'simple_syncopation'

Functions included:
- get_features_of_stream
- compute_feature
- get_accepted_feature_labels
- compute_rhythm_density
- compute_rhythm_inhomogeneity
- compute_pcp_entropy
- compute_small_intervals
- compute_melody_markov_transitions
- compute_simple_syncopation

"""

# import music21 as m21
import numpy as np
import scipy.stats as sc

def get_accepted_feature_labels():
    ''' returns a list of strings that correspond to feature computation functions '''
    return ['r_density', 'r_inhomogeneity', 'pcp_entropy', 'small_intervals', 'simple_syncopation', 'pentatonicity']
# end get_accepted_feature_labels

def compute_rhythm_density(s):
    # isolate all note events
    notes = []
    # take flat notes from all parts
    for p in s.parts:
        notes.extend( p.flat.notes )
    # isolate all offsets
    offs = []
    # for all notes in all parts
    for n in notes:
        offs.append( float(n.offset) )
    # keep only unique offsets
    offs_unique = list(set( offs ))
    # suppose that there is a maximum of 4 notes per offset unit (16ths)
    # and compute the maximum expected number of offsets
    expected_offsets = 4.0*max(offs_unique)
    # compute actual offets over expected
    return len(offs_unique)/expected_offsets
# end compute_rhythm_density
def compute_simple_sycopation(s):
    # syncopation per bar
    synco_per_bar = []
    for p in s.parts:
        # get measures
        ms = p.getElementsByClass('Measure')
        for m in ms:
            # get offsets of all notes in bar
            offs = []
            for n in m.notes:
                offs.append( float(n.offset) )
            offs = np.array( offs )
            # get l1 notes and their number
            l1 = np.floor(offs) == offs
            s1 = np.sum(l1)
            # get all l2 notes and their sum
            l2 = np.logical_and( np.floor(10*offs) == 10*offs, np.logical_not(l1) )
            s2 = np.sum(l2)
            # get all l3 notes and their number
            l1_or_l2 = np.logical_or(l1, l2)
            l3 = np.logical_and( np.floor(100*offs) == 100*offs, np.logical_not(l1_or_l2) )
            s3 = np.sum(l3)
            # get all l4 notes and their number
            l1_or_l2_or_l3 = np.logical_or(l1_or_l2, l3)
            l4 = np.logical_and( np.floor(1000*offs) == 1000*offs, np.logical_not(l1_or_l2_or_l3) )
            s4 = np.sum(l4)
            # SUPPORTS
            # ------------ l2
            # shift vector for l2
            l2_shift = offs + 0.5
            # roll by one position
            l2_shift_roll = np.roll( l2_shift, 1 )
            # get l2 support
            l2_support = l2_shift_roll == offs
            # unsupport vector for l2
            l2u = np.logical_and( l2, np.logical_not( l2_support ) )
            s2u = np.sum(l2u)
            # ------------ l3
            # shift vector for l3
            l3_shift = offs + 0.25
            # roll by one position
            l3_shift_roll = np.roll( l3_shift, 1 )
            # get l3 support
            l3_support = l3_shift_roll == offs
            # unsupport vector for l3
            l3u = np.logical_and( l3, np.logical_not( l3_support ) )
            s3u = np.sum(l3u)
            # ------------ l4
            # shift vector for l4
            l4_shift = offs + 0.125
            # roll by one position
            l4_shift_roll = np.roll( l4_shift, 1 )
            # get l4 support
            l4_support = l4_shift_roll == offs
            # unsupport vector for l4
            l4u = np.logical_and( l4, np.logical_not( l4_support ) )
            s4u = np.sum(l4u)
            # append to all syncopations per bar
            synco_val = 0.0*s1 + 0.05*s2 + 0.1*s3 + 0.2*s4 + 1.0*s2u + 2.0*s3u + 4.0*s4u
            if len( offs ) > 0:
                synco_val = synco_val/len(offs)
            synco_per_bar.append( synco_val )
    synco_per_bar = np.array( synco_per_bar )
    return np.mean( synco_per_bar )
# end compute_simple_sycopation
def compute_rhythm_inhomogeneity(s):
    # isolate all note events
    notes = []
    # take flat notes from all parts
    for p in s.parts:
        notes.extend( p.flat.notes )
    # isolate all offsets
    offs = []
    # for all notes in all parts
    for n in notes:
        offs.append( float(n.offset) )
    # keep only unique offsets
    offs_unique = np.array( list(set( offs )) )
    # sort offsets to make sure
    sorted_offs = np.sort( offs_unique )
    # get differences in offsets
    diff_offs = np.diff( sorted_offs )
    # return std over mean
    return np.std(diff_offs)/np.mean(diff_offs)
# end compute_rhythm_inhomogeneity
def compute_pcp_entropy(s):
    # isolate all note events
    notes = []
    # take flat notes from all parts
    for p in s.parts:
        notes.extend( p.flat.notes )
    # isolate all midi notes
    midis = []
    # for all notes in all parts
    for n in notes:
        midis.append( n.pitch.midi)
    # compute pcp
    # pcp = np.histogram( np.mod(midis, 12), bins=12 )[0]
    pcp = np.histogram( np.mod(midis, 12), bins=[0,1,2,3,4,5,6,7,8,9,10,11,12] )[0]
    # return entropy
    return sc.entropy( pcp )
# end compute_pcp_entropy
def compute_pcp(s):
    # isolate all note events
    notes = []
    # take flat notes from all parts
    for p in s.parts:
        notes.extend( p.flat.notes )
    # isolate all midi notes
    midis = []
    # for all notes in all parts
    for n in notes:
        midis.append( n.pitch.midi)
    # compute pcp
    # pcp = np.histogram( np.mod(midis, 12), bins=12 )[0]
    pcp = np.histogram( np.mod(midis, 12), bins=[0,1,2,3,4,5,6,7,8,9,10,11,12] )[0]
    return pcp
def compute_pentatonicity(s):
    # pentatonic template
    penta_template = np.array([ 1,0,0,1,0,1,0,1,0,0,1,0 ])
    # isolate all note events
    notes = []
    # take flat notes from all parts
    for p in s.parts:
        notes.extend( p.flat.notes )
    # isolate all midi notes
    midis = []
    # for all notes in all parts
    for n in notes:
        midis.append( n.pitch.midi)
    # compute pcp
    pcp = np.histogram( np.mod(midis, 12), bins=[0,1,2,3,4,5,6,7,8,9,10,11,12] )[0]
    # pcp = pcp/np.max(pcp)
    # assume a minimum correlation
    c = -1
    # roll and check
    for i in range(12):
        # c_new = np.corrcoef( pcp , np.roll(penta_template, i) )[0][1]
        c_new = np.inner(pcp, np.roll(penta_template, i))/np.sum(pcp)*np.corrcoef( pcp , np.roll(penta_template, i) )[0][1]
        if c_new > c:
            c = c_new
    # return (c+1)/2
    return c
# end compute_pentatonicity
def compute_small_intervals(s):
    # stream is considered monophonic
    # isolate all note events
    notes = []
    # take flat notes from all parts
    for p in s.parts:
        notes.extend( p.flat.notes )
    # isolate all midi notes
    midis = []
    # for all notes in all parts
    for n in notes:
        midis.append( n.pitch.midi)
    # small intervals percentage
    d = np.diff( np.array( midis ) )
    dd = d[ d!=0 ]
    return np.sum(np.abs(dd) < 3)/np.size(dd)
# end compute_small_intervals
def compute_melody_markov_transitions(s):
    # stream is considered monophonic
    # initialise 128x128 Markov transition matrix
    m = np.zeros( (128,128) )
    # isolate all note events
    notes = []
    # take flat notes from all parts
    for p in s.parts:
        notes.extend( p.flat.notes )
    # isolate all midi notes
    midis = []
    # for all notes in all parts
    for n in notes:
        midis.append( n.pitch.midi)
    # construct sums
    for i in range(len(midis)-1):
        m[ midis[i], midis[i+1] ] = m[ midis[i], midis[i+1] ] + 1
    # make probabilities
    for i in range(m.shape[0]):
        tmpSum = np.sum(m[i,:])
        if tmpSum > 0:
            m[i,:] = m[i,:]/tmpSum
    return m
# end compute_melody_markov_transitions

def compute_feature(s, label):
    ''' gets a stream s and an accepted label and returns the numeric value
        of the requested feature '''
    # initialise an empty feature value
    f = []
    # first check if given label is accepted
    if label in get_accepted_feature_labels():
        if label is 'r_density':
            f = compute_rhythm_density(s)
        elif label is 'r_inhomogeneity':
            f = compute_rhythm_inhomogeneity(s)
        elif label is 'pcp_entropy':
            f = compute_pcp_entropy(s)
        elif label is 'pentatonicity':
            f = compute_pentatonicity(s)
        elif label is 'small_intervals':
            f = compute_small_intervals(s)
        elif label is 'simple_syncopation':
            f = compute_simple_sycopation(s)
        else:
            print('wtf?')
    else:
        print('feature label: ', label, ' not in accepted list')
    return f
    # don't forget to compute and return feature!
# end compute_feature

def get_features_of_stream(s, feature_labels=['r_density', 'simple_syncopation', 'pentatonicity', 'small_intervals']):
    ''' gets a stream s and an array of the desired feature labels and
        returns an np array with the requested feature values'''
    # initialise an empty array of features
    f = []
    # start appending feature values
    for lb in feature_labels:
        f.append( compute_feature(s, lb) )
    # return final np array
    return np.array(f)
# end get_features_of_stream