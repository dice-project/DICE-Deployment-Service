app.config(['$routeProvider',
    function ($routeProvider) {
        $routeProvider
        .when('/', {
            templateUrl: STATIC_URL + '/partials/containers.html',
            controller: 'ContainersCtrl'
        })
        .when('/containers', {
            templateUrl: STATIC_URL + '/partials/containers.html',
            controller: 'ContainersCtrl'
        })
        .otherwise({
            redirectTo: '/page-not-found'
        });
    }]);