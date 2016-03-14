// -------------------------------------------------------------------------------------
var app = angular.module('cfyWrapper', [
    'ngRoute',
    'ngResource',
    'angularModalService',
    'angularFileUpload',
    'ui-notification',
    'ngSanitize'
]);
// -------------------------------------------------------------------------------------

// UTILITY FUNCTIONS
function strStartsWith(str, prefix) {
    return str.indexOf(prefix) === 0;
}
function strEndsWith(str, suffix) {
    return str.match(suffix+"$")==suffix;
}
function parseDateTime(apiDateTime){
    return moment.utc(apiDateTime, C_dtFormatAPI);
}

var LOG = function(intro, my_object) {console.log(intro, JSON.stringify(my_object, null, 2));};
var C_dtFormatAPI = 'YYYY-MM-DDTHH:mm:ss';
var C_dtFormatGUI = 'LLLL';  // locale