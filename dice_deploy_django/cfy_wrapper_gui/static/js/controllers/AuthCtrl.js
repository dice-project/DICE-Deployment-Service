app.controller('AuthCtrl', function($scope, RestServices, $rootScope, $location, Notification) {
    $scope.authObj = {
        username: undefined,
        password: undefined
    };
    
    $scope.login = function(authObj){
        RestServices.auth.save(authObj, function(user){
            user.username = authObj.username;
            user.prettyName = user.username;
            $rootScope.saveUser(user);
            $location.path("/");
        }, function(err){
            for(var key in err.data){
                if(key == 'non_field_errors'){
                    Notification.error(err.data[key][0]);
                }else{
                    Notification.error(key + ': ' + err.data[key]);
                }
            }
        });
    };

});
