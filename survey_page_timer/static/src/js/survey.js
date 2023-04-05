odoo.define('survey.survey.timer', function (require) {
'use strict';

// TODO get information about actual question of survey
setTimeout(function () {
    console.debug("Force next or finish survey")
    $('[value="next"]').click();
    $('[value="finish"]').click();
}, 30000);

});
