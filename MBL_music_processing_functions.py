#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 23 15:59:37 2018

@author: maximoskaliakatsos-papakostas

Functions included:
- neutral_transposition
- fix_lowest_octave
- get_minimum_midi_pitch

"""

import music21 as m21
import copy
import numpy as np

def get_minimum_pitch(s):
    ''' scans all notes in all parts of stream s and returns the lowest pitch 
        as a m21 pitch object'''
    # initialise minimum pitch
    m = m21.pitch.Pitch(127)
    # scan all parts
    for p in s.parts:
        # can all notes in part
        for n in p.flat.notes.getElementsByClass('Note'):
            # and compare them with minimum pitch
            if n.pitch < m:
                m = n.pitch
    return m
# end get_minimum_pitch

def neutral_transposition(s):
    ''' gets a stream s and returns a stream in C maj or Amin key '''
    # get tonality
    k = s.analyze('key.krumhanslschmuckler')
    # major and minor class modes
    major_class = {'major', 'mixolydian', 'lydian'}
    # minor_class = {'minor', 'dorian', 'phrygian', 'locrian'}
    # get mode for transposing
    m = k.mode
    # get tonic pitch
    t = k.tonic
    # get transposition interval depending on mode
    if m in major_class:
        i = m21.interval.Interval(t, m21.pitch.Pitch('C'))
    else:
        i = m21.interval.Interval(t, m21.pitch.Pitch('A'))
    # transpose
    s_trans = s.transpose(i)
    return s_trans
# end neutral_transposition

def fix_lowest_octave(s, lowest_pitch=60):
    ''' gest a stream s and returns a stream in the same key but
        with its lowest pitch in a given octave - just above a lowestpitch '''
    # find minimum pitch
    m = get_minimum_pitch(s)
    # check octaves difference from lowest pitch
    d = int( np.ceil( m21.interval.Interval(m, m21.pitch.Pitch(lowest_pitch)).semitones/12 ) )
    # transpose by so many octaves
    i = m21.interval.Interval( 12*d )
    s_fix = s.transpose(i)
    return s_fix
# end fix_lowest_octave

def keep_notes_only(s):
    # keeps only note-class elements - removes harmony / not chords
    new_s = copy.deepcopy(s)
    # check is first bar is empty from notes and remove it
    if len( new_s.parts[0].getElementsByClass('Measure')[0].getElementsByClass('Note') ) == 0:
        # get measure to remove
        m0 = new_s.parts[0].getElementsByClass('Measure')[0]
        # get it's time signature
        ts = m0.getElementsByClass('TimeSignature')
        # if there's no time signature to the next measure, add the previous one
        if not new_s.parts[0].getElementsByClass('Measure')[1].timeSignature:
            new_s.parts[0].getElementsByClass('Measure')[1].insert(0, ts[0])
        # remove the first measure
        new_s.parts[0].remove( m0 )
        # new_s.parts[0].getElementsByClass('Measure').pop( 0 )
    for m in new_s.parts[0].getElementsByClass('Measure'):
        for h in m.getElementsByClass('Harmony'):
            m.remove(h)
    return new_s
# end keep_notes_only

def keep_num_bars(s, n):
    # return at most the first n bars of s
    s_out = m21.stream.Score()
    for p in s.parts:
        p_new = m21.stream.Part()
        ms = p.getElementsByClass('Measure')
        bars_num = min( len(ms), n )
        for i in range( bars_num ):
            p_new.insert(ms[i].offset, ms[i])
        s_out.insert(0, p_new)
    return s_out
# end keep_num_bars

def fix_durations(s):
    s_new = copy.deepcopy(s)
    # s_new = s_new.stripTies()
    for p in s_new.parts:
        for m in p.getElementsByClass('Measure'):
            notes_to_remove = []
            for i in range( len( m.notes ) ):
                if m.notes[i].tie:
                    if m.notes[i].tie.type == 'start':
                        m.notes[i].tie = None
                    elif m.notes[i].tie.type == 'stop':
                        m.notes[i].tie = None
                        notes_to_remove.append( m.notes[i] )
                    elif m.notes[i].tie.type == 'continue':
                        m.notes[i].tie = None
                        notes_to_remove.append( m.notes[i] )
            # remove notes
            for i in range( len(notes_to_remove) ):
                m.remove(notes_to_remove[i])
            for i in range( len( m.notes ) ):
                if i < ( len( m.notes )-1 ):
                    if m.notes[i].duration.quarterLength < ( m.notes[i+1].offset - m.notes[i].offset ):
                        m.notes[i].duration.quarterLength = ( m.notes[i+1].offset - m.notes[i].offset )
                else:
                    if (m.notes[i].offset + m.notes[i].duration.quarterLength) > m.barDuration.quarterLength:
                        m.notes[i].duration.quarterLength = m.barDuration.quarterLength - m.notes[i].offset
    s_new = s_new.stripTies()
    return s_new
# end fix_durations