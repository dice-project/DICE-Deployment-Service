app.config(function ($routeProvider){
    $routeProvider
        .when('/', {
            templateUrl: STATIC_URL + '/partials/containers.html',
            controller: 'ContainersCtrl',
            data: {
                requireLogin: true
            }
        })
        .when('/containers', {
            templateUrl: STATIC_URL + '/partials/containers.html',
            controller: 'ContainersCtrl',
            data: {
                requireLogin: true
            }
        })
        .when('/login', {
            templateUrl: STATIC_URL + '/partials/login.html',
            controller: 'AuthCtrl',
            data: {
                requireLogin: false
            }
        })
        .otherwise({
            redirectTo: '/page-not-found',
            data: {
                requireLogin: false
            }
        });
});


/*
 * Login redirect
 */
app.run(function ($rootScope, $location) {
    $rootScope.$on("$routeChangeStart", function (event, next, current) {
        var requireLogin = next.data && next.data.requireLogin;
        $rootScope.loadUser();

        if (requireLogin && !$rootScope.user){
            console.log('Redirecting to login page');
            $location.path("/login");
        }
    });
});


/*
 * Add Authorization header to every request.
 */
app.factory('restApiInterceptor', function ($rootScope) {
    return {
        request: function (conf) {
            if(conf.url.indexOf('/auth/get-token') == 0)
                return conf;

            if($rootScope.user){
                conf.headers.Authorization = 'Token ' + $rootScope.user.token;
            }

            return conf;
        }
    };
});
app.config(['$httpProvider', function ($httpProvider) {
    $httpProvider.interceptors.push('restApiInterceptor');
}]);

