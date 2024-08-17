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

$(document).on('htmx:afterSettle', function(e) {
    attachContentCkeditor();
});

$(document).on('htmx:beforeRequest', function(e) {
    attachContentCkeditor();
});
