$(document).ready(function() {
    get_toolbar();
});

function get_toolbar() {
    $.ajax({
        url: "https://secure.my.jobs/topbar/",
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
