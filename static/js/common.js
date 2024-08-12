// htmx.logAll();

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

let csrfToken = JSON.parse(
    document.querySelector('body').getAttribute('hx-headers')
)['X-CSRFToken']

function applyTagify() {
    function tagifyAction(action, tagName, tagHeader) {
        let formData = new FormData();
        formData.append('tag', tagName);
        fetch(action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
                'View-Type': tagHeader,
            },
        }).catch(error => console.error('Error:', error));
    }

    const inputs = document.querySelectorAll('[data-tagify]');
    inputs.forEach(input => {
        if (input.dataset.tagifyApplied) {return}

        const problemId = input.getAttribute('data-problem-id');
        const action = `/official/problem/tag/${problemId}/`
        const tags = input.getAttribute('data-tags').split(',').map(tag => tag.trim());
        const tagify = new Tagify(input, {
            editTags: false,
            hooks: {
                beforeRemoveTag : tags => {
                    return new Promise((resolve, reject) => {
                        confirm(`'${tags[0].data.value}' 태그를 삭제할까요?`) ? resolve() : reject();
                    });
                }
            }
        });
        tagify.addTags(tags);

        tagify.on('add', function(e) {tagifyAction(action, e.detail.data.value, 'add')});
        tagify.on('remove', function(e) {tagifyAction(action, e.detail.data.value, 'remove')});
        input.dataset.tagifyApplied = 'true';
    });
}
$(window).on('load', applyTagify);
$(document).on('htmx:afterSettle', applyTagify);


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

function mainAnchorClick() {
    $('#main a, #aside-group a, #aside-group select').click(function (){
        hideSidebar();
    });
}

mainAnchorClick();
// jQuery('body').on('htmx:afterSwap', function() {
//     mainAnchorClick();
// });

// Attach the content of ckeditor to the form
function attachContentCkeditor() {
    $('.ckeditor-submit').click( function() {
        let button = $(this);
        let ckeditorId = button.closest('form').find('div.django-ckeditor-widget').attr('data-field-id');
        let content = CKEDITOR.instances[ckeditorId].getData();
        button.closest('form').find('textarea.ckeditor-content').text(content);
    });
}

function initializeSelect2() {
    $('.select2-filter-style').select2({
        language: 'ko',
    }).on('select2:select', function () {
        this.dispatchEvent(new Event('change', { bubbles: true}));
    });
}


$(document).ready(function() {
    attachContentCkeditor();
    initializeSelect2();
});

$(document).on('htmx:afterSettle', function(event) {
    attachContentCkeditor();
    initializeSelect2();
});
