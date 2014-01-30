$(document).ready(function() {
    get_toolbar();
})

function get_toolbar() {
    $.ajax({
        url: "https://secure.my.jobs/toolbar",
        dataType: "jsonp",
        type: "GET",
        jsonpCallback: "populate_toolbar",
        crossDomain: true,
        processData: false,
        headers: {"Content-Type": "application/json", Accept: "text/javascript"},
    });
}

function populate_toolbar(data) {
    user_fullname = data.user_fullname;
    user_gravatar = data.user_gravatar;
    employer = data.employer;

    if (employer) {
        $("#menu-primary-navigation").append('<li><a href="https://secure.my.jobs/candidates">Candidates</a></li>');
    }
    if (user_fullname != "" && user_gravatar != "") {
        nav_html = '<li>';
        nav_html += '<a href="" class="main-nav">' + user_gravatar + '<span class="arrow"></span></a>';
        nav_html += '<ul class="span4" id="pop-menu">';
        nav_html += '<li id="logged-in-li">Logged in as <b>' + user_fullname + '</b></li>';
        nav_html += '<li><a id="account-link" href="https://secure.my.jobs/account/edit/">Account Settings</a></li>';
        nav_html += '<li><a id="logout-link" href="https://secure.my.jobs/accounts/logout/">Log Out</a></li>';
        nav_html += '</ul>';
        nav_html += '</li>';

        $("#nav").html(nav_html);
        $("#nav").removeClass("menu-login");
        if ($('.main-nav img').length) {
            $("#nav").addClass("gravatar");
            $('.main-nav img').addClass('gravatar-info');
        }
     }
     $("#account").removeClass("hidden");
}
