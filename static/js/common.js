// Initialize tooltips, Sortables, toggleButtons
(function initializeTooltips() {$('[data-bs-toggle="tooltip"]').tooltip();})();

(
    function initializeSortables() {
        $('.sortable').each(function() {
            new Sortable(this, {
                animation: 150,
                ghostClass: 'blue-background-class'
            });
        });
    }
)();

(
    function initializeToggleButtons() {
        $('#toggleProblemBtn, #toggleCommentBtn, #floatingCollectionIndicator').click(function () {
            $('#floatingCollection').removeClass('show-menu');
            $('#toggleCollectionBtn').show().animate({right: '20'}, 300);
        });
        $('#toggleCollectionBtn').click(function() {
            $('#floatingCollection').addClass('show-menu');
            $(this).hide();
        });
    }
)();


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


// Attach the content of ckeditor to the form
function attachContentCkeditor() {
    $('.ckeditor-submit').click( function() {
        let button = $(this);
        let ckeditorId = button.closest('form').find('div.django-ckeditor-widget').attr('data-field-id');
        let content = CKEDITOR.instances[ckeditorId].getData();
        button.closest('form').find('textarea.ckeditor-content').text(content);
    });
}

$(document).ready(function() {
    attachContentCkeditor();
});

$(document).on('htmx:afterSettle', function(event) {
    attachContentCkeditor();
});
