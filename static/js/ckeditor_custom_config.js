CKEDITOR.stylesSet.add('custom_styles', [
    // Block-level styles
    { name: '선지', element: 'p', attributes: { 'class': 'answer-choice' } },
    { name: '보기', element: 'p', attributes: { 'class': 'selection-choice' } },
    { name: 'Custom Paragraph', element: 'p', attributes: { 'class': 'custom-paragraph' } },

    // Inline styles
    { name: 'Custom Span', element: 'span', attributes: { 'class': 'custom-span' } },
    { name: 'Custom Strong', element: 'strong', styles: { 'font-weight': 'bold', 'color': 'red' } },
]);

CKEDITOR.on('dialogDefinition', function(event) {
    let dialogName = event.data.name;
    let dialogDefinition = event.data.definition;

    if (dialogName === 'table') {
        let infoTab = dialogDefinition.getContents('info');
        let advancedTab = dialogDefinition.getContents('advanced');

        // Set default values for the info tab
        let borderField = infoTab.get('txtBorder');
        let cellSpaceField = infoTab.get('txtCellSpace');
        let cellPadField = infoTab.get('txtCellPad');
        let widthField = infoTab.get('txtWidth');
        var rowsField = infoTab.get('txtRows');
        var colsField = infoTab.get('txtCols');

        if (borderField) borderField['default'] = '1';
        if (cellSpaceField) cellSpaceField['default'] = '0';
        if (cellPadField) cellPadField['default'] = '10';
        if (widthField) widthField['default'] = '100%';
        if (rowsField) rowsField['default'] = '1';
        if (colsField) colsField['default'] = '1';

        // Default attributes for the advanced tab
        let idField = advancedTab.get('advId');
        let stylesField = advancedTab.get('advStyles');
        let classesField = advancedTab.get('advCSSClasses');
        let langDirField = advancedTab.get('advLangDir');

        if (idField) idField['default'] = 'myTableId';
        if (stylesField) stylesField['default'] = 'border: 1px solid black;';
        if (classesField) classesField['default'] = 'my-custom-class';
        if (langDirField) langDirField['default'] = 'ltr';
    }
});