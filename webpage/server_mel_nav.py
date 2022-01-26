from flask import Flask, render_template, send_file, request, redirect, Response, jsonify
import json
import shutil
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
import MBL_feature_blending_functions as fbl
# email imports
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import _thread

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
evoSession = []
available = True
# my_email = []
# email_pwd = []

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

# make a global list with all output files in any folder
all_files_single = []
for i in range(4):
    all_files_single.append('one_jazz_into_han_'+str(i)+'.mid')
    all_files_single.append('one_jazz_into_han_'+str(i)+'.xml')
    all_files_single.append('one_han_into_jazz_'+str(i)+'.mid')
    all_files_single.append('one_han_into_jazz_'+str(i)+'.xml')
all_files_single.append('han_input.mid')
all_files_single.append('jazz_input.mid')
all_files_single.append('Output.txt')
def append_single_path_to_files(fold):
    print('fold: ', fold)
    global all_files_single
    files_out = []
    for f in all_files_single:
        print('f: ', f)
        files_out.append( fold+f )
    return files_out
# end append_single_path_to_files

# do the same for the full list of blends
all_files_full = []
for i in range(14):
    all_files_full.append('blend_'+str(i)+'.mid')
    all_files_full.append('blend_'+str(i)+'.xml')
    all_files_full.append('blend_'+str(i)+'.mid')
    all_files_full.append('blend_'+str(i)+'.xml')
all_files_full.append('han_input.mid')
all_files_full.append('jazz_input.mid')
all_files_full.append('Output.txt')
def append_full_path_to_files(fold):
    print('fold: ', fold)
    global all_files_full
    files_out = []
    for f in all_files_full:
        print('f: ', f)
        files_out.append( fold+f )
    return files_out
# end append_single_path_to_files

def send_email(send_to, subject, text, files=None):
    assert isinstance(send_to, list)

    global my_email
    global email_pwd

    msg = MIMEMultipart()
    msg['From'] = my_email
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)


    # smtp = smtplib.SMTP(server)
    smtp = smtplib.SMTP("mail.auth.gr",587)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo
    smtp.login(my_email, email_pwd)
    smtp.sendmail(my_email, send_to, msg.as_string())
    smtp.close()

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
    os.makedirs(APP_ROOT+'/static/results/'+session_folder, exist_ok=True)
    output_1 = APP_ROOT+'/static/results/'+session_folder+'/'
    os.makedirs(APP_ROOT+'/templates/static/results/'+session_folder, exist_ok=True)
    output_2 = APP_ROOT+'/templates/static/results/'+session_folder+'/'
    # evo constants
    nGens = 30
    nPop = 30

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

def thread_all_single_blends(email, han, jazz, session):
    global cwd
    email_address = email
    han_file = han
    jazz_file = jazz
    jazz_name = jazz_file.split("/")[-1].split(".")[0]
    han_name = han_file.split("/")[-1].split(".")[0]
    # target_features = dat_json['target'] # we'll make all single-scope combinations
    session_folder = session
    # request_code = datetime.datetime.now().strftime("%I_%M_%S%p_%b_%d_%Y")
    # session_folder = 'single_'+jazz_name+'_'+han_name+'_'+request_code
    print('APP_ROOT: ', APP_ROOT)
    os.makedirs(APP_ROOT+'/static/results/'+session_folder, exist_ok=True)
    output_1 = APP_ROOT+'/static/results/'+session_folder+'/'
    os.makedirs(APP_ROOT+'/templates/static/results/'+session_folder, exist_ok=True)
    output_2 = APP_ROOT+'/templates/static/results/'+session_folder+'/'
    # evo constants
    nGens = 30
    nPop = 30

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
    zip_base_1 = 'static/results/'
    zip_base_2 = 'templates/static/results/'

    # first write inputs to midi
    fef.write_stream_to_midi(js, appendToPath=base_name_1, fileName=jazz_name+'.mid')
    fef.write_stream_to_midi(hs, appendToPath=base_name_1, fileName=han_name+'.mid')
    fef.write_stream_to_midi(js, appendToPath=base_name_2, fileName=jazz_name+'.mid')
    fef.write_stream_to_midi(hs, appendToPath=base_name_2, fileName=han_name+'.mid')
    # also write them as han_input and jazz_input for including them in the email
    fef.write_stream_to_midi(js, appendToPath=base_name_1, fileName='jazz_input.mid')
    fef.write_stream_to_midi(hs, appendToPath=base_name_1, fileName='han_input.mid')
    fef.write_stream_to_midi(js, appendToPath=base_name_2, fileName='jazz_input.mid')
    fef.write_stream_to_midi(hs, appendToPath=base_name_2, fileName='han_input.mid')
    # make markov target - which remains the same during all simulations
    target_markov = ( jm + hm )/2.0
    # open the log file
    log_file_1 = open(APP_ROOT+'/'+base_name_1 + "Output.txt", "w")
    log_file_2 = open(APP_ROOT+'/'+base_name_2 + "Output.txt", "w")
    # write the  feature titles
    log_file_1.write('Feature names:' + str(mff.get_accepted_feature_labels()) + '\n')
    log_file_2.write('Feature names:' + str(mff.get_accepted_feature_labels()) + '\n')
    # and features of each input melody
    log_file_1.write('han features:' + str(hf) + '\n')
    log_file_2.write('han features:' + str(hf) + '\n')
    log_file_1.write('jazz features:' + str(jf) + '\n')
    log_file_2.write('jazz features:' + str(jf) + '\n')

    # all scenarios for deut into han
    for i in range(4):
        print('jazz into han: ', i)
        # folder_name_1 = base_name_1
        # folder_name_2 = base_name_2
        # check if folder exists, else make it
        if not os.path.exists(APP_ROOT+'/'+base_name_1):
            os.makedirs(APP_ROOT+'/'+base_name_1)
        if not os.path.exists(APP_ROOT+'/'+base_name_2):
            os.makedirs(APP_ROOT+'/'+base_name_2)
        # make target features
        target_features = fbl.blend_single_feature(hf, jf, i)
        evoSession = evo.EvoSession( han_file, jazz_file, target_features, target_markov, nPop=nPop, nGen=nGens, print_gens=True )
        bl_name_mid = 'one_han_into_jazz_'+str(i)+'.mid'
        bl_name_xml = 'one_han_into_jazz_'+str(i)+'.xml'
        # include name in stream
        evoSession.best_individual.stream.insert(0, m21.metadata.Metadata())
        evoSession.best_individual.stream.metadata.title = 's_bl_'+han_name+jazz_name+'_'
        evoSession.best_individual.stream.metadata.composer = 'Mel Blender'
        # write to midi files
        print('writing midi')
        fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=base_name_1, fileName=bl_name_mid)
        fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=base_name_2, fileName=bl_name_mid)
        # and xml for showing
        print('writing xml1')
        uof.generate_xml( evoSession.best_individual.stream, fileName=output_1+bl_name_xml, destination=output_1+bl_name_xml )
        print('writing xml2')
        uof.generate_xml( evoSession.best_individual.stream, fileName=output_2+bl_name_xml, destination=output_2+bl_name_xml )
        # # write to midi files
        # fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=folder_name, fileName='one_han_into_jazz_'+str(i)+'.mid')
        # write to log file
        log_file_1.write('one_han_into_jazz_'+str(i)+' ================== \n')
        log_file_1.write('target features: ' + str(evoSession.target_features) + '\n')
        log_file_1.write('best features: ' + str(evoSession.best_individual.features) + '\n')
        log_file_2.write('one_han_into_jazz_'+str(i)+' ================== \n')
        log_file_2.write('target features: ' + str(evoSession.target_features) + '\n')
        log_file_2.write('best features: ' + str(evoSession.best_individual.features) + '\n')
    # all scenarios for han into deut
    for i in range(4):
        print('han into jazz: ', i)
        # folder_name_1 = base_name_1
        # folder_name_2 = base_name_2
        # check if folder exists, else make it
        if not os.path.exists(APP_ROOT+'/'+base_name_1):
            os.makedirs(APP_ROOT+'/'+base_name_1)
        if not os.path.exists(APP_ROOT+'/'+base_name_2):
            os.makedirs(APP_ROOT+'/'+base_name_2)
        # make target features
        target_features = fbl.blend_single_feature(jf, hf, i)
        evoSession = evo.EvoSession( APP_ROOT+'/'+jazz_file, APP_ROOT+'/'+han_file, target_features, target_markov, nPop=nPop, nGen=nGens, print_gens=True )
        bl_name_mid = 'one_jazz_into_han_'+str(i)+'.mid'
        bl_name_xml = 'one_jazz_into_han_'+str(i)+'.xml'
        # include name in stream
        evoSession.best_individual.stream.insert(0, m21.metadata.Metadata())
        evoSession.best_individual.stream.metadata.title = 's_bl_'+jazz_name+'_'+han_name
        evoSession.best_individual.stream.metadata.composer = 'Mel Blender'
        # write to midi files
        print('writing midi')
        fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=base_name_1, fileName=bl_name_mid)
        fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=base_name_2, fileName=bl_name_mid)
        # and xml for showing
        print('writing xml1')
        uof.generate_xml( evoSession.best_individual.stream, fileName=output_1+bl_name_xml, destination=output_1+bl_name_xml )
        print('writing xml2')
        uof.generate_xml( evoSession.best_individual.stream, fileName=output_2+bl_name_xml, destination=output_2+bl_name_xml )
        # write to midi files
        # fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=folder_name, fileName='one_jazz_into_han_'+str(i)+'.mid')
        # write to log file
        log_file_1.write('one_jazz_into_han_'+str(i)+' ================== \n')
        log_file_1.write('target features: ' + str(evoSession.target_features) + '\n')
        log_file_1.write('best features: ' + str(evoSession.best_individual.features) + '\n')
        log_file_2.write('one_jazz_into_han_'+str(i)+' ================== \n')
        log_file_2.write('target features: ' + str(evoSession.target_features) + '\n')
        log_file_2.write('best features: ' + str(evoSession.best_individual.features) + '\n')
    # close log file
    log_file_1.close()
    log_file_2.close()
    # zipping folders
    # shutil.make_archive(zip_base_1+session_folder, 'zip', APP_ROOT+'/'+base_name_1)
    # shutil.make_archive(zip_base_2+session_folder, 'zip', APP_ROOT+'/'+base_name_2)
    # email attachement
    text = "Hello! Here are the blending results you've requested."
    files2email = append_single_path_to_files(base_name_1)
    # send_email([email_address], "Melody blending results: "+session_folder, text, files=[zip_base_1+session_folder+'.zip'])
    send_email([email_address], "Melody blending results: "+session_folder, text, files=files2email)
# end thread

def thread_all_blends(email, han, jazz, session):
    global cwd
    email_address = email
    han_file = han
    jazz_file = jazz
    jazz_name = jazz_file.split("/")[-1].split(".")[0]
    han_name = han_file.split("/")[-1].split(".")[0]
    # target_features = dat_json['target'] # we'll make all single-scope combinations
    session_folder = session
    # request_code = datetime.datetime.now().strftime("%I_%M_%S%p_%b_%d_%Y")
    # session_folder = 'single_'+jazz_name+'_'+han_name+'_'+request_code
    print('APP_ROOT: ', APP_ROOT)
    os.makedirs(APP_ROOT+'/static/results/'+session_folder, exist_ok=True)
    output_1 = APP_ROOT+'/static/results/'+session_folder+'/'
    os.makedirs(APP_ROOT+'/templates/static/results/'+session_folder, exist_ok=True)
    output_2 = APP_ROOT+'/templates/static/results/'+session_folder+'/'
    # evo constants
    nGens = 30
    nPop = 30

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
    zip_base_1 = 'static/results/'
    zip_base_2 = 'templates/static/results/'

    # first write inputs to midi
    fef.write_stream_to_midi(js, appendToPath=base_name_1, fileName=jazz_name+'.mid')
    fef.write_stream_to_midi(hs, appendToPath=base_name_1, fileName=han_name+'.mid')
    fef.write_stream_to_midi(js, appendToPath=base_name_2, fileName=jazz_name+'.mid')
    fef.write_stream_to_midi(hs, appendToPath=base_name_2, fileName=han_name+'.mid')
    # also write them as han_input and jazz_input for including them in the email
    fef.write_stream_to_midi(js, appendToPath=base_name_1, fileName='jazz_input.mid')
    fef.write_stream_to_midi(hs, appendToPath=base_name_1, fileName='han_input.mid')
    fef.write_stream_to_midi(js, appendToPath=base_name_2, fileName='jazz_input.mid')
    fef.write_stream_to_midi(hs, appendToPath=base_name_2, fileName='han_input.mid')
    # make markov target - which remains the same during all simulations
    target_markov = ( jm + hm )/2.0
    # open the log file
    log_file_1 = open(APP_ROOT+'/'+base_name_1 + "Output.txt", "w")
    log_file_2 = open(APP_ROOT+'/'+base_name_2 + "Output.txt", "w")
    # write the  feature titles
    log_file_1.write('Feature names:' + str(mff.get_accepted_feature_labels()) + '\n')
    log_file_2.write('Feature names:' + str(mff.get_accepted_feature_labels()) + '\n')
    # and features of each input melody
    log_file_1.write('han features:' + str(hf) + '\n')
    log_file_2.write('han features:' + str(hf) + '\n')
    log_file_1.write('jazz features:' + str(jf) + '\n')
    log_file_2.write('jazz features:' + str(jf) + '\n')
    
    # make all blending combinations
    combs = fbl.blend_all_combinations(hf, jf)

    # all scenarios for deut into han
    for i in range( len(combs) ):
        print('blend: ', i)
        # folder_name_1 = base_name_1
        # folder_name_2 = base_name_2
        # check if folder exists, else make it
        if not os.path.exists(APP_ROOT+'/'+base_name_1):
            os.makedirs(APP_ROOT+'/'+base_name_1)
        if not os.path.exists(APP_ROOT+'/'+base_name_2):
            os.makedirs(APP_ROOT+'/'+base_name_2)
        # make target features
        target_features = combs[i]
        evoSession = evo.EvoSession( han_file, jazz_file, target_features, target_markov, nPop=nPop, nGen=nGens, print_gens=True )
        bl_name_mid = 'blend_'+str(i)+'.mid'
        bl_name_xml = 'blend_'+str(i)+'.xml'
        # include name in stream
        evoSession.best_individual.stream.insert(0, m21.metadata.Metadata())
        evoSession.best_individual.stream.metadata.title = 'bl_'+han_name+jazz_name+'_'
        evoSession.best_individual.stream.metadata.composer = 'Mel Blender'
        # write to midi files
        print('writing midi')
        fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=base_name_1, fileName=bl_name_mid)
        fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=base_name_2, fileName=bl_name_mid)
        # and xml for showing
        print('writing xml1')
        uof.generate_xml( evoSession.best_individual.stream, fileName=output_1+bl_name_xml, destination=output_1+bl_name_xml )
        print('writing xml2')
        uof.generate_xml( evoSession.best_individual.stream, fileName=output_2+bl_name_xml, destination=output_2+bl_name_xml )
        # # write to midi files
        # fef.write_stream_to_midi(evoSession.best_individual.stream, appendToPath=folder_name, fileName='one_han_into_jazz_'+str(i)+'.mid')
        # write to log file
        log_file_1.write('blend_'+str(i)+' ================== \n')
        log_file_1.write('target features: ' + str(evoSession.target_features) + '\n')
        log_file_1.write('best features: ' + str(evoSession.best_individual.features) + '\n')
        log_file_2.write('blend_'+str(i)+' ================== \n')
        log_file_2.write('target features: ' + str(evoSession.target_features) + '\n')
        log_file_2.write('best features: ' + str(evoSession.best_individual.features) + '\n')
    # close log file
    log_file_1.close()
    log_file_2.close()
    # zipping folders
    # shutil.make_archive(zip_base_1+session_folder, 'zip', APP_ROOT+'/'+base_name_1)
    # shutil.make_archive(zip_base_2+session_folder, 'zip', APP_ROOT+'/'+base_name_2)
    # email attachement
    text = "Hello! Here are the blending results you've requested."
    files2email = append_full_path_to_files(base_name_1)
    # send_email([email_address], "Melody blending results: "+session_folder, text, files=[zip_base_1+session_folder+'.zip'])
    send_email([email_address], "Melody blending results: "+session_folder, text, files=files2email)
# end thread

@app.route('/all_single_blends', methods=['POST'])
def all_single_blends():
    # make unavailable
    available = False
    data = request.get_data()
    dat_json = json.loads(data.decode('utf-8'))
    print('dat_json: ', dat_json);
    email_address = dat_json['email']
    han_file = dat_json['name1']
    jazz_file = dat_json['name2']
    jazz_name = jazz_file.split("/")[-1].split(".")[0]
    han_name = han_file.split("/")[-1].split(".")[0]
    session_folder = 'single_'+jazz_name+'_'+han_name
    zip_base_1 = 'static/results/'
    zip_base_2 = 'templates/static/results/'
    base_name_1 = 'static/results/'+session_folder+'/'
    base_name_2 = 'templates/static/results/'+session_folder+'/'
    
    # check if file already exists and send it to client, else send it to email
    # if os.path.isfile( zip_base_1+session_folder+'.zip' ) or os.path.isfile( zip_base_2+session_folder+'.zip' ):
    print('base_name_1: ', base_name_1)
    print('os.path.isdir( base_name_1 ): ', os.path.isdir( base_name_1 ))
    print('base_name_2: ', base_name_2)
    print('os.path.isdir( base_name_2 ): ', os.path.isdir( base_name_2 ))
    if os.path.isdir( base_name_1 ) or os.path.isdir( base_name_2 ):
        # return response with file
        print('sending existing file')
        text = "Hello! Here are the blending results you've requested."
        files2email = append_single_path_to_files(base_name_1)
        # send_email([email_address], "Melody blending results: "+session_folder, text, files=[zip_base_1+session_folder+'.zip'])
        send_email([email_address], "Melody blending results: "+session_folder, text, files=files2email)
        # return send_file(filename_or_fp=zip_base_1+session_folder+'.zip', attachment_filename=session_folder+'.zip', as_attachment=True)
    else:
        try:
            _thread.start_new_thread( thread_all_single_blends, (email_address, han_file, jazz_file, session_folder, ) )
        except:
            print("Error: unable to start thread")
        print('sending response')
    tmp_json = {}
    tmp_json['status'] = 'done'
    tmp_json['bl_path'] = zip_base_1+session_folder
    # return to available
    available = True
    return jsonify(tmp_json)

@app.route('/all_blends', methods=['POST'])
def all_blends():
    # make unavailable
    available = False
    data = request.get_data()
    dat_json = json.loads(data.decode('utf-8'))
    print('dat_json: ', dat_json);
    email_address = dat_json['email']
    han_file = dat_json['name1']
    jazz_file = dat_json['name2']
    jazz_name = jazz_file.split("/")[-1].split(".")[0]
    han_name = han_file.split("/")[-1].split(".")[0]
    session_folder = 'all_'+jazz_name+'_'+han_name
    zip_base_1 = 'static/results/'
    zip_base_2 = 'templates/static/results/'
    base_name_1 = 'static/results/'+session_folder+'/'
    base_name_2 = 'templates/static/results/'+session_folder+'/'
    
    # check if file already exists and send it to client, else send it to email
    # if os.path.isfile( zip_base_1+session_folder+'.zip' ) or os.path.isfile( zip_base_2+session_folder+'.zip' ):
    print('base_name_1: ', base_name_1)
    print('os.path.isdir( base_name_1 ): ', os.path.isdir( base_name_1 ))
    print('base_name_2: ', base_name_2)
    print('os.path.isdir( base_name_2 ): ', os.path.isdir( base_name_2 ))
    if os.path.isdir( base_name_1 ) or os.path.isdir( base_name_2 ):
        # return response with file
        print('sending existing file')
        text = "Hello! Here are the blending results you've requested."
        files2email = append_full_path_to_files(base_name_1)
        # send_email([email_address], "Melody blending results: "+session_folder, text, files=[zip_base_1+session_folder+'.zip'])
        send_email([email_address], "Melody blending results: "+session_folder, text, files=files2email)
        # return send_file(filename_or_fp=zip_base_1+session_folder+'.zip', attachment_filename=session_folder+'.zip', as_attachment=True)
    else:
        try:
            _thread.start_new_thread( thread_all_blends, (email_address, han_file, jazz_file, session_folder, ) )
        except:
            print("Error: unable to start thread")
        print('sending response')
    tmp_json = {}
    tmp_json['status'] = 'done'
    tmp_json['bl_path'] = zip_base_1+session_folder
    # return to available
    available = True
    return jsonify(tmp_json)

if __name__ == '__main__':
    print('--- --- --- main')
    arguments = sys.argv[1:]
    if len(arguments) < 2:
        print('Need two arguments to run: email and password')
    else:
        # global my_email
        # global email_pwd
        my_email = arguments[0]
        email_pwd = arguments[1]
    app.run(host='0.0.0.0', port=8515, debug=True)