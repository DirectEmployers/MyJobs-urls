$(document).ready(function() {
    get_toolbar();
});

function get_toolbar() {
    $.ajax({
        url: "http://ec2-23-20-67-65.compute-1.amazonaws.com/topbar/",
        dataType: "jsonp",
        type: "GET",
        jsonpCallback: "populate_toolbar",
        crossDomain: true,
        processData: false,
        headers: {"Content-Type": "application/json", Accept: "text/javascript"}
    });
}

function populate_toolbar(data) {
    $('body').prepend(data);
}
