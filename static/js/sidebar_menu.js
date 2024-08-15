const info = JSON.parse($('#info').text());
const menu = info['menu'];  // notice, dashboard, official, score, schedule
const view_type = info['view_type'];  // problem, like, rate, solve, search
const parent_menu = ['score']  // menu with child branches

$(window).on("scroll", function() {
    const distance = $(this).scrollTop();
    const $herotext = $(".herotext-anim");
    if ($herotext.length) {
        const opacity = 1 - distance / ($(window).height() * 0.15);
        $herotext.css({
            transform: `translateY(${distance * 0.7}px)`,
            opacity: opacity
        });
    }
});


// Toggle the side navigation
$("#sidebarToggle").click(function() {
    $("body").toggleClass("toggle-sidebar");
});

function hideSidebar() {
    if ($(window).width() < 1200) {
        $('body').removeClass('toggle-sidebar');
    }
}

// Expand & activate menu
function expandMenu(target) {
    const navContent = $(target).closest('ul');
    const navLink = navContent.prev('a');
    const bulletPoint = $(target).children().first();

    navLink.removeClass('collapsed').attr('aria-expanded', 'true');
    navContent.addClass('show');
    $(target).addClass('active');
    bulletPoint.removeClass('fa-regular').addClass('fa-solid');
}

// Initialize the side menu bar
function initialMenu() {
    $('.nav-link').addClass('collapsed').attr('aria-expanded', 'false');
    $('.aside-nav-icon').removeClass('active').find('i').removeClass('fa-solid').addClass('fa-regular');
}

// When the main menu activated
$(document).ready(function() {
    if (parent_menu.includes(menu)) {
        expandMenu(`#${view_type}List`);
    }
    else {
        $(`#${menu}List`).removeClass('collapsed');
    }
});

// When clicked the logo
$('.logo').click(function() {
    let target = $(this).data('target');
    initialMenu();
    $(target).removeClass('collapsed').attr('aria-expanded', 'true');
    hideSidebar();
});

// When clicked the main menu
$('#noticeList, #dashboardList, #officialList, #predictList, #scheduleList, #lectureList').click(
    function() {
        initialMenu();
        $(this).removeClass('collapsed').attr('aria-expanded', 'true');
        hideSidebar()
});

// When clicked the sub-menu
jQuery('.aside-nav-icon').click(function() {
    initialMenu();

    $(this).closest('ul').prev('a').removeClass('collapsed').attr('aria-expanded', 'true');
    $(this).closest('li').children().removeClass('active');
    $(this).closest('li').children().find('i').removeClass('fa-solid').addClass('fa-regular');

    $(this).addClass('active').find('i').removeClass('fa-regular').addClass('fa-solid');
    hideSidebar();
});

function mainAnchorClick() {
    $('#main a, #aside-group a, #aside-group select').click(function (){
        hideSidebar();
    });
}

mainAnchorClick();
// jQuery('body').on('htmx:afterSwap', function() {
//     mainAnchorClick();
// });
