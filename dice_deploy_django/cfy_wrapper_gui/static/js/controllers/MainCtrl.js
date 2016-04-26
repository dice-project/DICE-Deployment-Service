app.controller('MainCtrl', function($scope, RestServices, $rootScope, $window, $location) {
	//console.log('MainCtrl loaded.');
    $scope.getUser = function(){
        return $rootScope.user;
    };
    $scope.logout = function(event){
        $rootScope.forgetUser();
        $location.path("/login");
    };

    //
    //Global functions
    //
    $rootScope.saveUser = function(user){
        $window.localStorage.setItem('user', JSON.stringify(user));
    };
    $rootScope.loadUser = function(){
        var userStr = $window.localStorage.getItem('user');
        if(userStr){
            $rootScope.user = JSON.parse(userStr);
            return $rootScope.user;
        }else{
            return undefined;
        }
    };
    $rootScope.forgetUser = function(){
        $rootScope.user = undefined;
        $window.localStorage.removeItem('user');
    };
});
