app.controller('AuthCtrl', function($scope, RestServices, $rootScope, $location) {
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
        });
    };

});
