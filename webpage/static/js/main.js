console.log('main called 1');

var static_dat_1 = []
var static_dat_2 = []

var dat_1 = [];
var dat_2 = [];

var hc = []

function initialise_chart(pca_1, pca_2, names_1, names_2){
    dat_1 = merge_pca_names(pca_1, names_1);
    static_dat_1 = JSON.parse(JSON.stringify(dat_1));
    // console.log('dat_1: ', dat_1);
    dat_2 = merge_pca_names(pca_2, names_2);
    static_dat_2 = JSON.parse(JSON.stringify(dat_2));
    hc = Highcharts.chart('container', {
        chart: {
            type: 'scatter',
            zoomType: 'xy',
            width: 600,
            height: 600
        },
        title: {
            text: 'Han and Jazz melodies'
        },
        subtitle: {
            text: 'Plotted according to feature values'
        },
        xAxis: {
            title: {
                enabled: true,
                text: 'PCA axis 1'
            },
            startOnTick: true,
            endOnTick: true,
            showLastLabel: true
        },
        yAxis: {
            title: {
                text: 'PCA axis 2'
            }
        },
        legend: {
            layout: 'vertical',
            align: 'left',
            verticalAlign: 'top',
            x: 100,
            y: 70,
            floating: true,
            backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF',
            borderWidth: 1
        },
        plotOptions: {
            scatter: {
                marker: {
                    radius: 5,
                    states: {
                        hover: {
                            enabled: true,
                            lineColor: 'rgb(100,100,100)'
                        }
                    }
                },
                states: {
                    hover: {
                        marker: {
                            enabled: false
                        }
                    }
                },
                tooltip: {
                    headerFormat: '<b>{point.key}</b><br>',
                    pointFormat: '{point.x:.3f} , {point.y:.3f} '
                }
            }
        },
        series: [{
            turboThreshold: 0,
            events: {
                click: function (event) {
                    console.log('event: ', event.point.name);
                    idx2 = names2.indexOf(event.point.name);
                    update_f2();
                    var tmp_name = event.point.name.split(".")[0];
                    // var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("container_main");
                    osmd_jazz.load('static/all_xmls/jazz/'+tmp_name+'.xml').then( function() {
                        osmd_jazz.zoom = 0.4;
                        osmd_jazz.render();
                    });
                    piece_name_jazz = 'static/all_midis/jazz/'+tmp_name+'.mid';
                    MIDIjs.stop();
                    if(event.shiftKey){
                        MIDIjs.play('static/all_midis/jazz/'+tmp_name+'.mid'); 
                    }
                    // console.log(
                    //     this.data + ' clicked\n' +
                    //     'Alt: ' + event.altKey + '\n' +
                    //     'Control: ' + event.ctrlKey + '\n' +
                    //     'Meta: ' + event.metaKey + '\n' +
                    //     'Shift: ' + event.shiftKey
                    // );
                }
            },
            name: 'Jazz',
            color: 'rgba(223, 83, 83, .5)',
            data: dat_2
        }, {
            turboThreshold: 0,
            events: {
                click: function (event) {
                    console.log('event: ', event.point.name);
                    idx1 = names1.indexOf(event.point.name);
                    update_f1();
                    var tmp_name = event.point.name.split(".")[0];
                    // var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("container_main");
                    osmd_han.load('static/all_xmls/han/'+tmp_name+'.xml').then( function() {
                        osmd_han.zoom = 0.4;
                        osmd_han.render();
                    });
                    piece_name_han = 'static/all_midis/han/'+tmp_name+'.mid';
                    MIDIjs.stop();
                    if(event.shiftKey){
                        MIDIjs.play('static/all_midis/han/'+tmp_name+'.mid'); 
                    }
                }
            },
            name: 'Han',
            color: 'rgba(119, 152, 191, .5)',
            data: dat_1
        }]
    });
}

function update_data_with_percentage(p){
    var new_dat_1 = [];
    var new_dat_2 = [];
    var tmp_dat_1 = JSON.parse(JSON.stringify(static_dat_1));
    var tmp_dat_2 = JSON.parse(JSON.stringify(static_dat_2));
    // var tmp_step_1 = (tmp_dat_1.length+p*1)/(1+tmp_dat_1.length*p);
    var tmp_step_1 = tmp_dat_1.length + 1 - tmp_dat_1.length*Math.pow(p,0.02) + Math.random();
    var tmp_step_2 = tmp_dat_2.length + 1 - tmp_dat_2.length*Math.pow(p,0.02) + Math.random();
    // console.log('tmp_step_1: ', tmp_step_1);
    for (var i=0; i<Math.max(1,p*tmp_dat_1.length); i+=parseInt( Math.ceil(tmp_step_1) ) ){
        new_dat_1.push( tmp_dat_1[i] );
    }
    for (var i=0; i<Math.max(1,p*tmp_dat_2.length); i+=parseInt( Math.ceil(tmp_step_2) )){
        new_dat_2.push( tmp_dat_2[i] );
    }
    // console.log('new_dat_1.length: ', new_dat_1.length);
    hc.series[0].setData(new_dat_2);
    // console.log('hc.series[0].data.length: ', hc.series[0].data.length);
    hc.series[1].setData(new_dat_1);
}

function merge_pca_names(p, n){
    var d = [];
    for (var i=0; i<n.length; i++){
        d.push( {name: n[i], x: p[i][0], y:p[i][1]} );
    }
    return d;
}