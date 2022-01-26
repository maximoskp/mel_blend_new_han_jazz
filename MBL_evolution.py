#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 23 19:25:49 2018

@author: maximoskaliakatsos-papakostas
"""

import numpy as np
import music21 as m21
import copy
import math
import time
import MBL_music_processing_functions as mpf
import MBL_melody_features_functions as mff
import os
cwd = os.getcwd()
import random

class Melody:
    ''' includes the m21 stream, features np array and Markov np matrix '''
    ''' it also includes fitness value '''
    def __init__(self, s):
        ''' initialisation from stream '''
        self.stream = s
        self.features = mff.get_features_of_stream(self.stream)
        self.markov = mff.compute_melody_markov_transitions(self.stream)
        self.fitness = []
    # end constructor
    def compute_feature_markov_fitness(self, f, m):
        ''' computes the fitness value of the melody based on '''
        ''' the input np array of target features and np matrix target markov matrix '''
        # v1 = np.linalg.norm( f - self.features )
        v1 = self.mean_relative_distance( f , self.features )
        v2 = np.linalg.norm( m - self.markov )
        self.fitness = 0.9*v1 + 0.1*v2
    # end compute_feature_markov_fitness
    def mean_relative_distance(self, x, y):
        z = np.vstack( (x ,y) )
        m = np.max(z, axis=0)
        m[ m==0 ] = 1
        return np.linalg.norm( (x-y), ord=2 )
        # return np.linalg.norm( (x-y)/m, ord=2 )
    # end mean_relative_distance
# end class Melody

class EvoSession:
    ''' includes all information about evolution '''
    def __init__(self, file1_name, file2_name, target_features, target_markov, nPop=300, nGen=200, print_gens=True):
        if print_gens:
            print('initialising evolution')
        # METADATA --------------------------------------------------- METADATA
        # names
        self.input1_name = []
        self.input2_name = []
        self.blend_name = []
        # evolution parameters
        self.nPop = nPop
        self.nGen = nGen
        self.operator_probabilities = np.array([ 0.1, 0.4, 0.4, 0.1 ])
        # TARGETs
        self.target_features = target_features
        self.target_markov = target_markov
        # PARENTS ----------------------------------------------------- PARENTS
        # parse pieces
        s1 = m21.converter.parse(file1_name)
        s2 = m21.converter.parse(file2_name)
        # put a piano instrument to both parents
        for i in s1.recurse():
            if 'Instrument' in i.classes:
                i.activeSite.replace(i, m21.instrument.Piano())
        for i in s2.recurse():
            if 'Instrument' in i.classes:
                i.activeSite.replace(i, m21.instrument.Piano())
        # transpose
        s1_trans = mpf.neutral_transposition(s1)
        s2_trans = mpf.neutral_transposition(s2)
        # fix lowest octave
        s1_fix = mpf.fix_lowest_octave(s1_trans)
        s2_fix = mpf.fix_lowest_octave(s2_trans)
        # asign to melody objects
        self.parent1 = Melody( self.fix_durations(s1_fix) )
        self.parent2 = Melody( self.fix_durations(s2_fix) )
        # compute fitness of parents
        self.parent1.compute_feature_markov_fitness( target_features, target_markov )
        self.parent2.compute_feature_markov_fitness( target_features, target_markov )
        # INITIAL POP --------------------------------------------- INITIAL POP
        if print_gens:
            print('initialising population')
        # self.prevPop, self.prevFits = self.initialise_from_parents()
        self.prevPop, self.prevFits = self.initialise_mixed_from_folders( [ '../all_xmls/han' , '../all_xmls/jazz' ])
        # EVOLUTION ------------------------------------------------- EVOLUTION
        if print_gens:
            print('applying evolution')
        self.currGen = 0
        self.bestFitness = np.min( self.prevFits )
        while self.currGen <= self.nGen and self.bestFitness > 0.0000001:
            self.currGen += 1
            self.nextPop = self.evolution_round()
            if print_gens:
                print('generation: ', self.currGen, ' - best fitness: ', self.bestFitness)
    # end constructor
    def initialise_from_parents(self):
        ''' initiliase with 50% exact copies of each parent '''
        tmpPop = []
        tmpFits = []
        for i in range(self.nPop):
            if i < self.nPop/2.0:
                tmpPop.append( self.parent1 )
                tmpFits.append( self.parent1.fitness )
            else:
                tmpPop.append( self.parent2 )
                tmpFits.append( self.parent2.fitness )
        return tmpPop, tmpFits
    # end initialise_from_parents
    def initialise_mixed_from_folders(self, folders_in, extension='.xml'):
        ''' initiliase with a copy from each parent and fill the remaining '''
        ''' positions with randomly selected individuals '''
        ''' assuming nPop will always be > 2 '''
        tmpPop = []
        tmpFits = []
        print('initialise_mixed_from_folders')
        # append parents
        tmpPop.append( self.parent1 )
        tmpFits.append( self.parent1.fitness )
        tmpPop.append( self.parent2 )
        tmpFits.append( self.parent2.fitness )
        for i in range(self.nPop-2):
            tmp_individual, tmp_fitness = self.initialise_random_piece_from_folders( folders_in )
            tmpPop.append( tmp_individual )
            tmpFits.append( tmp_fitness )
        return tmpPop, tmpFits
    # end initialise_mixed_from_folder
    def initialise_random_piece_from_folders( self, folders_in, extension='.xml' ):
        ''' initiliase a random piece from a random folder in the list of '''
        ''' input folders in folders_in '''
        print('initialise_random_piece_from_folders')
        # pick random folder from input list of folders
        picked_folder = random.choice( folders_in )
        # get list of files in folder
        file_names = os.listdir(picked_folder)
        desired_file_names = []
        # keep files with the desired extension
        for f in file_names:
            if f.endswith(extension):
                desired_file_names.append( f )
        # check if desired_file_names empty
        if len( desired_file_names ) == 0:
            print('initialisation folder not containing files with extension: ', extension)
            return
        else:
            # select a random piece
            file1_name = random.choice( desired_file_names )
            # parse pieces
            s1 = m21.converter.parse(picked_folder + os.sep + file1_name)
            # put a piano instrument to both parents
            for i in s1.recurse():
                if 'Instrument' in i.classes:
                    i.activeSite.replace(i, m21.instrument.Piano())
            # transpose
            s1_trans = mpf.neutral_transposition(s1)
            # fix lowest octave
            s1_fix = mpf.fix_lowest_octave(s1_trans)
            # asign to melody objects
            out_individual = Melody( self.fix_durations(s1_fix) )
            # compute fitness of parents
            out_individual.compute_feature_markov_fitness( self.target_features, self.target_markov )
        return out_individual, out_individual.fitness
    # end initialise_random_piece_from_folder
    def roulette_selection(self, f, n):
        ' select n idxs from f (which needs to become) distribution '
        # make f a distribution
        if np.sum(f) > 0:
            f = f/np.sum(f)
        c = np.cumsum( f )
        # dice
        z = np.random.rand()
        # see were dice falls
        idxs = []
        for i in range(n):
            idxs.append( np.argmax( z < c ) )
        return idxs
    # end roulette_selection
    def fix_durations(self, s):
        s_new = mpf.fix_durations(s)
        return s_new
    # end fix_durations
    def fix_durations_OLD(self, s):
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
                        if (m.notes[i].offset + m.notes[i].duration.quarterLength) > m.duration.quarterLength:
                            m.notes[i].duration.quarterLength = m.duration.quarterLength - m.notes[i].offset
        s_new = s_new.stripTies()
        return s_new
    # end fix_durations_OLD
    def get_random_midi_pitch_from_part(self, p):
        ' returns midi pitch, pitch index and measure index '
        # get all measures
        ms = p.getElementsByClass('Measure')
        # get random midi pitch from p1
        midi_pitch = []
        mIdx = []
        nIdx = []
        while not midi_pitch:
            # select random bar
            mIdx = np.random.randint( len( ms ) )
            tmpBar = ms[mIdx]
            # get notes of random bar
            tmpPitches = tmpBar.pitches
            if len(tmpPitches) > 0:
                # get note index
                nIdx = np.random.randint( len( tmpPitches ) )
                # get note pitch
                midi_pitch = tmpPitches[nIdx].midi
        return midi_pitch, nIdx, mIdx
    # end get_random_midi_pitch_from_part
    def get_random_pair_midi_pitch_from_part(self, p):
        ' returns midi pitch, pitch index and measure index '
        # get all measures
        ms = p.getElementsByClass('Measure')
        # get random midi pitch from p1
        midi_pitches = []
        mIdx = []
        nIdx = []
        while not midi_pitches:
            # select random bar
            mIdx = np.random.randint( len( ms ) )
            tmpBar = ms[mIdx]
            # get notes of random bar
            tmpPitches = tmpBar.pitches
            if len(tmpPitches) > 1:
                # get note index
                tmp_idx = np.random.randint( len( tmpPitches )-1 )
                # get note pitch
                midi_pitches = [tmpPitches[tmp_idx].midi, tmpPitches[tmp_idx+1].midi]
                nIdx = [tmp_idx, tmp_idx+1]
        return midi_pitches, nIdx, mIdx
    # end get_random_pair_midi_pitch_from_part
    def single_note_exchange(self, p1, p2):
        ' exchange pitches of random notes in random part and random bar '
        # initialise children
        c1 = copy.deepcopy(p1)
        c2 = copy.deepcopy(p2)
        # get minimum common part number and part
        partIdx = np.random.randint( min([ len( p1.parts), len( p2.parts) ]) )
        # get random midi pitch, note and measure index from p1
        midi_pitch_1, note_index_1, measure_index_1 = self.get_random_midi_pitch_from_part(p1.parts[partIdx])
        # get random midi pitch, note and measure index from p2
        midi_pitch_2, note_index_2, measure_index_2 = self.get_random_midi_pitch_from_part(p2.parts[partIdx])
        # exchange respective notes
        c1.parts[partIdx].getElementsByClass('Measure')[measure_index_1].notes[note_index_1].pitch = m21.pitch.Pitch(midi_pitch_2)
        c2.parts[partIdx].getElementsByClass('Measure')[measure_index_2].notes[note_index_2].pitch = m21.pitch.Pitch(midi_pitch_1)
        c1 = self.fix_durations(c1)
        c2 = self.fix_durations(c2)
        return c1, c2
    # end single_note_exchange
    def notes_pair_exchange(self, p1, p2):
        ' exchange pitches of random notes in random part and random bar '
        # initialise children
        c1 = copy.deepcopy(p1)
        c2 = copy.deepcopy(p2)
        # get minimum common part number and part
        partIdx = np.random.randint( min([ len( p1.parts), len( p2.parts) ]) )
        # get random midi pitch, note and measure index from p1
        midi_pitch_1, note_index_1, measure_index_1 = self.get_random_pair_midi_pitch_from_part(p1.parts[partIdx])
        # get random midi pitch, note and measure index from p2
        midi_pitch_2, note_index_2, measure_index_2 = self.get_random_pair_midi_pitch_from_part(p2.parts[partIdx])
        # exchange respective notes
        for i in [0,1]:
            c1.parts[partIdx].getElementsByClass('Measure')[measure_index_1].notes[note_index_1[i]].pitch = m21.pitch.Pitch(midi_pitch_2[i])
            c2.parts[partIdx].getElementsByClass('Measure')[measure_index_2].notes[note_index_2[i]].pitch = m21.pitch.Pitch(midi_pitch_1[i])
        c1 = self.fix_durations(c1)
        c2 = self.fix_durations(c2)
        return c1, c2
    # end notes_pair_exchange
    def get_random_measure_from_part(self, p):
        ' returns random bar and bar index from part '
        # get all measures
        ms = p.getElementsByClass('Measure')
        # select random bar
        mIdx = np.random.randint( len( ms ) )
        tmpBar = ms[mIdx]
        return tmpBar, mIdx
    # end get_random_measure_from_part
    def get_specific_measure_from_part(self, p, i):
        ' returns random bar and bar index from part '
        # get all measures
        ms = p.getElementsByClass('Measure')
        tmpBar = ms[i]
        return tmpBar, i
    # end get_specific_measure_from_part
    def map_offsets_and_durations(self, offs, durs, d_from, d_to):
        # compute gradient
        a = np.ceil(d_to/d_from)
        # initialise new offsets
        new_offsets = []
        # initialise new durations
        new_durations = []
        # compute offsets
        for f in offs:
            # quantise to 16th
            new_offsets.append( math.floor( 4.0*a*f )/4.0 )
        '''
        # compute durations
        for f in durs:
            # quantise to 16th
            new_durations.append( max( [math.floor( 4.0*a*f )/4.0, 0.25] ))
        '''
        # keep unique offsets through numpy
        new_offsets = np.array( new_offsets )
        # new_durations = np.array( new_durations )
        new_offsets, unidxs = np.unique( new_offsets, return_index=True )
        # new_durations = new_durations[ unidxs ]
        # compute durations based on offset - in m21 consecutive durations beat offets...
        # delete all elements that go beyond the bar border (d_to)
        beyonders = np.where( new_offsets >= d_to )[0]
        new_offsets = np.delete( new_offsets, beyonders )
        # make expanded offsets by adding the measure length as the last element
        tmp_expanded = np.append( new_offsets, d_to )
        # compute durations as differences of expanded offsets
        new_durations = np.diff( tmp_expanded )
        return new_offsets, new_durations
    # end map_offsets_to_duration
    def fit_exchange_rhythm_to_pitches(self, m1, m2):
        ' copy rhythm structure from one measure to the other '
        # first make a copy of m2
        m = copy.deepcopy(m2)
        # get all the necessary elements from the two inputs
        # measure durations
        m1_dur = m1.barDuration.quarterLength
        m2_dur = m.barDuration.quarterLength
        # notes and rests arrays
        nr1 = m1.notesAndRests
        nr2 = m.notesAndRests
        # only notes arrays
        n1 = m1.notes
        n2 = m.notes
        # offsets
        nr1_offsets = [n.offset for n in nr1]
        nr2_offsets = [n.offset for n in nr2]
        n1_offsets = [n.offset for n in n1]
        n2_offsets = [n.offset for n in n2]
        # durations
        nr1_durations = [n.duration.quarterLength for n in nr1]
        nr2_durations = [n.duration.quarterLength for n in nr2]
        n1_durations = [n.duration.quarterLength for n in n1]
        n2_durations = [n.duration.quarterLength for n in n2]
        # pitches
        n1_pitches = [n.pitch for n in n1]
        n2_pitches = [n.pitch for n in n2]
        nr1_pitches = []
        nr2_pitches = []
        for n in nr1:
            if n.isNote:
                nr1_pitches.append( n.pitch )
            else:
                nr1_pitches.append( -1 )
        for n in nr2:
            if n.isNote:
                nr2_pitches.append( n.pitch )
            else:
                nr2_pitches.append( -1 )
        # proceed only if both input measures have notes
        if len(n1_pitches) > 0 and len(n2_pitches) > 0:
            # get mapped offsets
            n1_new_offsets, n1_new_durations = self.map_offsets_and_durations( nr2_offsets, nr2_durations, m2_dur, m1_dur )
            n2_new_offsets, n2_new_durations = self.map_offsets_and_durations( nr1_offsets, nr1_durations, m1_dur, m2_dur )
            '''
            # get mapped durations
            n1_new_durations = self.map_offsets_to_duration( n2_durations, m2_dur, m1_dur )
            n2_new_durations = self.map_offsets_to_duration( n1_durations, m1_dur, m2_dur )
            '''
            # remove all notes from m1
            for n in m1.notesAndRests:
                m1.remove(n)
            # create and append new pitches to m1
            tmp_idx = 0;
            for i in range( len( n1_new_offsets ) ):
                tmp_pitch = n1_pitches[ tmp_idx ]
                if nr2_pitches[i] == -1:
                    tmp_note = m21.note.Rest()
                else:
                    tmp_note = m21.note.Note( tmp_pitch )
                    tmp_idx = tmp_idx + 1
                    tmp_idx = tmp_idx%len( n1_pitches )
                tmp_note.offset = n1_new_offsets[i]
                tmp_note.duration.quarterLength = n1_new_durations[i]
                m1.append( tmp_note )
            # remove all notes from m2
            for n in m2.notesAndRests:
                m2.remove(n)
            # create and append new pitches to m1
            tmp_idx = 0;
            for i in range( len( n2_new_offsets ) ):
                tmp_pitch = n2_pitches[ tmp_idx ]
                if nr1_pitches[i] == -1:
                    tmp_note = m21.note.Rest()
                else:
                    tmp_note = m21.note.Note( tmp_pitch )
                    tmp_idx = tmp_idx + 1
                    tmp_idx = tmp_idx%len( n2_pitches )
                tmp_note.offset = n2_new_offsets[i]
                tmp_note.duration.quarterLength = n2_new_durations[i]
                m2.append( tmp_note )
    # end fit_exchange_rhythm_to_pitches
    def bar_rhythm_exchange(self, p1, p2):
        ' exchange pitches of random notes in random part and random bar '
        # initialise children
        c1 = copy.deepcopy(p1)
        c2 = copy.deepcopy(p2)
        # get minimum common part number and part
        partIdx = np.random.randint( min([ len( p1.parts), len( p2.parts) ]) )
        # get measures and indexes from p1 and p2
        measure_1, measure_index_1 = self.get_random_measure_from_part(c1.parts[partIdx])
        measure_2, measure_index_2 = self.get_random_measure_from_part(c2.parts[partIdx])
        # NEW exchange
        self.fit_exchange_rhythm_to_pitches( measure_1, measure_2 )
        c1 = self.fix_durations(c1)
        c2 = self.fix_durations(c2)
        return c1, c2
    # end bar_rhythm_exchange
    def entire_rhythm_exchange(self, p1, p2):
        # initialise children
        ' exchange pitches of random notes in random part and random bar '
        c1 = copy.deepcopy(p1)
        c2 = copy.deepcopy(p2)
        # get minimum common part number and part
        minPartsNum = min([ len( p1.parts), len( p2.parts) ])
        for i in range(minPartsNum):
            c1p = c1.parts[i]
            c2p = c2.parts[i]
            # get minimum number of measures in part
            minMeasuresNum = min( [len(c1p.getElementsByClass('Measure')), len(c2p.getElementsByClass('Measure'))] )
            # get all measures
            for j in range( minMeasuresNum ):
                # get specific measures and indexes from p1 and p2
                measure_1, measure_index_1 = self.get_specific_measure_from_part(c1.parts[i], j)
                measure_2, measure_index_2 = self.get_specific_measure_from_part(c2.parts[i], j)
                # NEW exchange
                self.fit_exchange_rhythm_to_pitches( measure_1, measure_2 )
        c1 = self.fix_durations(c1)
        c2 = self.fix_durations(c2)
        return c1, c2
    # end bar_rhythm_exchange
    def select_best_population(self):
        ' returns the best nPop individuals and their respective fitnesses '
        # sort fitnesses and get the indexes
        sortedIdxs = np.argsort( self.mergedFits )
        newPop = []
        newFits = []
        # sort pop and fits accordingly
        for i in sortedIdxs:
            newPop.append( self.mergedPop[i] )
            newFits.append( self.mergedFits[i] )
        newFits = np.array( newFits )
        # keep only the top nPop
        self.prevFits = newFits[:self.nPop]
        self.prevPop = newPop[:self.nPop]
        # compute self.best_individual and self.bestFitness
        self.best_individual = self.prevPop[0]
        self.bestFitness = self.prevFits[0]
    # end select_best_population
    def evolution_round(self):
        self.nextPop = []
        self.nextFits = []
        # until nextPop has less than nPop individuals
        while len(self.nextPop) < self.nPop:
            # roulette-based selection of parents
            idxs = self.roulette_selection(self.prevFits, 2)
            # get respective parents:
            p1 = self.prevPop[idxs[0]].stream
            p2 = self.prevPop[idxs[1]].stream
            # roulette-based selection of operators
            idx_op = self.roulette_selection(self.operator_probabilities, 1)
            # check and select operator
            if idx_op[0] == 0:
                c1, c2 = self.single_note_exchange(p1, p2)
            elif idx_op[0] == 1:
                c1, c2 = self.notes_pair_exchange(p1, p2)
            elif idx_op[0] == 2:
                c1, c2 = self.bar_rhythm_exchange(p1, p2)
            elif idx_op[0] == 3:
                c1, c2 = self.entire_rhythm_exchange(p1, p2)
            else:
                print('unknown operator!')
            # melody objects and fitness computation for each child
            m1 = Melody(c1)
            m1.compute_feature_markov_fitness( self.target_features, self.target_markov )
            m2 = Melody(c2)
            m2.compute_feature_markov_fitness( self.target_features, self.target_markov )
            # put child in nextPop
            self.nextPop.append( m1 )
            self.nextPop.append( m2 )
            self.nextFits.append( m1.fitness )
            self.nextFits.append( m2.fitness )
            # merge the two populations
            self.mergedPop = self.prevPop + self.nextPop
            self.mergedFits = np.concatenate( (self.prevFits, self.nextFits) )
            self.mergedFits = np.array( self.mergedFits )
            # select best from merged population and keep best individual and fitness
            self.select_best_population()
    # end evolution_round