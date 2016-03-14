app.factory('PopupServices', function(ModalService, $q) {
    return {
        popupConfirm: function(message){
            /* This function opens dialog with message specified and YES/NO buttons. Promise is resolved if user
             * says YES and rejected otherwise.
             */

            var deferred = $q.defer();
            ModalService.showModal({
                templateUrl: STATIC_URL + '/partials/popups/popupYesNo.html',
                controller: 'YesNoController',
                inputs: {
                    message: message
                }
            }).then(function(modal) {
                modal.element.modal();
                modal.close.then(function(isConfirmed) {
                    if(isConfirmed)
                        deferred.resolve();
                    else
                        deferred.reject();
                });
            });

            return deferred.promise;
        },
        popupNotify: function(message, title){
            /* This function opens dialog with message specified and OK button. Promise is resolved when popup is closed
             */

            var deferred = $q.defer();
            ModalService.showModal({
                templateUrl: STATIC_URL + '/partials/popups/popupNotify.html',
                controller: 'NotifyController',
                inputs: {
                    message: message,
                    title: title
                }
            }).then(function(modal) {
                modal.element.modal();
                modal.close.then(function(isConfirmed) {
                    if(isConfirmed)
                        deferred.resolve();
                    else
                        deferred.reject();
                });
            });

            return deferred.promise;
        },
        popupAddContrainer: function(message, title){
            /* This function opens dialog with message specified and OK button. Promise is resolved when popup is closed
             */

            var deferred = $q.defer();
            ModalService.showModal({
                templateUrl: STATIC_URL + '/partials/popups/popupAddContainer.html',
                controller: 'AddContainerController',
                inputs: {

                }
            }).then(function(modal) {
                modal.element.modal();
                modal.close.then(function(data) {
                    if(data)
                        deferred.resolve(data);
                    else
                        deferred.reject();
                });
            });

            return deferred.promise;
        }
    }
});



app.controller('YesNoController', function($scope, close, message, $sce) {
    $scope.message = $sce.trustAsHtml(message);
    $scope.close = function(result) {
        close(result, 500); // close, but give 500ms for bootstrap to animate
    };
});

app.controller('NotifyController', function($scope, close, message, title, $sce) {
    $scope.message = $sce.trustAsHtml(message);
    $scope.title = title;
    $scope.close = function(result) {
        close(result, 500); // close, but give 500ms for bootstrap to animate
    };
});

app.controller('AddContainerController', function($scope, close) {
    $scope.close = function(data) {
        close(data, 500); // close, but give 500ms for bootstrap to animate
    };
});
