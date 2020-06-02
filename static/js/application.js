
$(document).ready(function(){
    //connect to the socket server.
    $(".knob").knob();
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/thermostat');

    //receive details from server
    socket.on('newnumber', function(msg) {
        console.log("Temp Set" + msg.number);
        //maintain a list of ten numbers
        var secHtml = $(".knob");
        secHtml.val(msg.number)
        secHtml.change()

    });

});