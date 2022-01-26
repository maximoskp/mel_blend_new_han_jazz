import numpy as np
import os
cwd = os.getcwd()
import sys
sys.path.insert(0, cwd + '/..')
import pickle
import music21 as m21
import MBL_music_processing_functions as mpf
import MBL_melody_features_functions as mff
import MBL_evolution as evo
import MP_file_export_functions as fef
import CM_user_output_functions as uof
import MBL_feature_blending_functions as fbl

# input files
han_file = '../all_xmls/han/han0163.xml'
han_name = han_file.split("/")[-1].split(".")[0]
jazz_file = '../all_xmls/jazz/jersy_bounce.xml'
jazz_name = jazz_file.split("/")[-1].split(".")[0]

session_folder = 'no_NN_' + jazz_name+'_'+han_name

os.makedirs(cwd+'/'+session_folder, exist_ok=True)
output_1 = cwd+'/'+session_folder

nGens = 20
nPop = 20

# parse pieces
js = m21.converter.parse(jazz_file)
hs = m21.converter.parse(han_file)

# put a piano instrument to both parents - this also needs to happen in evolution
for i in hs.recurse():
    if 'Instrument' in i.classes:
        i.activeSite.replace(i, m21.instrument.Piano())
for i in js.recurse():
    if 'Instrument' in i.classes:
        i.activeSite.replace(i, m21.instrument.Piano())

# transpose
j_trans = mpf.neutral_transposition(js)
h_trans = mpf.neutral_transposition(hs)

# fix lowest octave
j_fix = mpf.fix_lowest_octave(j_trans)
h_fix = mpf.fix_lowest_octave(h_trans)

# compute features
jf = mff.get_features_of_stream(j_fix)
hf = mff.get_features_of_stream(h_fix)

# compute markov transitions
jm = mff.compute_melody_markov_transitions(j_fix)
hm = mff.compute_melody_markov_transitions(h_fix)

# make base folder based on names
base_name_1 = '/'+session_folder+'/'

# first write inputs to midi
fef.write_stream_to_midi(js, appendToPath=base_name_1, fileName=jazz_name+'.mid')
fef.write_stream_to_midi(hs, appendToPath=base_name_1, fileName=han_name+'.mid')

# make markov target - which remains the same during all simulations
target_markov = ( jm + hm )/2.0

# open the log file
log_file_1 = open(cwd+'/'+base_name_1 + "Output.txt", "w")
# write the feature titles
log_file_1.write('Feature names:' + str(mff.get_accepted_feature_labels()) + '\n')
# and features of each input melody
log_file_1.write('han features:' + str(hf) + '\n')
log_file_1.write('jazz features:' + str(jf) + '\n')

# all scenarios for deut into han
for i in range(4):
    print('jazz into han: ', i)
    # make target features
    target_features = fbl.blend_single_feature(hf, jf, i)
    evoSession = evo.EvoSession( jazz_file, han_file, target_features, target_markov, nPop=nPop, nGen=nGens, print_gens=True )
    bl_name_mid = 'one_han_into_jazz_'+str(i)+'.mid'
    bl_name_xml = 'one_han_into_jazz_'+str(i)+'.xml'
    # include name in stream
    evoSession.best_individual.stream.insert(0, m21.metadata.Metadata())
    evoSession.best_individual.stream.metadata.title = 's_bl_'+han_name+jazz_name+'_'
    evoSession.best_individual.stream.metadata.composer = 'Mel Blender'
    # write to midi files
    print('writing midi')
    fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=base_name_1, fileName=bl_name_mid)
    # and xml for showing
    print('writing xml1')
    uof.generate_xml( evoSession.best_individual.stream, fileName=output_1+os.sep+bl_name_xml, destination=output_1+bl_name_xml )
    # write to log file
    log_file_1.write('one_han_into_jazz_'+str(i)+' ================== \n')
    log_file_1.write('target features: ' + str(evoSession.target_features) + '\n')
    log_file_1.write('best features: ' + str(evoSession.best_individual.features) + '\n')

# all scenarios for han into deut
for i in range(4):
    print('han into jazz: ', i)
    # make target features
    target_features = fbl.blend_single_feature(jf, hf, i)
    evoSession = evo.EvoSession( jazz_file, han_file, target_features, target_markov, nPop=nPop, nGen=nGens, print_gens=True )
    bl_name_mid = 'one_jazz_into_han_'+str(i)+'.mid'
    bl_name_xml = 'one_jazz_into_han_'+str(i)+'.xml'
    # include name in stream
    evoSession.best_individual.stream.insert(0, m21.metadata.Metadata())
    evoSession.best_individual.stream.metadata.title = 's_bl_'+jazz_name+'_'+han_name
    evoSession.best_individual.stream.metadata.composer = 'Mel Blender'
    # write to midi files
    print('writing midi')
    fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=base_name_1, fileName=bl_name_mid)
    # and xml for showing
    print('writing xml1')
    uof.generate_xml( evoSession.best_individual.stream, fileName=output_1+os.sep+bl_name_xml, destination=output_1+bl_name_xml )
    # write to log file
    log_file_1.write('one_jazz_into_han_'+str(i)+' ================== \n')
    log_file_1.write('target features: ' + str(evoSession.target_features) + '\n')
    log_file_1.write('best features: ' + str(evoSession.best_individual.features) + '\n')

# close log file
log_file_1.close()