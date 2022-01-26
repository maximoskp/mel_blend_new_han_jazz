#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 23 15:59:37 2018

@author: maximoskaliakatsos-papakostas

Functions included:
- write_stream_to_midi

"""

import music21 as m21
import os

def write_stream_to_midi(s, filePath=os.getcwd()+"/", appendToPath="", fileName='test_midi_export.mid'):
    ''' exports stream s in midi file saved in filepath with fileName '''
    mf = m21.midi.translate.streamToMidiFile(s)
    mf.open(filePath + appendToPath + fileName, 'wb')
    mf.write()
    mf.close()
# end write_stream_to_midi

# XML NOT WORKING
def write_stream_to_xml(s, filePath=os.getcwd()+"/", appendToPath="", fileName='test_midi_export.xml'):
    mf = m21.musicxml.m21ToXml.GeneralObjectExporter(s)
    mfText = mf.parse().decode('utf-8')
    f = open(filePath + appendToPath + fileName, 'w')
    f.write(mfText.strip())
    f.close()
# end write_stream_to_xml