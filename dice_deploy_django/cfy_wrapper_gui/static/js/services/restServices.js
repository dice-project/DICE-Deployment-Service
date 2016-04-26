app.factory('RestServices', function ($resource, $rootScope) {
    return {
        auth: $resource(BASE_URL + '/auth/get-token', {}, {}),
        containers: $resource(BASE_URL + '/containers', {}, {}),
        container: $resource(BASE_URL + '/containers/:id', {'id': '@id'}, {}),
        containerBlueprint: $resource(BASE_URL + '/containers/:id/blueprint', {'id': '@id'}, {
            put: {method: 'PUT'}
        }),
        containerErrors: $resource(BASE_URL + '/containers/:id/errors', {'id': '@id'}, {}),
        blueprints: $resource(BASE_URL + '/blueprints', {}, {}),
        blueprint: $resource(BASE_URL + '/blueprints/:id', {'id': '@id'}, {}),
        output: $resource(BASE_URL + '/blueprints/:id/outputs', {'id': '@id'}, {})
    };
});
