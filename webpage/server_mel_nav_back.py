from flask import Flask, render_template, request, redirect, Response, jsonify
import json
import numpy as np
import os
cwd = os.getcwd()
import sys
import datetime
# use folders of generation functions
# sys.path.insert(0, cwd + '/../saved_data')
sys.path.insert(0, cwd + '/..')
import pickle
import music21 as m21
import MBL_music_processing_functions as mpf
import MBL_melody_features_functions as mff
import MBL_evolution as evo
import MP_file_export_functions as fef
import CM_user_output_functions as uof

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
evoSession = []
available = True

with open('../saved_data/all_names.pickle', 'rb') as handle:
    all_names = pickle.load(handle)
with open('../saved_data/all_styles.pickle', 'rb') as handle:
    all_styles = pickle.load(handle)
with open('../saved_data/all_styles_idx.pickle', 'rb') as handle:
    all_styles_idx = pickle.load(handle)
with open('../saved_data/all_features.pickle', 'rb') as handle:
    all_features = pickle.load(handle)
with open('../saved_data/all_pca.pickle', 'rb') as handle:
    all_pca = pickle.load(handle)
with open('../saved_data/style_folders.pickle', 'rb') as handle:
    style_folders = pickle.load(handle)
# load sorted pcas and names
with open('../saved_data/s_pca_1.pickle', 'rb') as handle:
    s_pca_1 = pickle.load(handle)
with open('../saved_data/s_pca_2.pickle', 'rb') as handle:
    s_pca_2 = pickle.load(handle)
with open('../saved_data/s_features_1.pickle', 'rb') as handle:
    s_features_1 = pickle.load(handle)
with open('../saved_data/s_features_2.pickle', 'rb') as handle:
    s_features_2 = pickle.load(handle)
with open('../saved_data/s_names_1.pickle', 'rb') as handle:
    s_names_1 = pickle.load(handle)
with open('../saved_data/s_names_2.pickle', 'rb') as handle:
    s_names_2 = pickle.load(handle)

# server
app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_initial_data', methods=['POST','GET'])
def get_initial_data():
    # data = request.get_data()
    # dat_json = json.loads(data)
    tmp_json = {}
    tmp_json['s_pca_1'] = s_pca_1.tolist()
    tmp_json['s_pca_2'] = s_pca_2.tolist()
    tmp_json['s_features_1'] = s_features_1.tolist()
    tmp_json['s_features_2'] = s_features_2.tolist()
    tmp_json['s_names_1'] = s_names_1
    tmp_json['s_names_2'] = s_names_2
    return jsonify(tmp_json)

# need some kind of threading to work
# https://stackoverflow.com/questions/24251898/flask-app-update-progress-bar-while-function-runs
# @app.route('/get_evo_progress')
# def get_evo_progress():
#     print('getting progress: ', evoSession.currGen/evoSession.nGen)
#     return evoSession.currGen/evoSession.nGen

# @app.route('/get_availability')
# def get_availability():
#     print('getting availability')
#     return available

@app.route('/blend', methods=['POST'])
def blend():
    # make unavailable
    available = False
    data = request.get_data()
    dat_json = json.loads(data.decode('utf-8'))
    print('dat_json: ', dat_json);
    han_file = dat_json['name1']
    jazz_file = dat_json['name2']
    jazz_name = jazz_file.split("/")[-1].split(".")[0]
    han_name = han_file.split("/")[-1].split(".")[0]
    target_features = dat_json['target']
    request_code = datetime.datetime.now().strftime("%I_%M_%S%p_%b_%d_%Y")
    session_folder = jazz_name+'_'+han_name+'_'+request_code
    print('APP_ROOT: ', APP_ROOT)
    os.mkdir(APP_ROOT+'/static/results/'+session_folder)
    output_1 = APP_ROOT+'/static/results/'+session_folder+'/'
    os.mkdir(APP_ROOT+'/templates/static/results/'+session_folder)
    output_2 = APP_ROOT+'/templates/static/results/'+session_folder+'/'
    # evo constants
    nGens = 50
    nPop = 50

    # vvvvv WE ACTUALLY NEED ALL THESE FOR EXTRACTING INTITIAL FEATURES vvvvv
    # vvvvv TO FORM THE FINAL "BLENDED" TARGET FEATURES vvvvv
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
    base_name_1 = 'static/results/'+session_folder+'/'
    base_name_2 = 'templates/static/results/'+session_folder+'/'

    # first write inputs to midi
    fef.write_stream_to_midi(js, appendToPath=base_name_1, fileName=jazz_name+'.mid')
    fef.write_stream_to_midi(hs, appendToPath=base_name_1, fileName=han_name+'.mid')
    fef.write_stream_to_midi(js, appendToPath=base_name_2, fileName=jazz_name+'.mid')
    fef.write_stream_to_midi(hs, appendToPath=base_name_2, fileName=han_name+'.mid')

    # make markov target - which remains the same during all simulations
    target_markov = ( jm + hm )/2.0
    evoSession = evo.EvoSession( jazz_file, han_file, target_features, target_markov, nPop=nPop, nGen=nGens, print_gens=True )
    bl_name_mid = 'bl_'+jazz_name+han_name+'.mid'
    bl_name_xml = 'bl_'+jazz_name+han_name+'.xml'
    # include name in stream
    evoSession.best_individual.stream.insert(0, m21.metadata.Metadata())
    evoSession.best_individual.stream.metadata.title = 'bl_'+jazz_name+'_'+han_name
    evoSession.best_individual.stream.metadata.composer = 'Mel Blender'
    # write to midi files
    print('writing midi')
    fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=base_name_1, fileName=bl_name_mid)
    fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=base_name_2, fileName=bl_name_mid)
    # and xml for showing
    # fef.write_stream_to_xml(evoSession.best_individual.stream, appendToPath=base_name_2, fileName=bl_name_xml)
    # fef.write_stream_to_xml(evoSession.best_individual.stream, appendToPath=base_name_2, fileName=bl_name_xml)
    print('writing xml1')
    uof.generate_xml( evoSession.best_individual.stream, fileName=output_1+bl_name_xml, destination=output_1+bl_name_xml )
    print('writing xml2')
    uof.generate_xml( evoSession.best_individual.stream, fileName=output_2+bl_name_xml, destination=output_2+bl_name_xml )

    print('sending response')
    tmp_json = {}
    tmp_json['bl_features'] = evoSession.best_individual.features.tolist()
    tmp_json['bl_path'] = base_name_1
    tmp_json['bl_name_mid'] = bl_name_mid
    tmp_json['bl_name_xml'] = bl_name_xml
    # return to available
    available = True
    return jsonify(tmp_json)

if __name__ == '__main__':
    print('--- --- --- main')
    app.run(host='0.0.0.0', port=8515, debug=True)